# -*- coding: utf-8 -*-
"""
================================================================================
hot_reload.py
《GGBOM》统一强力热更新总入口 (Single Source of Truth)
强制实时读盘，免疫内存缓存，杜绝任何历史脚本回滚污染
================================================================================
"""
import sys
from pathlib import Path
import unreal

PROJECT_DIR = Path(unreal.Paths.project_dir()).resolve()
SCRIPTS_DIR = PROJECT_DIR / "Content" / "Python"

# 强制清理模块缓存
for mod_name in ["master_combat_system", "fix_projectile_collision_filter", "execute_and_verify_physics_combat"]:
    if mod_name in sys.modules:
        del sys.modules[mod_name]

def exec_disk_script(script_name):
    script_file = SCRIPTS_DIR / script_name
    if not script_file.exists():
        raise FileNotFoundError(f"未找到脚本: {script_file}")
    code_str = script_file.read_text(encoding="utf-8")
    scope = {
        "__name__": "__main__",
        "__file__": str(script_file)
    }
    exec(compile(code_str, str(script_file), "exec"), scope)

def hot_reload_all():
    print("[HOT_RELOAD] ==================================================", flush=True)
    print("[HOT_RELOAD] 🚀 启动 GGBOM 统一主控热更新 (Single Source of Truth)...", flush=True)
    
    # 1. 摄像机与地图正交基线恢复
    print("[HOT_RELOAD] 📷 [1/2] 执行摄像机与正交视口基线对齐...", flush=True)
    exec_disk_script("restore_camera_and_stage_ground_truth.py")
    
    # 2. 全局主控战斗系统流水线 (动能手枪子弹 + 拆除旧火球 + 炼狱火环 + 1200 穿透 + 图表清洗)
    print("[HOT_RELOAD] 🔫 [2/2] 执行主控战斗系统全量闭环 (master_combat_system.py)...", flush=True)
    exec_disk_script("master_combat_system.py")
    
    print("[HOT_RELOAD] 🎉 全局战斗系统热更新 100% 成功执行！", flush=True)
    print("[HOT_RELOAD] ==================================================", flush=True)

if __name__ == "__main__":
    hot_reload_all()
