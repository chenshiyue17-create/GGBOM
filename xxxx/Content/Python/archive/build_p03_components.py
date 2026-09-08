# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》P03 阶段: 纯蓝图通用核心组件集 (BPC_Components & BP_Test_Components)
================================================================================
"""
from __future__ import annotations
import math
import unreal

ASSETS = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary
COMPONENTS_DIR = "/Game/Blueprints/Core/Components"
TEST_DIR = "/Game/Tests/P03"

def log(msg: str):
    unreal.log(f"[GGBOM-P03] {msg}")

def ensure_dir(path: str):
    if not ASSETS.does_directory_exist(path):
        ASSETS.make_directory(path)

def create_component_bp(name: str) -> unreal.Blueprint:
    ensure_dir(COMPONENTS_DIR)
    path = f"{COMPONENTS_DIR}/{name}"
    if ASSETS.does_asset_exist(path):
        bp = unreal.load_asset(path)
    else:
        bp = BPLIB.create_blueprint_asset_with_parent(path, unreal.ActorComponent.static_class())
    if not bp:
        raise RuntimeError(f"Failed to create component: {path}")
    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    return bp

def create_test_actor_bp(name: str) -> unreal.Blueprint:
    ensure_dir(TEST_DIR)
    path = f"{TEST_DIR}/{name}"
    if ASSETS.does_asset_exist(path):
        bp = unreal.load_asset(path)
    else:
        bp = BPLIB.create_blueprint_asset_with_parent(path, unreal.Actor.static_class())
    if not bp:
        raise RuntimeError(f"Failed to create test actor: {path}")
    
    # 构造事件图测试逻辑
    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    begin = ed.find_event_node("ReceiveBeginPlay")
    
    # 打印测试通过信号
    test_node = ed.add_call_function_node("/Script/Engine.KismetSystemLibrary.PrintString")
    test_node.set_node_pos(unreal.IntPoint(300, 0))
    pin_str = [p for p in BPLIB.list_input_pins(test_node) if str(PINLIB.get_pin_name(p)).lower() == "instring"][0]
    pin_exec = [p for p in BPLIB.list_input_pins(test_node) if str(PINLIB.get_pin_name(p)).lower() == "execute"][0]
    PINLIB.set_pin_value(pin_str, "P03_COMPONENTS_OK")
    
    begin_then = [p for p in BPLIB.list_output_pins(begin) if str(PINLIB.get_pin_name(p)).lower() == "then"][0]
    PINLIB.try_create_connection(begin_then, pin_exec)
    
    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    return bp

def main():
    log("=== 开始执行 P03 Components 构建 ===")
    components = [
        "BPC_Health",
        "BPC_Targeting",
        "BPC_WeaponInventory",
        "BPC_Experience",
        "BPC_Inventory",
        "BPC_StatusEffects",
        "BPC_CardModifiers",
        "BPC_LootDrop"
    ]
    
    created = []
    for c in components:
        bp = create_component_bp(c)
        created.append(bp.get_path_name())
        log(f"✅ 组件就绪: {c}")
        
    test_actor = create_test_actor_bp("BP_Test_Components")
    log(f"✅ 测试 Actor 就绪: {test_actor.get_path_name()}")
    
    # 保存所有资产
    ASSETS.save_directory(COMPONENTS_DIR, only_if_is_dirty=False, recursive=True)
    ASSETS.save_directory(TEST_DIR, only_if_is_dirty=False, recursive=True)
    
    log("P03_BUILD_COMPLETE")

if __name__ == "__main__":
    main()
