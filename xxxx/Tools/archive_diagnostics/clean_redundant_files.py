#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工程冗余代码与临时文件清理/归档工具
1. 清理临时废弃脚本与根目录 dump 文本
2. 将 Tools 目录下的历史测试探针归档至 Tools/archive_diagnostics/
3. 保持核心生产工具与资产整洁规范
"""
import os
import shutil
from pathlib import Path

ROOT = Path("/Users/cc/Desktop/GGBOM")
XXXX = ROOT / "xxxx"
TOOLS = XXXX / "Tools"
ARCHIVE_DIR = TOOLS / "archive_diagnostics"

# 1. 明确删除的纯临时废弃文本与废弃脚本
FILES_TO_DELETE = [
    # 根目录临时文本
    ROOT / "all_actors_dump.txt",
    ROOT / "bullet_assets.txt",
    ROOT / "camera_vectors.txt",
    ROOT / "diagnose_output.txt",
    
    # xxxx 根目录临时文本
    XXXX / "diagnose_output.txt",
    XXXX / "flipbook_audit.txt",
    XXXX / "ground_truth_coords.txt",
    XXXX / "projectile_audit.txt",
    XXXX / "world_coords.txt",
    
    # Content/Python 临时文本
    XXXX / "Content/Python/diagnose_output.txt",
    XXXX / "Content/Python/subobject_methods.txt",
    XXXX / "Content/Python/subobjects_result.txt",
    XXXX / "Content/Python/widget_api_output.txt",
    
    # 本次调试废弃脚本
    TOOLS / "probe_math_and_bp.py",
    TOOLS / "dump_player_medic_graph.py",
    TOOLS / "test_ping_pong.py",
]

# 2. 保留在 Tools 根目录的核心生产工具白名单
CORE_TOOLS_WHITELIST = {
    "run_ue_script.py",
    "p01_asset_pipeline.py",
    "rebuild_player_medic.py",
    "headless_official_update.py",
    "master_combat_system.py",
    "finalize_all_combat_ai.py",
    "setup_complete_bossbar_and_combat.py",
    "install_auditor_skill.py",
    "install_lite_runner.py",
    "launch_lightweight_game.sh",
    "unreal_mcp_bridge.py",
    "official_remote_execution.py",
    "ue_remote_executor.py",
    "run_python.sh",
    "view_latest_logs.sh",
    "UE58_Bullet_Direction_FullFix_Package",
    "archive_diagnostics"
}

def main():
    print("🧹 [1/3] 清理临时废弃文本与一次性脚本...")
    deleted_count = 0
    for f in FILES_TO_DELETE:
        if f.exists():
            try:
                if f.is_dir():
                    shutil.rmtree(f)
                else:
                    f.unlink()
                print(f"  🗑️ 已删除: {f.relative_to(ROOT)}")
                deleted_count += 1
            except Exception as e:
                print(f"  ⚠️ 删除失败 {f}: {e}")
    print(f"  -> 共删除 {deleted_count} 个废弃临时文件。\n")

    print("📦 [2/3] 归档历史测试探针与中间诊断脚本至 Tools/archive_diagnostics/...")
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    archived_count = 0

    if TOOLS.exists():
        for item in list(TOOLS.iterdir()):
            name = item.name
            if name in CORE_TOOLS_WHITELIST or name.startswith("."):
                continue
            
            # 将 test_*, probe_*, dump_*, trace_*, inspect_* 以及非核心脚本归档
            if any(name.startswith(pfx) for pfx in ["test_", "probe_", "dump_", "trace_", "inspect_", "verify_", "check_"]) or name.endswith(".txt") or name.endswith(".log"):
                dest = ARCHIVE_DIR / name
                try:
                    shutil.move(str(item), str(dest))
                    print(f"  📦 归档: Tools/{name} -> Tools/archive_diagnostics/{name}")
                    archived_count += 1
                except Exception as e:
                    print(f"  ⚠️ 归档失败 {name}: {e}")

    print(f"  -> 共归档 {archived_count} 个历史测试与探针文件。\n")

    print("📊 [3/3] 当前 Tools/ 目录核心资产概览:")
    for item in sorted(TOOLS.iterdir()):
        if item.name.startswith("."):
            continue
        tag = "[目录]" if item.is_dir() else "[工具]"
        print(f"  ⭐ {tag} {item.name}")

    print("\n✅ 清理与规范归档完成！")

if __name__ == "__main__":
    main()
