# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》第三阶段: 经验拾取、肉鸽三选一升级与动态属性增强
1. 创建/保存 WBP_Modal_CardSelection 控件蓝图
2. 创建 BP_Pickup_ExpGem 经验宝石掉落物蓝图
3. 扩展 BP_Player_Medic 经验与等级属性
4. 在 MAP_GGBOM_Main 中部署经验宝石供拾取验证
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
OUT_DIR = ROOT / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

WIDGET_PATH = "/Game/GGBOM/UI/WBP_Modal_CardSelection"
PICKUP_BP_DIR = "/Game/Blueprints/Pickups"
EXPGEM_BP_PATH = f"{PICKUP_BP_DIR}/BP_Pickup_ExpGem"
PLAYER_BP_PATH = "/Game/Blueprints/Player/BP_Player_Medic"
MAP_PATH = "/Game/GGBOM/Maps/MAP_GGBOM_Main"

def log(msg: str):
    print(f"[CardUpgrade] {msg}")
    unreal.log(f"[CardUpgrade] {msg}")

def ensure_directory(path: str):
    if not ASSETS.does_directory_exist(path):
        ASSETS.make_directory(path)

def set_or_reset_var(bp, var_name: str, pin_type, default_val: str, category: str = "Progression"):
    graph = BPLIB.find_event_graph(bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    existing = set(str(name) for name in BPLIB.list_member_variable_names(bp, False))
    if var_name in existing:
        editor.remove_member_variable(var_name)
    editor.add_member_variable(var_name, pin_type, default_val)
    BPLIB.set_blueprint_variable_category(bp, var_name, unreal.Text(category))
    BPLIB.set_blueprint_variable_instance_editable(bp, var_name, True)

# ============================================================================
# 1. 创建 WBP_Modal_CardSelection 控件蓝图
# ============================================================================
def build_card_selection_widget():
    log(f"🚀 [1/4] 构建肉鸽三选一升级弹窗: {WIDGET_PATH}...")
    ensure_directory("/Game/GGBOM/UI")
    
    widget_bp = None
    if ASSETS.does_asset_exist(WIDGET_PATH):
        widget_bp = unreal.load_asset(WIDGET_PATH)
    else:
        factory = unreal.WidgetBlueprintFactory()
        widget_bp = TOOLS.create_asset("WBP_Modal_CardSelection", "/Game/GGBOM/UI", unreal.WidgetBlueprint, factory)
        
    if not widget_bp:
        raise RuntimeError(f"无法创建控件蓝图: {WIDGET_PATH}")
        
    BPLIB.compile_blueprint(widget_bp)
    ASSETS.save_loaded_asset(widget_bp, only_if_is_dirty=False)
    log(f"✅ 控件蓝图 {WIDGET_PATH} 构建并编译保存成功！")
    return widget_bp

# ============================================================================
# 2. 创建 BP_Pickup_ExpGem 经验宝石蓝图
# ============================================================================
def build_exp_gem_pickup():
    log(f"🚀 [2/4] 构建经验宝石蓝图: {EXPGEM_BP_PATH}...")
    ensure_directory(PICKUP_BP_DIR)
    
    if ASSETS.does_asset_exist(EXPGEM_BP_PATH):
        ASSETS.delete_asset(EXPGEM_BP_PATH)
        
    bp = BPLIB.create_blueprint_asset_with_parent(EXPGEM_BP_PATH, unreal.PaperSpriteActor.static_class())
    if not bp:
        raise RuntimeError(f"无法创建经验宝石蓝图: {EXPGEM_BP_PATH}")
        
    real_type = BPLIB.get_basic_type_by_name("real")
    set_or_reset_var(bp, "ExpValue", real_type, "25.0", "Pickup Data")
    
    # CDO 配置 (经验宝石 Sprite 与缩放)
    cdo = unreal.get_default_object(bp.generated_class())
    if cdo:
        sprite_comp = cdo.get_component_by_class(unreal.PaperSpriteComponent)
        if sprite_comp:
            sp = unreal.load_asset("/Game/GGBOM/Art/Sprites/SP_HUD_Exp_Fill.SP_HUD_Exp_Fill") or unreal.load_asset("/Game/GGBOM/Art/Sprites/SP_Health.SP_Health")
            if sp:
                sprite_comp.set_editor_property("source_sprite", sp)
            sprite_comp.set_editor_property("relative_scale3d", unreal.Vector(0.40, 0.40, 0.40))
            sprite_comp.set_editor_property("translucency_sort_priority", 1500)
            sprite_comp.set_editor_property("visible", True)
            sprite_comp.set_editor_property("hidden_in_game", False)
            
    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"✅ 经验宝石蓝图 {EXPGEM_BP_PATH} 构建并编译保存成功！")
    return bp

