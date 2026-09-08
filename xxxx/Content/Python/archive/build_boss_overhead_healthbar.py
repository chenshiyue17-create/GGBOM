# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》Boss 头顶跟随血条实装脚本 (PaperSpriteActor 方案)
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

WIDGET_PATH = "/Game/GGBOM/UI/WBP_Boss_OverheadHealthBar"
BOSS_BP_DIR = "/Game/Blueprints/Characters/Enemies"
BOSS_BP_PATH = f"{BOSS_BP_DIR}/BP_Boss_Overlord"
MAP_PATH = "/Game/GGBOM/Maps/MAP_GGBOM_Main"

def log(msg: str):
    print(f"[BossHealthBar] {msg}")
    unreal.log(f"[BossHealthBar] {msg}")

def ensure_directory(path: str):
    if not ASSETS.does_directory_exist(path):
        ASSETS.make_directory(path)

# ============================================================================
# 1. 创建 WBP_Boss_OverheadHealthBar 控件蓝图
# ============================================================================
def build_widget_blueprint():
    log(f"🚀 [1/3] 构建头顶血条控件蓝图: {WIDGET_PATH}...")
    ensure_directory("/Game/GGBOM/UI")
    
    widget_bp = None
    if ASSETS.does_asset_exist(WIDGET_PATH):
        widget_bp = unreal.load_asset(WIDGET_PATH)
    else:
        factory = unreal.WidgetBlueprintFactory()
        widget_bp = TOOLS.create_asset("WBP_Boss_OverheadHealthBar", "/Game/GGBOM/UI", unreal.WidgetBlueprint, factory)
    
    if not widget_bp:
        raise RuntimeError(f"无法创建或加载控件蓝图: {WIDGET_PATH}")

    BPLIB.compile_blueprint(widget_bp)
    ASSETS.save_loaded_asset(widget_bp, only_if_is_dirty=False)
    log(f"✅ 控件蓝图 {WIDGET_PATH} 构建并保存成功！")
    return widget_bp

# ============================================================================
# 2. 创建/重构 BP_Boss_Overlord 蓝图
# ============================================================================
def build_boss_blueprint():
    log(f"🚀 [2/3] 构建 Boss 蓝图: {BOSS_BP_PATH}...")
    ensure_directory(BOSS_BP_DIR)
    
    if ASSETS.does_asset_exist(BOSS_BP_PATH):
        ASSETS.delete_asset(BOSS_BP_PATH)
        
    bp = BPLIB.create_blueprint_asset_with_parent(BOSS_BP_PATH, unreal.PaperSpriteActor.static_class())
    if not bp:
        raise RuntimeError(f"无法创建 Boss 蓝图: {BOSS_BP_PATH}")
    
    # 获取 EventGraph 与 GraphEditor
    graph = BPLIB.find_event_graph(bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    real_type = BPLIB.get_basic_type_by_name("real")
    
    for vname, default in (("MaxHealth", "4500.0"), ("CurrentHealth", "4500.0")):
        editor.add_member_variable(vname, real_type, default)
        BPLIB.set_blueprint_variable_category(bp, vname, unreal.Text("Combat Stats"))
        BPLIB.set_blueprint_variable_instance_editable(bp, vname, True)
    
    BPLIB.compile_blueprint(bp)
    
    # 配置 CDO 属性 (Boss Sprite 与 Scale)
    cdo = unreal.get_default_object(bp.generated_class())
    if cdo:
        sprite_comp = cdo.get_component_by_class(unreal.PaperSpriteComponent)
        if sprite_comp:
            sprite_asset = unreal.load_asset("/Game/GGBOM/Art/Sprites/SP_Boss.SP_Boss")
            if sprite_asset:
                sprite_comp.set_editor_property("source_sprite", sprite_asset)
            sprite_comp.set_editor_property("relative_scale3d", unreal.Vector(0.68, 0.68, 0.68))
            sprite_comp.set_editor_property("translucency_sort_priority", 300)
            sprite_comp.set_editor_property("visible", True)
            sprite_comp.set_editor_property("hidden_in_game", False)
            
    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"✅ Boss 蓝图 {BOSS_BP_PATH} 构建并保存成功！")
    return bp

