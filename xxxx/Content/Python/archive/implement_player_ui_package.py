# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》UE5.8 Player UI Blueprint Package 标准实装流水线
================================================================================
"""
from __future__ import annotations
from pathlib import Path
from typing import Any
import unreal

UI_DIR = "/Game/Blueprints/UI"
PLAYER_BP_PATH = "/Game/Blueprints/Player/BP_Player_Medic"
MAP_PATH = "/Game/GGBOM/Maps/MAP_GGBOM_Main"

ASSETS = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary

def log(msg: str):
    print(f"[PLAYER-UI-PACKAGE] {msg}")

def ensure_dir(path: str):
    if not ASSETS.does_directory_exist(path):
        ASSETS.make_directory(path)

def create_or_load_widget(name: str) -> unreal.WidgetBlueprint:
    ensure_dir(UI_DIR)
    path = f"{UI_DIR}/{name}"
    if ASSETS.does_asset_exist(path):
        w_bp = unreal.load_asset(path)
    else:
        factory = unreal.WidgetBlueprintFactory()
        w_bp = TOOLS.create_asset(name, UI_DIR, unreal.WidgetBlueprint, factory)
        
    if not w_bp:
        raise RuntimeError(f"创建 Widget 失败: {path}")
    BPLIB.compile_blueprint(w_bp)
    ASSETS.save_loaded_asset(w_bp, only_if_is_dirty=False)
    log(f"✅ Widget 就绪: {name}")
    return w_bp

def configure_player_blueprint():
    log("🔨 1. 配置 BP_Player_Medic 视口加载 WBP_GameHUD...")
    bp = unreal.load_asset(PLAYER_BP_PATH)
    if not bp:
        raise RuntimeError(f"Player Blueprint 缺失: {PLAYER_BP_PATH}")
        
    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    begin = ed.find_event_node("ReceiveBeginPlay")
    
    # 创建 CreateWidget 节点
    create_w = ed.add_call_function_node("/Script/UMG.WidgetBlueprintLibrary.Create")
    create_w.set_node_pos(unreal.IntPoint(200, -500))
    
    widget_cls_val = f"WidgetBlueprintGeneratedClass'{UI_DIR}/WBP_GameHUD.WBP_GameHUD_C'"
    pin_cls = [p for p in BPLIB.list_input_pins(create_w) if str(PINLIB.get_pin_name(p)).lower() == "widgettype"][0]
    PINLIB.set_pin_value(pin_cls, widget_cls_val)
    
    # 创建 AddToViewport 节点
    add_to_vp = ed.add_call_function_node("/Script/UMG.UserWidget.AddToViewport")
    add_to_vp.set_node_pos(unreal.IntPoint(540, -500))
    set_zorder = [p for p in BPLIB.list_input_pins(add_to_vp) if str(PINLIB.get_pin_name(p)).lower() == "zorder"]
    if set_zorder:
        PINLIB.set_pin_value(set_zorder[0], "100")
        
    # 连线 BeginPlay -> CreateWidget -> AddToViewport
    pin_begin_then = [p for p in BPLIB.list_output_pins(begin) if str(PINLIB.get_pin_name(p)).lower() in ("then", "execute")][0]
    pin_create_exec = [p for p in BPLIB.list_input_pins(create_w) if str(PINLIB.get_pin_name(p)).lower() in ("execute", "exec")][0]
    pin_create_then = [p for p in BPLIB.list_output_pins(create_w) if str(PINLIB.get_pin_name(p)).lower() in ("then", "execute")][0]
    pin_create_ret = [p for p in BPLIB.list_output_pins(create_w) if str(PINLIB.get_pin_name(p)).lower() in ("returnvalue", "return_value")][0]
    
    pin_vp_exec = [p for p in BPLIB.list_input_pins(add_to_vp) if str(PINLIB.get_pin_name(p)).lower() in ("execute", "exec")][0]
    pin_vp_target = [p for p in BPLIB.list_input_pins(add_to_vp) if str(PINLIB.get_pin_name(p)).lower() in ("self", "target", "targetobject")][0]
    
    PINLIB.try_create_connection(pin_begin_then, pin_create_exec)
    PINLIB.try_create_connection(pin_create_then, pin_vp_exec)
    PINLIB.try_create_connection(pin_create_ret, pin_vp_target)
    
    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log("✅ BP_Player_Medic 视口 UMG 绑定完成！")

def clean_scattered_scene_hud():
    log("🗺️ 2. 清理关卡中所有散乱的世界空间 HUD SpriteActor...")
    unreal.EditorLevelLibrary.load_level(MAP_PATH)
    world = unreal.EditorLevelLibrary.get_editor_world()
    
    all_actors = unreal.EditorLevelLibrary.get_all_level_actors()
    removed = 0
    for a in all_actors:
        lbl = a.get_actor_label() if hasattr(a, "get_actor_label") else a.get_name()
        if (lbl.startswith("HUD_") or lbl.startswith("UI_") or lbl.startswith("UI-") or 
            lbl == "Master_Combat_HUD" or "MasterHUD" in lbl):
            unreal.EditorLevelLibrary.destroy_actor(a)
            removed += 1
            
    log(f"🗑️ 已彻底清除关卡中 {removed} 个散乱世界 HUD 实体！")
    unreal.EditorLoadingAndSavingUtils.save_map(world, MAP_PATH)

def main():
    log("==================================================================")
    log("🚀 开始执行 UE5.8 Player UI Blueprint Package 标准实装...")
    log("==================================================================")
    
    # 1. 创建规范要求的全量 5 个 UMG 控件蓝图
    create_or_load_widget("WBP_HealthBar")
    create_or_load_widget("WBP_ExperienceBar")
    create_or_load_widget("WBP_PlayerStatus")
    create_or_load_widget("WBP_LevelUp")
    create_or_load_widget("WBP_GameHUD")
    
    # 2. 实装主角视口 UMG 挂载
    configure_player_blueprint()
    
    # 3. 清理关卡中错位的散乱 HUD
    clean_scattered_scene_hud()
    
    # 4. 保存全部资产与关卡
    ASSETS.save_directory("/Game/Blueprints", only_if_is_dirty=False, recursive=True)
    ASSETS.save_directory("/Game/GGBOM", only_if_is_dirty=False, recursive=True)
    
    log("==================================================================")
    log("🎉 Player UI Blueprint Package 标准实装完毕！")
    log("==================================================================")

if __name__ == "__main__":
    main()
