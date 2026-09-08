#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能虚幻脚本执行器：
自动规避 MCP 8000 端口冲突，执行资产与关卡治理脚本
"""
import os
import sys
import subprocess
from pathlib import Path

ROOT = Path("/Users/cc/Desktop/GGBOM/xxxx")
PROJECT = ROOT / "xxxx.uproject"

if len(sys.argv) < 2:
    print("用法: python3 Tools/run_ue_script.py <script_relative_or_abs_path>")
    sys.exit(1)

script_path = Path(sys.argv[1])
if not script_path.is_absolute():
    script_path = ROOT / script_path

print(f"🚀 启动引擎执行脚本: {script_path.name}", flush=True)

def find_engine_cmd():
    import glob
    candidates = [
        "/Volumes/NINJAV 2/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd",
        "/Volumes/NINJAV 1/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd",
        "/Volumes/NINJAV/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd",
        "/Volumes/NINJAV 2/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor-Cmd",
        "/Volumes/NINJAV 1/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor-Cmd",
        "/Volumes/NINJAV/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor-Cmd",
    ]
    for c in candidates:
        if Path(c).exists():
            return Path(c)
    # 动态扫描所有挂载卷
    for pat in [
        "/Volumes/*/UE_5.*/UE_5.*/Engine/Binaries/Mac/UnrealEditor-Cmd",
        "/Volumes/*/UE_5.*/Engine/Binaries/Mac/UnrealEditor-Cmd",
        "/Volumes/*/UE_5.*/UE_5.*/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor-Cmd",
        "/Volumes/*/UE_5.*/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor-Cmd",
        "/Users/Shared/Epic Games/UE_5.*/Engine/Binaries/Mac/UnrealEditor-Cmd",
        "/Users/Shared/Epic Games/UE_5.*/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor-Cmd"
    ]:
        matches = glob.glob(pat)
        if matches:
            return Path(matches[0])
    return None

ENGINE_CMD = find_engine_cmd()
if not ENGINE_CMD:
    print("❌ 错误: 未在任何已挂载卷上找到 UnrealEditor-Cmd！请确保外部移动硬盘已正确插入连接电脑。", flush=True)
    sys.exit(1)

env = os.environ.copy()
env["PYTHONUNBUFFERED"] = "1"

cmd = [
    str(ENGINE_CMD),
    str(PROJECT),
    "-run=pythonscript",
    f"-script={script_path}",
    "-ini:Engine:[/Script/ModelContextProtocolEngine.ModelContextProtocolSettings]:bAutoStartServer=False",
    "-ini:Engine:[/Script/ModelContextProtocolEngine.ModelContextProtocolSettings]:ServerPortNumber=8002",
    "-nullrhi",
    "-unattended",
    "-NoSplash",
    "-stdout"
]

process = subprocess.Popen(
    cmd,
    stdin=subprocess.DEVNULL,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    universal_newlines=True,
    bufsize=1,
    env=env
)

for line in iter(process.stdout.readline, ""):
    line_clean = line.strip()
    if any(k in line_clean for k in ["[FIX_", "SUCCESS", "SAVED", "DESTROY", "SCALE", "ERROR", "Error", "Warning", "Traceback", "Exception", "LogBlueprint"]):
        print(line_clean, flush=True)

process.stdout.close()
return_code = process.wait()
print(f"✅ 执行完成，返回码: {return_code}", flush=True)
sys.exit(return_code)