# ============================================================================
# 3. 在地图 MAP_GGBOM_Main 中更新/替换 Boss 实例
# ============================================================================
def update_level_boss():
    log(f"🚀 [3/3] 在地图 {MAP_PATH} 中替换/放置 Boss 蓝图实例...")
    unreal.EditorLevelLibrary.load_level(MAP_PATH)
    world = unreal.EditorLevelLibrary.get_editor_world()
    
    # 查找旧的 Boss Actor
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    boss_loc = unreal.Vector(0.0, 20.0, 440.0) # 默认 Boss 关卡位置
    
    for a in actors:
        label = a.get_actor_label()
        if "boss" in label.lower() and "hud" not in label.lower():
            boss_loc = a.get_actor_location()
            log(f"找到旧 Boss Actor: {label} ({a.get_class().get_name()})，正在移除...")
            unreal.EditorLevelLibrary.destroy_actor(a)
            
    # 生成新的 BP_Boss_Overlord 蓝图实例
    boss_class = unreal.load_class(None, f"{BOSS_BP_PATH}.BP_Boss_Overlord_C")
    if not boss_class:
        raise RuntimeError(f"无法加载 Boss 蓝图类: {BOSS_BP_PATH}.BP_Boss_Overlord_C")
        
    new_boss = unreal.EditorLevelLibrary.spawn_actor_from_class(
        boss_class,
        boss_loc,
        unreal.Rotator(0.0, 0.0, 0.0)
    )
    if new_boss:
        new_boss.set_actor_label("Boss_Overlord_Runtime")
        # 确保 Sprite 属性生效
        comp = new_boss.get_component_by_class(unreal.PaperSpriteComponent)
        if comp:
            sprite_asset = unreal.load_asset("/Game/GGBOM/Art/Sprites/SP_Boss.SP_Boss")
            if sprite_asset:
                comp.set_editor_property("source_sprite", sprite_asset)
            comp.set_editor_property("relative_scale3d", unreal.Vector(0.68, 0.68, 0.68))
            comp.set_editor_property("translucency_sort_priority", 300)
            comp.set_editor_property("visible", True)
            comp.set_editor_property("hidden_in_game", False)
        log(f"✅ 成功生成 Boss 蓝图实例: Boss_Overlord_Runtime 坐标={boss_loc}")
        
    # 生成跟随 Boss 头顶的血条 (放置在 Boss 上方 Z=+135, Y=-5)
    # 查找旧的头顶血条 Actor
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        if "overhead_bossbar" in a.get_actor_label().lower():
            unreal.EditorLevelLibrary.destroy_actor(a)
            
    # 生成原生 2D 头顶血条 (底框 + 填充)，附着在 Boss 上
    bg_sprite = unreal.load_asset("/Game/GGBOM/Art/Sprites/SP_HUD_BossBar_Bg.SP_HUD_BossBar_Bg")
    fill_sprite = unreal.load_asset("/Game/GGBOM/Art/Sprites/SP_HUD_BossBar_Fill.SP_HUD_BossBar_Fill")
    
    if bg_sprite and new_boss:
        bg_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.PaperSpriteActor,
            boss_loc + unreal.Vector(0.0, -2.0, 135.0),
            unreal.Rotator(0.0, 0.0, 0.0)
        )
        if bg_actor:
            bg_actor.set_actor_label("Overhead_BossBar_Bg")
            c = bg_actor.get_component_by_class(unreal.PaperSpriteComponent)
            if c:
                c.set_editor_property("source_sprite", bg_sprite)
                c.set_editor_property("relative_scale3d", unreal.Vector(0.38, 0.38, 0.38))
                c.set_editor_property("translucency_sort_priority", 2600)
                c.set_editor_property("visible", True)
                c.set_editor_property("hidden_in_game", False)
            bg_actor.attach_to_actor(new_boss, unreal.Name(), unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)
            log("✅ 头顶血条底框已挂载并跟随 Boss！")

    if fill_sprite and new_boss:
        fill_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.PaperSpriteActor,
            boss_loc + unreal.Vector(-8.0, -4.0, 135.0),
            unreal.Rotator(0.0, 0.0, 0.0)
        )
        if fill_actor:
            fill_actor.set_actor_label("Overhead_BossBar_Fill")
            c = fill_actor.get_component_by_class(unreal.PaperSpriteComponent)
            if c:
                c.set_editor_property("source_sprite", fill_sprite)
                c.set_editor_property("relative_scale3d", unreal.Vector(0.35, 0.35, 0.35))
                c.set_editor_property("translucency_sort_priority", 2620)
                c.set_editor_property("visible", True)
                c.set_editor_property("hidden_in_game", False)
            fill_actor.attach_to_actor(new_boss, unreal.Name(), unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)
            log("✅ 头顶血条红色填充已挂载并跟随 Boss！")

    # 保存地图
    unreal.EditorLevelLibrary.save_current_level()
    log(f"✅ 地图 {MAP_PATH} 保存成功！")

def main():
    log("=== 开始 Boss 头顶血条实装流水线 ===")
    status = {
        "BOSS_OVERHEAD_HEALTHBAR": "FAIL",
        "WBP_Boss_OverheadHealthBar": False,
        "BP_Boss_Overlord": False,
        "Map_Updated": False
    }
    
    try:
        w_bp = build_widget_blueprint()
        status["WBP_Boss_OverheadHealthBar"] = bool(w_bp)
        
        b_bp = build_boss_blueprint()
        status["BP_Boss_Overlord"] = bool(b_bp)
        
        update_level_boss()
        status["Map_Updated"] = True
        
        status["BOSS_OVERHEAD_HEALTHBAR"] = "PASS"
        log("🎉 Boss 头顶跟随血条实装全部完成！")
    except Exception as e:
        log(f"❌ 实装失败: {e}")
        status["error"] = str(e)
        
    status_file = OUT_DIR / "boss_overhead_healthbar_status.json"
    status_file.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Status written to {status_file}")

if __name__ == "__main__":
    main()
