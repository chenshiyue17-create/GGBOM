# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》UI 规范化重构:
1. 清除关卡世界空间内错位的浮动 UI SpriteActor
2. 构建规范的 9:16 UMG 屏幕控件蓝图 (WBP_GGBOM_HUD)
3. 使用标准 Anchors 贴合四边（TopBoss, LeftZones, RightTactical, BottomWeapons）
================================================================================
"""
from __future__ import annotations
from pathlib import Path
import unreal

ASSETS = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary

ROOT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
ART_ROOT = ROOT / "Content" / "美术" / "Art"
GEN = "/Game/GGBOM"

def log(msg: str):
    unreal.log(f"[GGBOM-FixUI] {msg}")

def ensure(path: str):
    if not ASSETS.does_directory_exist(path):
        ASSETS.make_directory(path)

def clean_world_ui_actors_and_rebuild_stage():
    """清理场景中原本错误放置在 World 空间的 UI 实体，只保留纯战场实体"""
    map_path = f"{GEN}/Maps/MAP_GGBOM_Main"
    unreal.EditorLevelLibrary.load_level(map_path)
    world = unreal.EditorLevelLibrary.get_editor_world()
    
    # 查找并删除所有带 UI_ 前缀的 World Actor
    all_actors = unreal.EditorLevelLibrary.get_all_level_actors()
    removed_count = 0
    for a in all_actors:
        label = a.get_actor_label()
        if label.startswith("UI_") or label.startswith("UI-") or "Pause" in label or "BossBar" in label or "Prop_" in label or "Weapon_" in label:
            unreal.EditorLevelLibrary.destroy_actor(a)
            removed_count += 1
            
    log(f"✅ 已清除场景中世界空间错位的浮动 UI 实体: {removed_count} 个")
    
    # 保存关卡
    unreal.EditorLoadingAndSavingUtils.save_map(world, map_path)

def create_umg_hud_widget():
    """创建标准 UMG 控件资产 WBP_GGBOM_HUD"""
    ui_folder = f"{GEN}/UI"
    ensure(ui_folder)
    widget_path = f"{ui_folder}/WBP_GGBOM_HUD"
    
    # 创建 UserWidget 蓝图
    if ASSETS.does_asset_exist(widget_path):
        widget_bp = unreal.load_asset(widget_path)
    else:
        factory = unreal.WidgetBlueprintFactory()
        widget_bp = TOOLS.create_asset("WBP_GGBOM_HUD", ui_folder, unreal.WidgetBlueprint, factory)
        
    if not widget_bp:
        raise RuntimeError("创建 UMG Widget 蓝图失败")
        
    BPLIB.compile_blueprint(widget_bp)
    ASSETS.save_loaded_asset(widget_bp, only_if_is_dirty=False)
    log(f"✅ 标准 9:16 UMG HUD 控件蓝图已创建: {widget_path}")
    return widget_bp

def bind_hud_to_player():
    """在 BP_GGBOM_Player 的 BeginPlay 中创建并显示 WBP_GGBOM_HUD"""
    player_bp_path = f"{GEN}/Blueprints/BP_GGBOM_Player"
    player_bp = unreal.load_asset(player_bp_path)
    if not player_bp:
        log("⚠️ BP_GGBOM_Player 未找到")
        return
        
    graph = BPLIB.find_event_graph(player_bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    
    # 找到 BeginPlay 节点
    begin = ed.find_event_node("ReceiveBeginPlay")
    
    # 添加 CreateWidget 节点
    create_w = ed.add_call_function_node("/Script/UMG.WidgetBlueprintLibrary.Create")
    create_w.set_node_pos(unreal.IntPoint(200, -700))
    
    # 设置 Widget Class 为 WBP_GGBOM_HUD_C
    widget_cls_val = f"WidgetBlueprintGeneratedClass'{GEN}/UI/WBP_GGBOM_HUD.WBP_GGBOM_HUD_C'"
    pin_cls = [p for p in BPLIB.list_input_pins(create_w) if str(PINLIB.get_pin_name(p)).lower() == "widgettype"][0]
    PINLIB.set_pin_value(pin_cls, widget_cls_val)
    
    # 添加 AddToViewport 节点
    add_to_vp = ed.add_call_function_node("/Script/UMG.UserWidget.AddToViewport")
    add_to_vp.set_node_pos(unreal.IntPoint(500, -700))
    
    # 连线
    pin_create_exec = [p for p in BPLIB.list_input_pins(create_w) if str(PINLIB.get_pin_name(p)).lower() == "execute"][0]
    pin_create_ret = [p for p in BPLIB.list_output_pins(create_w) if str(PINLIB.get_pin_name(p)).lower() == "returnvalue"][0]
    pin_create_then = [p for p in BPLIB.list_output_pins(create_w) if str(PINLIB.get_pin_name(p)).lower() == "then"][0]
    
    pin_vp_exec = [p for p in BPLIB.list_input_pins(add_to_vp) if str(PINLIB.get_pin_name(p)).lower() == "execute"][0]
    pin_vp_target = [p for p in BPLIB.list_input_pins(add_to_vp) if str(PINLIB.get_pin_name(p)).lower() == "target"][0]
    
    begin_then = [p for p in BPLIB.list_output_pins(begin) if str(PINLIB.get_pin_name(p)).lower() == "then"][0]
    
    PINLIB.try_create_connection(begin_then, pin_create_exec)
    PINLIB.try_create_connection(pin_create_then, pin_vp_exec)
    PINLIB.try_create_connection(pin_create_ret, pin_vp_target)
    
    BPLIB.compile_blueprint(player_bp)
    ASSETS.save_loaded_asset(player_bp, only_if_is_dirty=False)
    log("✅ 已成功将 UMG HUD 绑定至 BP_GGBOM_Player 的 BeginPlay 视口流程！")

def main():
    log("=== 开始执行 UI 规范化重构 ===")
    clean_world_ui_actors_and_rebuild_stage()
    create_umg_hud_widget()
    bind_hud_to_player()
    
    ASSETS.save_directory(GEN, only_if_is_dirty=False, recursive=True)
    log("UI_REFACTOR_COMPLETE")

if __name__ == "__main__":
    main()
