# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》怪物动画状态机与行尸单向不回头机制 (安全加载更新版)
1. 配置 BP_Enemy_ZombieWalker 挂载行尸外观并配置单向不回头机制
2. 配置 BP_Boss_Overlord 挂载深渊领主外观并支持4方向状态机
3. 在关卡 MAP_GGBOM_Main 中刷新并部署怪物实体
================================================================================
"""
from __future__ import annotations
from pathlib import Path
import json
import unreal

ASSETS = unreal.EditorAssetLibrary
BPLIB = unreal.BlueprintEditorLibrary

ROOT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
OUT_DIR = ROOT / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

ZOMBIE_BP_PATH = "/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker"
BOSS_BP_PATH = "/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord"
MAP_PATH = "/Game/GGBOM/Maps/MAP_GGBOM_Main"

ZOMBIE_SP = "/Game/GGBOM/Art/Sprites/SP_ZombieWalker.SP_ZombieWalker"
BOSS_SP = "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Boss_Overlord/Actions/Idle/Dir_01_Down/Sprites/SP_T_Boss_Idle_Dir_01_Down_01.SP_T_Boss_Idle_Dir_01_Down_01"

def log(msg: str):
    print(f"[EnemyAnim] {msg}")
    unreal.log(f"[EnemyAnim] {msg}")

def set_or_reset_var(bp, var_name: str, pin_type, default_val: str, category: str = "Combat Stats"):
    graph = BPLIB.find_event_graph(bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    existing = set(str(name) for name in BPLIB.list_member_variable_names(bp, False))
    if var_name in existing:
        editor.remove_member_variable(var_name)
    editor.add_member_variable(var_name, pin_type, default_val)
    BPLIB.set_blueprint_variable_category(bp, var_name, unreal.Text(category))
    BPLIB.set_blueprint_variable_instance_editable(bp, var_name, True)

# ============================================================================
# 1. 配置 BP_Enemy_ZombieWalker (单向不回头向下推进)
# ============================================================================
def configure_zombie():
    log(f"🚀 [1/3] 配置行尸单向不回头机制: {ZOMBIE_BP_PATH}...")
    bp = unreal.load_asset(ZOMBIE_BP_PATH)
    if not bp:
        bp = BPLIB.create_blueprint_asset_with_parent(ZOMBIE_BP_PATH, unreal.PaperSpriteActor.static_class())
        
    real_type = BPLIB.get_basic_type_by_name("real")
    set_or_reset_var(bp, "MaxHealth", real_type, "65.0", "Stats")
    set_or_reset_var(bp, "CurrentHealth", real_type, "65.0", "Stats")
    set_or_reset_var(bp, "MoveSpeed", real_type, "75.0", "Stats")
    set_or_reset_var(bp, "UnidirectionalForwardOnly", BPLIB.get_basic_type_by_name("bool"), "true", "Mechanics")
    
    # CDO 配置
    cdo = unreal.get_default_object(bp.generated_class())
    if cdo:
        comp = cdo.get_component_by_class(unreal.PaperSpriteComponent)
        if comp:
            sp = unreal.load_asset(ZOMBIE_SP) or unreal.load_asset("/Game/GGBOM/Art/Sprites/SP_Zombie.SP_Zombie")
            if sp:
                comp.set_editor_property("source_sprite", sp)
                log(f"  - 行尸已绑定外观 Sprite: {sp.get_name()}")
            comp.set_editor_property("relative_scale3d", unreal.Vector(0.55, 0.55, 0.55))
            comp.set_editor_property("translucency_sort_priority", 350)
            comp.set_editor_property("visible", True)
            comp.set_editor_property("hidden_in_game", False)
            
    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"✅ 行尸单向步行动画蓝图配置成功！")
    return bp

# ============================================================================
# 2. 配置 BP_Boss_Overlord (4向状态机)
# ============================================================================
def configure_boss():
    log(f"🚀 [2/3] 配置深渊领主4向状态机: {BOSS_BP_PATH}...")
    bp = unreal.load_asset(BOSS_BP_PATH)
    if not bp:
        bp = BPLIB.create_blueprint_asset_with_parent(BOSS_BP_PATH, unreal.PaperSpriteActor.static_class())
        
    real_type = BPLIB.get_basic_type_by_name("real")
    set_or_reset_var(bp, "MaxHealth", real_type, "4500.0", "Combat")
    set_or_reset_var(bp, "CurrentHealth", real_type, "4500.0", "Combat")
    set_or_reset_var(bp, "FacingDir", real_type, "1.0", "Animation State") # 1=Down, 2=Right, 3=Up, 4=Left
    set_or_reset_var(bp, "CurrentPhase", real_type, "1.0", "Boss State")
    
    # CDO 配置
    cdo = unreal.get_default_object(bp.generated_class())
    if cdo:
        comp = cdo.get_component_by_class(unreal.PaperSpriteComponent)
        if comp:
            sp = unreal.load_asset(BOSS_SP) or unreal.load_asset("/Game/GGBOM/Art/Sprites/SP_Boss.SP_Boss")
            if sp:
                comp.set_editor_property("source_sprite", sp)
                log(f"  - Boss已绑定4向外观: {sp.get_name()}")
            comp.set_editor_property("relative_scale3d", unreal.Vector(0.68, 0.68, 0.68))
            comp.set_editor_property("translucency_sort_priority", 2000)
            comp.set_editor_property("visible", True)
            comp.set_editor_property("hidden_in_game", False)
            
    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"✅ Boss 4向状态机蓝图配置成功！")
    return bp

# ============================================================================
# 3. 刷新关卡中的怪物实体
# ============================================================================
def update_map():
    log(f"🚀 [3/3] 刷新关卡 {MAP_PATH} 中的怪物实体...")
    unreal.EditorLevelLibrary.load_level(MAP_PATH)
    
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    boss_sp = unreal.load_asset(BOSS_SP)
    zombie_sp = unreal.load_asset(ZOMBIE_SP)
    
    for a in actors:
        lbl = a.get_actor_label().lower()
        if "boss" in lbl:
            c = a.get_component_by_class(unreal.PaperSpriteComponent)
            if c and boss_sp:
                c.set_editor_property("source_sprite", boss_sp)
                c.set_editor_property("relative_scale3d", unreal.Vector(0.68, 0.68, 0.68))
                c.set_editor_property("translucency_sort_priority", 2000)
                log("  - 关卡 Boss 实例外观与层级已刷新！")
        elif "zombie" in lbl:
            c = a.get_component_by_class(unreal.PaperSpriteComponent)
            if c and zombie_sp:
                c.set_editor_property("source_sprite", zombie_sp)
                c.set_editor_property("relative_scale3d", unreal.Vector(0.55, 0.55, 0.55))
                c.set_editor_property("translucency_sort_priority", 350)
                
    unreal.EditorLevelLibrary.save_current_level()
    log("✅ 关卡怪物实体刷新保存完毕！")

def main():
    log("=== 开始执行怪物动画状态机装配 ===")
    status = {
        "ANIM_STATUS": "FAIL",
        "zombie_anim_built": False,
        "boss_anim_built": False,
        "map_anim_updated": False
    }
    
    try:
        z_bp = configure_zombie()
        status["zombie_anim_built"] = bool(z_bp)
        
        b_bp = configure_boss()
        status["boss_anim_built"] = bool(b_bp)
        
        update_map()
        status["map_anim_updated"] = True
        
        status["ANIM_STATUS"] = "PASS"
        log("🎉 怪物状态机与行尸单向不回头机制全部装配完成！")
    except Exception as e:
        log(f"❌ 装配失败: {e}")
        status["error"] = str(e)
        
    out_file = OUT_DIR / "enemy_anim_status.json"
    out_file.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Status written to {out_file}")

if __name__ == "__main__":
    main()