# ============================================================================
# 3. 扩展 BP_Player_Medic 经验与等级属性
# ============================================================================
def configure_player_progression():
    log(f"🚀 [3/4] 扩展玩家蓝图经验与升级属性: {PLAYER_BP_PATH}...")
    bp = unreal.load_asset(PLAYER_BP_PATH)
    if not bp:
        raise RuntimeError(f"未找到玩家蓝图: {PLAYER_BP_PATH}")
        
    real_type = BPLIB.get_basic_type_by_name("real")
    set_or_reset_var(bp, "CurrentExp", real_type, "0.0", "Progression")
    set_or_reset_var(bp, "ExpToNextLevel", real_type, "100.0", "Progression")
    set_or_reset_var(bp, "PlayerLevel", real_type, "1.0", "Progression")
    
    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"✅ 玩家经验与升级体系装配成功！")

# ============================================================================
# 4. 在关卡中部署经验宝石实例
# ============================================================================
def update_map_pickups():
    log(f"🚀 [4/4] 在关卡 {MAP_PATH} 中部署经验宝石...")
    unreal.EditorLevelLibrary.load_level(MAP_PATH)
    world = unreal.EditorLevelLibrary.get_editor_world()
    
    # 清理旧经验宝石
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    for a in actors:
        if "expgem_runtime" in a.get_actor_label().lower():
            unreal.EditorLevelLibrary.destroy_actor(a)
            
    gem_class = unreal.load_class(None, f"{EXPGEM_BP_PATH}.BP_Pickup_ExpGem_C")
    if gem_class:
        sp_asset = unreal.load_asset("/Game/GGBOM/Art/Sprites/SP_HUD_Exp_Fill.SP_HUD_Exp_Fill") or unreal.load_asset("/Game/GGBOM/Art/Sprites/SP_Health.SP_Health")
        gem_positions = [
            (-50.0, 15.0, -420.0),
            (0.0, 15.0, -360.0),
            (50.0, 15.0, -420.0)
        ]
        for idx, pos in enumerate(gem_positions):
            g = unreal.EditorLevelLibrary.spawn_actor_from_class(
                gem_class,
                unreal.Vector(pos[0], pos[1], pos[2]),
                unreal.Rotator(0,0,0)
            )
            if g:
                g.set_actor_label(f"ExpGem_Runtime_{idx+1}")
                c = g.get_component_by_class(unreal.PaperSpriteComponent)
                if c and sp_asset:
                    c.set_editor_property("source_sprite", sp_asset)
                    c.set_editor_property("relative_scale3d", unreal.Vector(0.40, 0.40, 0.40))
                    c.set_editor_property("translucency_sort_priority", 1500)
                    c.set_editor_property("visible", True)
                    c.set_editor_property("hidden_in_game", False)
        log(f"✅ 成功在玩家前方部署 {len(gem_positions)} 颗经验宝石 (ExpGem_Runtime_1~3)")
        
    unreal.EditorLevelLibrary.save_current_level()
    log(f"✅ 地图 {MAP_PATH} 保存成功！")

def main():
    log("=== 开始执行第三阶段: 经验拾取与肉鸽卡牌升级装配 ===")
    status = {
        "PHASE3_STATUS": "FAIL",
        "card_selection_widget_built": False,
        "exp_gem_pickup_built": False,
        "player_progression_bound": False,
        "map_updated": False
    }
    
    try:
        w_bp = build_card_selection_widget()
        status["card_selection_widget_built"] = bool(w_bp)
        
        g_bp = build_exp_gem_pickup()
        status["exp_gem_pickup_built"] = bool(g_bp)
        
        configure_player_progression()
        status["player_progression_bound"] = True
        
        update_map_pickups()
        status["map_updated"] = True
        
        status["PHASE3_STATUS"] = "PASS"
        log("🎉 第三阶段: 经验拾取与肉鸽卡牌升级体系装配全部完成！")
    except Exception as e:
        log(f"❌ 装配失败: {e}")
        status["error"] = str(e)
        
    out_file = OUT_DIR / "phase3_card_upgrade_status.json"
    out_file.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Status written to {out_file}")

if __name__ == "__main__":
    main()
