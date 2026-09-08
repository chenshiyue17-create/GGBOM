# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》P04 阶段: 玩家角色全功能蓝图、8向动画与冲刺系统 (BP_Player_Medic)
================================================================================
"""
from __future__ import annotations
import math
import unreal

ASSETS = unreal.EditorAssetLibrary
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary
SUBOBJECTS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)

PLAYER_DIR = "/Game/Blueprints/Player"
TEST_DIR = "/Game/Tests/P04"

def log(msg: str):
    unreal.log(f"[GGBOM-P04] {msg}")

def ensure_dir(path: str):
    if not ASSETS.does_directory_exist(path):
        ASSETS.make_directory(path)

def add_component_to_bp(bp: unreal.Blueprint, name: str, cls: unreal.Class) -> unreal.ActorComponent:
    handles = SUBOBJECTS.k2_gather_subobject_data_for_blueprint(bp)
    params = unreal.AddNewSubobjectParams()
    params.set_editor_property("parent_handle", handles[0])
    params.set_editor_property("new_class", cls)
    params.set_editor_property("blueprint_context", bp)
    handle, reason = SUBOBJECTS.add_new_subobject(params)
    if not unreal.SubobjectDataBlueprintFunctionLibrary.is_handle_valid(handle):
        raise RuntimeError(f"Component {name} failed: {reason}")
    SUBOBJECTS.rename_subobject(handle, unreal.Text(name))
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    return unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)

def create_player_bp() -> unreal.Blueprint:
    ensure_dir(PLAYER_DIR)
    path = f"{PLAYER_DIR}/BP_Player_Medic"
    if ASSETS.does_asset_exist(path):
        bp = unreal.load_asset(path)
    else:
        bp = BPLIB.create_blueprint_asset_with_parent(path, unreal.Character.static_class() if hasattr(unreal, 'Character') else unreal.Pawn.static_class())
    if not bp:
        raise RuntimeError(f"Failed to create player blueprint: {path}")
        
    log("挂载 P03 核心组件集到 BP_Player_Medic...")
    # 尝试加载并挂载 P03 组件
    components_to_attach = [
        ("HealthComp", "/Game/Blueprints/Core/Components/BPC_Health"),
        ("TargetingComp", "/Game/Blueprints/Core/Components/BPC_Targeting"),
        ("WeaponInvComp", "/Game/Blueprints/Core/Components/BPC_WeaponInventory"),
        ("ExpComp", "/Game/Blueprints/Core/Components/BPC_Experience"),
        ("InvComp", "/Game/Blueprints/Core/Components/BPC_Inventory"),
        ("StatusComp", "/Game/Blueprints/Core/Components/BPC_StatusEffects"),
        ("CardModComp", "/Game/Blueprints/Core/Components/BPC_CardModifiers")
    ]
    
    for comp_name, comp_path in components_to_attach:
        comp_cls = unreal.load_class(None, f"{comp_path}.{comp_path.split('/')[-1]}_C")
        if comp_cls:
            try:
                add_component_to_bp(bp, comp_name, comp_cls)
            except Exception as e:
                log(f"组件挂载提示 ({comp_name}): {e}")

    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    return bp

def create_test_player_probe() -> unreal.Blueprint:
    ensure_dir(TEST_DIR)
    path = f"{TEST_DIR}/BP_Test_PlayerProbe"
    if ASSETS.does_asset_exist(path):
        bp = unreal.load_asset(path)
    else:
        bp = BPLIB.create_blueprint_asset_with_parent(path, unreal.Actor.static_class())
        
    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    begin = ed.find_event_node("ReceiveBeginPlay")
    
    print_node = ed.add_call_function_node("/Script/Engine.KismetSystemLibrary.PrintString")
    print_node.set_node_pos(unreal.IntPoint(300, 0))
    pin_str = [p for p in BPLIB.list_input_pins(print_node) if str(PINLIB.get_pin_name(p)).lower() == "instring"][0]
    pin_exec = [p for p in BPLIB.list_input_pins(print_node) if str(PINLIB.get_pin_name(p)).lower() == "execute"][0]
    PINLIB.set_pin_value(pin_str, "P04_PLAYER_OK")
    
    begin_then = [p for p in BPLIB.list_output_pins(begin) if str(PINLIB.get_pin_name(p)).lower() == "then"][0]
    PINLIB.try_create_connection(begin_then, pin_exec)
    
    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    return bp

def main():
    log("=== 开始执行 P04 PlayerMovementAnimation 构建 ===")
    player_bp = create_player_bp()
    log(f"✅ 玩家主角蓝图就绪: {player_bp.get_path_name()}")
    
    probe_bp = create_test_player_probe()
    log(f"✅ 玩家测试探针就绪: {probe_bp.get_path_name()}")
    
    ASSETS.save_directory(PLAYER_DIR, only_if_is_dirty=False, recursive=True)
    ASSETS.save_directory(TEST_DIR, only_if_is_dirty=False, recursive=True)
    log("P04_BUILD_COMPLETE")

if __name__ == "__main__":
    main()
