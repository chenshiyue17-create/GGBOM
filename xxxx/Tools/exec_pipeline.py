#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import time
import json
import urllib.request
import urllib.error
import subprocess
from pathlib import Path

ROOT = Path("/Users/cc/Desktop/GGBOM/xxxx")
PROJECT = ROOT / "xxxx.uproject"
OUT_JSON = ROOT / "output/headless_update_result.json"

def try_live_editor_execution():
    """
    如果主编辑器正在运行，直接通过官方 Remote Control API (端口 30010)
    在运行中的编辑器主线程内执行热更新与资产落盘，视口当场实时生效！
    """
    url_info = "http://127.0.0.1:30010/remote/info"
    try:
        req = urllib.request.Request(url_info, method="GET")
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            if resp.status != 200:
                return False
    except Exception:
        return False

    print("⚡ 检测到主编辑器正在运行 (127.0.0.1:30010)，直接通过官方远程控制通道执行...", flush=True)
    
    url_call = "http://127.0.0.1:30010/remote/object/call"
    cmd_py = "py import headless_official_update; import importlib; importlib.reload(headless_official_update); headless_official_update.run_headless()"
    payload = {
        "objectPath": "/Script/Engine.Default__KismetSystemLibrary",
        "functionName": "ExecuteConsoleCommand",
        "parameters": {
            "Command": cmd_py
        },
        "generateTransaction": False
    }
    
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url_call, data=data, headers={"Content-Type": "application/json"}, method="PUT")
        with urllib.request.urlopen(req, timeout=15.0) as resp:
            res_text = resp.read().decode("utf-8")
            print(f"✅ 主编辑器响应: {res_text}", flush=True)
            
        # 等待产物写盘
        time.sleep(2.0)
        if OUT_JSON.exists():
            with open(OUT_JSON, "r", encoding="utf-8") as f:
                res = json.load(f)
            print(f"🎉 资产与关卡碰撞体积全量同步写盘成功！", flush=True)
            print(f"   - 关卡地图保存状态: {res.get('level_map', {}).get('saved')}", flush=True)
            print(f"   - 同步怪物实例数: {res.get('level_map', {}).get('updated_instances')}", flush=True)
            print(f"   - 补齐怪物实例数: {res.get('level_map', {}).get('added_instances')}", flush=True)
            return True
    except Exception as e:
        print(f"⚠️ 实时通道调用异常，将回退至命令行模式: {e}", flush=True)
        return False

def run_headless_cmd():
    # 动态探测多卷名移动硬盘路径
    ENGINE_CMD = None
    for candidate in [
        "/Volumes/NINJAV 2/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd",
        "/Volumes/NINJAV 1/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd",
        "/Volumes/NINJAV/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd"
    ]:
        if Path(candidate).exists():
            ENGINE_CMD = Path(candidate)
            break

    if not ENGINE_CMD:
        print("❌ 错误: 未在任何已挂载卷上找到 UnrealEditor-Cmd，请检查移动硬盘连接！", flush=True)
        sys.exit(1)

    SCRIPT = ROOT / "Content/Python/headless_official_update.py"
    if len(sys.argv) > 1 and sys.argv[1]:
        SCRIPT = Path(sys.argv[1]) if Path(sys.argv[1]).is_absolute() else ROOT / sys.argv[1]

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    cmd = [
        str(ENGINE_CMD),
        str(PROJECT),
        "-run=pythonscript",
        f"-script={SCRIPT}",
        "-nullrhi",
        "-unattended",
        "-stdout"
    ]

    log_file = ROOT / "output/exec_pipeline.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"================================================================", flush=True)
    print(f"🚀 [流水线启动] 正在启动 UnrealEditor-Cmd 无头模式...", flush=True)
    print(f"📁 引擎路径: {ENGINE_CMD}", flush=True)
    print(f"📜 装配脚本: {SCRIPT.name}", flush=True)
    print(f"⏳ 正在加载 UE5 资产注册表与核心模块 (约需 30~50 秒)...", flush=True)
    print(f"================================================================", flush=True)

    start_time = time.time()
    proc = subprocess.Popen(
        cmd,
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env
    )

    with open(log_file, "w", encoding="utf-8") as f:
        for line in iter(proc.stdout.readline, ''):
            f.write(line)
            f.flush()
            line_str = line.strip()
            
            if any(kw in line_str for kw in ["[OFFICIAL_UPDATE]", "[INIT_UNREAL]", "Compiling Blueprint"]):
                elapsed = time.time() - start_time
                print(f"[{elapsed:5.1f}s] {line_str}", flush=True)
            elif "Critical error" in line_str or "Assertion failed" in line_str:
                print(f"❌ {line_str}", flush=True)

    proc.wait()
    total_time = time.time() - start_time
    print(f"================================================================", flush=True)
    print(f"🏁 [流水线结束] 运行完成，耗时: {total_time:.1f}s，退出码: {proc.returncode}", flush=True)
    print(f"📄 完整执行日志已保存至: {log_file}", flush=True)
    print(f"================================================================", flush=True)
    return proc.returncode == 0

def main():
    # 优先使用 live editor 通道
    if try_live_editor_execution():
        print("🎉 流水线执行成功 (主编辑器热更新模式)！")
        sys.exit(0)
        
    print("⏳ 切换至无头命令行独立执行模式...")
    ok = run_headless_cmd()
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
