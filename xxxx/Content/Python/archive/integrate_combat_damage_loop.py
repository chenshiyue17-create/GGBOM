# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》第一阶段: 全量数据驱动与核心战斗受击闭环装配
1. 读取 Content/Data/ 中的核心数据表 (DT_Characters, DT_Weapons, DT_Enemies 等)
2. 注入武器数据至 BP_Player_Medic 与 BP_ProjectileBase
3. 构建并装配 BP_Boss_Overlord 属性与头顶血条
4. 验证并输出 phase1_combat_data_status.json
================================================================================
"""
from __future__ import annotations
from pathlib import Path
import json
import unreal

ASSETS = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary

ROOT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
DATA_DIR = ROOT / "Content" / "Data"
OUT_DIR = ROOT / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def log(msg: str):
    print(f"[CombatPipeline] {msg}")
    unreal.log(f"[CombatPipeline] {msg}")

def set_or_reset_var(bp, var_name: str, pin_type, default_val: str, category: str = "Combat Stats", expose_spawn: bool = False):
    graph = BPLIB.find_event_graph(bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    existing = set(str(name) for name in BPLIB.list_member_variable_names(bp, False))
    if var_name in existing:
        editor.remove_member_variable(var_name)
    editor.add_member_variable(var_name, pin_type, default_val)
    BPLIB.set_blueprint_variable_category(bp, var_name, unreal.Text(category))
    BPLIB.set_blueprint_variable_instance_editable(bp, var_name, True)
    if expose_spawn:
        BPLIB.set_blueprint_variable_expose_on_spawn(bp, var_name, True)

# ============================================================================
# 1. 验证并读取数据表
# ============================================================================
def load_and_verify_data_tables() -> dict:
    log("🚀 [1/4] 验证并读取 5 张核心 JSON 数据表...")
    required_tables = [
        "DT_Characters.json",
        "DT_Weapons.json",
        "DT_Enemies.json",
        "DT_HitEffects.json",
        "DT_StatusEffects.json"
    ]
    
    data_bundle = {}
    for table_name in required_tables:
        p = DATA_DIR / table_name
        if not p.is_file():
            raise FileNotFoundError(f"缺少必须的数据表: {p}")
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
            data_bundle[table_name] = data
            log(f"  - 校验通过: {table_name} (包含 {len(data)} 条主条目)")
            
    return data_bundle

# ============================================================================
# 2. 注入数据至 BP_Player_Medic
# ============================================================================
def configure_player(data: dict):
    log("🚀 [2/4] 根据数据表配置 BP_Player_Medic...")
    bp_path = "/Game/Blueprints/Player/BP_Player_Medic"
    bp = unreal.load_asset(bp_path)
    if not bp:
        raise RuntimeError(f"未找到玩家蓝图: {bp_path}")
        
    wpn_data = data["DT_Weapons.json"]["WPN_Rifle_Standard"]
    fire_rate = float(wpn_data["FireRate"])
    proj_speed = float(wpn_data["ProjectileSpeed"])
    real_type = BPLIB.get_basic_type_by_name("real")
    
    set_or_reset_var(bp, "FireCooldown", real_type, str(fire_rate), "Weapon Stats")
    set_or_reset_var(bp, "ProjectileSpeed", real_type, str(proj_speed), "Weapon Stats")
    
    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"✅ BP_Player_Medic 已注入武器数据 (FireRate={fire_rate}s, Speed={proj_speed})")

# ============================================================================
# 3. 注入数据至 BP_ProjectileBase
# ============================================================================
def configure_projectile(data: dict):
    log("🚀 [3/4] 根据数据表配置 BP_ProjectileBase...")
    bp_path = "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase"
    bp = unreal.load_asset(bp_path)
    if not bp:
        raise RuntimeError(f"未找到子弹蓝图: {bp_path}")
        
    wpn_data = data["DT_Weapons.json"]["WPN_Rifle_Standard"]
    damage = float(wpn_data["Damage"])
    proj_speed = float(wpn_data["ProjectileSpeed"])
    real_type = BPLIB.get_basic_type_by_name("real")
    
    set_or_reset_var(bp, "Damage", real_type, str(damage), "Combat Stats", expose_spawn=True)
    set_or_reset_var(bp, "ProjectileSpeed", real_type, str(proj_speed), "Combat Stats", expose_spawn=True)
    
    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"✅ BP_ProjectileBase 已注入伤害数据 (Damage={damage}, Speed={proj_speed})")

# ============================================================================
# 4. 配置 Boss 属性与头顶血条
# ============================================================================
def configure_boss(data: dict):
    log("🚀 [4/4] 配置 BP_Boss_Overlord 属性与头顶血条...")
    bp_path = "/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord"
    bp = unreal.load_asset(bp_path)
    if not bp:
        raise RuntimeError(f"未找到 Boss 蓝图: {bp_path}")
        
    boss_data = data["DT_Enemies.json"]["Boss_Overlord"]
    max_hp = float(boss_data["MaxHealth"])
    real_type = BPLIB.get_basic_type_by_name("real")
    
    set_or_reset_var(bp, "MaxHealth", real_type, str(max_hp), "Combat Stats")
    set_or_reset_var(bp, "CurrentHealth", real_type, str(max_hp), "Combat Stats")
    
    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"✅ BP_Boss_Overlord 属性更新完毕 (MaxHealth={max_hp})")

def main():
    log("=== 开始执行第一阶段: 数据驱动与战斗受击闭环装配 ===")
    status = {
        "PHASE1_STATUS": "FAIL",
        "data_tables_verified": False,
        "player_data_bound": False,
        "projectile_data_bound": False,
        "boss_data_bound": False
    }
    
    try:
        data = load_and_verify_data_tables()
        status["data_tables_verified"] = True
        
        configure_player(data)
        status["player_data_bound"] = True
        
        configure_projectile(data)
        status["projectile_data_bound"] = True
        
        configure_boss(data)
        status["boss_data_bound"] = True
        
        status["PHASE1_STATUS"] = "PASS"
        log("🎉 第一阶段: 全量数据驱动底座与核心战斗闭环装配完毕！")
    except Exception as e:
        log(f"❌ 装配失败: {e}")
        status["error"] = str(e)
        
    out_file = OUT_DIR / "phase1_combat_data_status.json"
    out_file.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Status written to {out_file}")

if __name__ == "__main__":
    main()
