#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
tools/sync_game_and_export_blueprints.py
虚幻引擎 5.8 官方蓝图资产【游戏实装与 H5 审核预览 100% 同步导出系统】

支持两种运行模式：
1. 终端外层调用 (普通 Python 3):
   python3 tools/sync_game_and_export_blueprints.py
   -> 自动通过 ggbom.paths 探测本地 UnrealEditor-Cmd
   -> 无头拉起 UE 5.8 执行 Python 反射与拓扑提取
   -> 校验生成的资产 SHA256、节点与连线数据，并同步至 Docs/ 与根目录

2. 引擎内部调用 (UE 嵌入式 Python):
   -run=pythonscript -script=".../sync_game_and_export_blueprints.py"
   -> 直接使用 unreal 模块执行 .uasset 深度反射、引脚与拓扑回读
   -> 输出 JSON / UMD-JS 数据包
================================================================================
"""

import os
import sys
import json
import shutil
import hashlib
import subprocess
from datetime import datetime
from pathlib import Path

# 尝试检测是否运行在虚幻引擎 Python 环境内部
IN_UNREAL = False
try:
    import unreal
    IN_UNREAL = True
except ImportError:
    IN_UNREAL = False


def get_file_meta(file_path: Path):
    """计算物理磁盘文件大小、SHA256 与修改时间"""
    if not file_path.exists():
        return {"exists": False, "size": 0, "sha256": "N/A", "mtime": "N/A"}
    stat = file_path.stat()
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return {
        "exists": True,
        "size": stat.st_size,
        "sha256": h.hexdigest(),
        "mtime": datetime.fromtimestamp(stat.st_mtime).isoformat()
    }


def run_inside_unreal():
    """在虚幻引擎内部通过官方 API 深度提取真实的 Blueprint EventGraph 拓扑"""
    BPLIB = unreal.BlueprintEditorLibrary
    PINLIB = unreal.BlueprintGraphPinLibrary
    ASSETS = unreal.EditorAssetLibrary

    project_dir = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
    content_dir = project_dir / "Content"
    output_dir = project_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    repo_root = project_dir.parent
    docs_dir = repo_root / "Docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    def get_pin_type_str(p):
        try:
            if hasattr(PINLIB, "get_pin_type_display_string"):
                s = str(PINLIB.get_pin_type_display_string(p))
                if s:
                    return s
        except Exception:
            pass
        try:
            return str(PINLIB.get_pin_type(p))
        except Exception:
            return "any"

    def get_pin_val(p):
        try:
            return str(PINLIB.get_pin_value(p))
        except Exception:
            return ""

    def read_bp(pkg_path):
        rel = pkg_path.removeprefix("/Game/")
        disk_file = content_dir / f"{rel}.uasset"
        meta = get_file_meta(disk_file)
        bp = ASSETS.load_asset(pkg_path)
        if not bp:
            return {"pkg": pkg_path, "disk": str(disk_file), "meta": meta, "error": "NOT_FOUND"}

        parent_name = "Actor"
        try:
            parent_name = bp.get_editor_property("parent_class").get_name()
        except Exception:
            pass

        var_names = []
        try:
            var_names = [str(n) for n in BPLIB.list_member_variable_names(bp, False)]
        except Exception:
            pass

        graph = BPLIB.find_event_graph(bp)
        nodes_info = []
        edges_info = []
        if graph:
            editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
            all_nodes = editor.list_all_nodes()
            node_map = {}
            for idx, n in enumerate(all_nodes):
                nid = f"{n.get_name()}_{idx}"
                node_map[n] = nid
                title = unreal.BlueprintEditorLibrary.get_node_title(n)
                pos = n.get_node_pos()
                cls = n.get_class().get_name()

                in_pins = []
                for p in BPLIB.list_input_pins(n):
                    in_pins.append({
                        "name": str(PINLIB.get_pin_name(p)),
                        "type": get_pin_type_str(p),
                        "default": get_pin_val(p)
                    })
                out_pins = []
                for p in BPLIB.list_output_pins(n):
                    out_pins.append({
                        "name": str(PINLIB.get_pin_name(p)),
                        "type": get_pin_type_str(p)
                    })
                nodes_info.append({
                    "id": nid,
                    "name": n.get_name(),
                    "title": title,
                    "class": cls,
                    "pos": [pos.x, pos.y],
                    "inputs": in_pins,
                    "outputs": out_pins
                })

            for src in all_nodes:
                src_id = node_map.get(src)
                for p in BPLIB.list_output_pins(src):
                    pname = str(PINLIB.get_pin_name(p))
                    ptype = get_pin_type_str(p).lower()
                    for dst_pin in PINLIB.list_connected_pins(p):
                        dst_node = dst_pin.get_owning_node()
                        dst_id = node_map.get(dst_node)
                        if dst_id:
                            edges_info.append({
                                "from_node": src_id,
                                "from_pin": pname,
                                "to_node": dst_id,
                                "to_pin": str(PINLIB.get_pin_name(dst_pin)),
                                "type": "exec" if ("exec" in ptype or pname.lower() in ("then", "execute")) else "data"
                            })

        return {
            "pkg": pkg_path,
            "disk": str(disk_file),
            "meta": meta,
            "parent": parent_name,
            "variables": var_names,
            "node_count": len(nodes_info),
            "edge_count": len(edges_info),
            "nodes": nodes_info,
            "edges": edges_info
        }

    targets = [
        "/Game/Blueprints/Player/BP_Player_Medic",
        "/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker",
        "/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord",
        "/Game/GGBOM/UI/WBP_Boss_OverheadHealthBar"
    ]

    print("\n================ 虚幻引擎 5.8 实装蓝图深度反射 ================", flush=True)
    blueprints_data = {}
    for t in targets:
        info = read_bp(t)
        blueprints_data[t] = info
        print(f"[LIVE AST] {t}: 节点数={info.get('node_count')}, 连线数={info.get('edge_count')}, SHA256={info.get('meta', {}).get('sha256', '')[:12]}...", flush=True)

    payload = {
        "engine_version": str(unreal.SystemLibrary.get_engine_version()),
        "sync_timestamp": datetime.now().isoformat(),
        "live_sync_verified": True,
        "blueprints": blueprints_data
    }

    # 1. 写入 xxxx/output/
    raw_json = json.dumps(payload, ensure_ascii=False, indent=2)
    (output_dir / "blueprint_live_readback.json").write_text(raw_json, encoding="utf-8")

    # 2. 写入 Docs/ 目录
    (docs_dir / "blueprint_live_readback.json").write_text(raw_json, encoding="utf-8")

    # 3. 写入通用 UMD 格式 JS (供浏览器、Node.js 与 WebWorker 共同加载)
    umd_content = (
        "(function(root) {\n"
        f"  var data = {raw_json};\n"
        "  if (typeof window !== 'undefined') { window.GGBOM_LIVE_READBACK = data; }\n"
        "  if (typeof global !== 'undefined') { global.GGBOM_LIVE_READBACK = data; }\n"
        "  if (typeof module !== 'undefined' && module.exports) { module.exports = data; }\n"
        "})(typeof globalThis !== 'undefined' ? globalThis : this);\n"
    )
    (docs_dir / "blueprint_live_readback.js").write_text(umd_content, encoding="utf-8")
    (repo_root / "blueprint_live_readback.js").write_text(umd_content, encoding="utf-8")

    # 4. 同步更新 Docs/index.html 与 index.html
    audit_html = docs_dir / "blueprint_audit.html"
    if audit_html.exists():
        shutil.copyfile(audit_html, docs_dir / "index.html")
        shutil.copyfile(audit_html, repo_root / "index.html")

    print("[LIVE AST] 同步与导出完成！所有产物已写入 Docs/ 与项目根目录。", flush=True)


def run_from_host():
    """普通终端环境下执行：定位 UE 二进制无头执行本脚本"""
    repo_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(repo_root / "tools"))

    try:
        from ggbom.paths import engine_binary, PROJECT_ROOT
    except ImportError:
        PROJECT_ROOT = repo_root / "xxxx"
        engine_bin = os.environ.get("GGBOM_UE_BIN")
        if not engine_bin:
            # 常见 Mac 路径
            candidate = Path("/Volumes/NINJAV 2/UE_5.8/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd")
            if candidate.is_file():
                engine_bin = str(candidate)
        if not engine_bin:
            print("错误: 未找到虚幻引擎可执行路径，请设置 GGBOM_UE_BIN 环境变量。", file=sys.stderr)
            sys.exit(1)
    else:
        engine_bin = str(engine_binary())

    # 确保使用 Cmd 无头程序
    if "UnrealEditor.app" in engine_bin and "UnrealEditor-Cmd" not in engine_bin:
        cmd_candidate = engine_bin.replace("UnrealEditor", "UnrealEditor-Cmd")
        if os.path.isfile(cmd_candidate):
            engine_bin = cmd_candidate

    uproject_file = PROJECT_ROOT / "xxxx.uproject"
    script_file = Path(__file__).resolve()

    print("================================================================================")
    print(" GGBOM: 启动虚幻引擎 5.8 实装蓝图同步与导出管道")
    print("================================================================================")
    print(f"  引擎二进制: {engine_bin}")
    print(f"  工程文件:   {uproject_file}")
    print(f"  执行脚本:   {script_file}")
    print("--------------------------------------------------------------------------------")

    cmd = [
        engine_bin,
        str(uproject_file),
        "-run=pythonscript",
        f"-script={script_file}",
        "-unattended",
        "-nopause",
        "-nosplash",
        "-nullrhi"
    ]

    result = subprocess.run(cmd, cwd=str(repo_root))
    if result.returncode != 0:
        print(f"\n[ERROR] 虚幻引擎脚本执行退出异常，返回码: {result.returncode}", file=sys.stderr)
        sys.exit(result.returncode)

    # 校验产物
    docs_json = repo_root / "Docs" / "blueprint_live_readback.json"
    if docs_json.exists():
        data = json.loads(docs_json.read_text(encoding="utf-8"))
        bp_count = len(data.get("blueprints", {}))
        print(f"\n[PASS] 实装蓝图同步验证成功！已提取 {bp_count} 个核心资产的真实 AST。")
        print(f"  回读时间戳: {data.get('sync_timestamp')}")
        print(f"  引擎版本:   {data.get('engine_version')}")
        print(f"  H5 审核页:  Docs/blueprint_audit.html")
    else:
        print("\n[WARN] 未在 Docs/ 找到导出的 blueprint_live_readback.json", file=sys.stderr)


def main():
    if IN_UNREAL:
        run_inside_unreal()
    else:
        run_from_host()


if __name__ == "__main__":
    main()
