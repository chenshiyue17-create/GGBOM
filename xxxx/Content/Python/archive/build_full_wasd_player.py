# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》全功能 WASD 键盘移动与平滑操控系统 (Full WASD Controller)
================================================================================
"""
from __future__ import annotations
import unreal

ASSETS = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
SUBOBJECTS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
PINLIB = unreal.BlueprintGraphPinLibrary
BPLIB = unreal.BlueprintEditorLibrary

GEN = "/Game/GGBOM"
BLUEPRINTS = f"{GEN}/Blueprints"
PLAYER_BP_PATH = f"{BLUEPRINTS}/BP_GGBOM_Player"

def log(msg: str):
    unreal.log(f"[GGBOM-WASD] {msg}")

def ensure(path: str):
    if not ASSETS.does_directory_exist(path):
        ASSETS.make_directory(path)

def pin(node: unreal.K2Node, name: str, output: bool) -> unreal.BlueprintGraphPin:
    values = BPLIB.list_output_pins(node) if output else BPLIB.list_input_pins(node)
    wanted = name.lower()
    exact = [p for p in values if str(PINLIB.get_pin_name(p)).lower() == wanted]
    if len(exact) == 1:
        return exact[0]
    raise RuntimeError(f"Pin {name} not found; available={[str(PINLIB.get_pin_name(p)) for p in values]}")

def set_value(node: unreal.K2Node, name: str, value: any) -> None:
    target = pin(node, name, False)
    if not PINLIB.set_pin_value(target, str(value)):
        raise RuntimeError(f"Default rejected: {name}={value}")

def connect(a: unreal.K2Node, a_pin: str, b: unreal.K2Node, b_pin: str) -> None:
    source, target = pin(a, a_pin, True), pin(b, b_pin, False)
    if not PINLIB.try_create_connection(source, target):
        raise RuntimeError(f"Connection rejected: {a_pin} -> {b_pin}")

def fn(editor: unreal.BlueprintGraphEditor, path: str, x: int, y: int) -> unreal.K2Node:
    node = editor.add_call_function_node(path)
    if not node:
        raise RuntimeError(f"Function node failed: {path}")
    node.set_node_pos(unreal.IntPoint(x, y))
    return node

def add_component(bp: unreal.Blueprint, name: str, cls: unreal.Class) -> unreal.ActorComponent:
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

def build_wasd_player_blueprint():
    log("🔨 构建全向 WASD 可操控主角蓝图...")
    ensure(BLUEPRINTS)
    
    if ASSETS.does_asset_exist(PLAYER_BP_PATH):
        ASSETS.delete_asset(PLAYER_BP_PATH)
        
    bp = BPLIB.create_blueprint_asset_with_parent(PLAYER_BP_PATH, unreal.Pawn.static_class())
    if not bp:
        raise RuntimeError(f"创建蓝图失败: {PLAYER_BP_PATH}")
        
    # 碰撞盒
    collision = add_component(bp, "Collision", unreal.BoxComponent.static_class())
    collision.set_editor_property("box_extent", unreal.Vector(36, 24, 50))
    collision.set_collision_profile_name("Pawn")
    
    # 动画组件
    flipbook_comp = add_component(bp, "Sprite", unreal.PaperFlipbookComponent.static_class())
    fb_idle = unreal.load_asset("/Game/P01/Imported/Content/Asset/Art/01_Player/01_Idle_Run/Dir_05_Up/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_05_Up_Sheet")
    mat = unreal.load_asset("/Paper2D/TranslucentUnlitSpriteMaterial")
    if fb_idle:
        flipbook_comp.set_editor_property("source_flipbook", fb_idle)
    if mat:
        flipbook_comp.set_material(0, mat)
    flipbook_comp.set_editor_property("translucency_sort_priority", 30)
    
    # CDO 自动附身 Player0
    cdo = unreal.get_default_object(bp.generated_class())
    if cdo:
        cdo.set_editor_property("auto_possess_player", unreal.AutoReceiveInput.PLAYER0)
        cdo.set_editor_property("auto_receive_input", unreal.AutoReceiveInput.PLAYER0)
        
    # 构建 Event Graph 里的 WASD 移动逻辑
    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    
    tick = ed.find_event_node("ReceiveTick")
    pc = fn(ed, "/Script/Engine.GameplayStatics.GetPlayerController", 0, 0)
    set_value(pc, "PlayerIndex", 0)
    
    # A (Left: +X), D (Right: -X), W (Up: +Z), S (Down: -Z)
    key_a = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 240, -160); set_value(key_a, "Key", "A")
    key_d = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 240, -60);  set_value(key_d, "Key", "D")
    key_w = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 240, 40);   set_value(key_w, "Key", "W")
    key_s = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 240, 140);  set_value(key_s, "Key", "S")
    
    connect(pc, "ReturnValue", key_a, "self")
    connect(pc, "ReturnValue", key_d, "self")
    connect(pc, "ReturnValue", key_w, "self")
    connect(pc, "ReturnValue", key_s, "self")
    
    br_a = ed.add_branch_node(); br_a.set_node_pos(unreal.IntPoint(480, -160))
    br_d = ed.add_branch_node(); br_d.set_node_pos(unreal.IntPoint(480, -60))
    br_w = ed.add_branch_node(); br_w.set_node_pos(unreal.IntPoint(480, 40))
    br_s = ed.add_branch_node(); br_s.set_node_pos(unreal.IntPoint(480, 140))
    
    connect(tick, "then", br_a, "execute"); connect(key_a, "ReturnValue", br_a, "Condition")
    connect(br_a, "else", br_d, "execute"); connect(key_d, "ReturnValue", br_d, "Condition")
    connect(br_d, "else", br_w, "execute"); connect(key_w, "ReturnValue", br_w, "Condition")
    connect(br_w, "else", br_s, "execute"); connect(key_s, "ReturnValue", br_s, "Condition")
    
    moves = [
        (br_a, 480.0, 0.0, 0.0, -200),    # A: 左移 (+X)
        (br_d, -480.0, 0.0, 0.0, -80),    # D: 右移 (-X)
        (br_w, 0.0, 0.0, 480.0, 40),     # W: 上移 (+Z)
        (br_s, 0.0, 0.0, -480.0, 160),   # S: 下移 (-Z)
    ]
    for branch, dx, dy, dz, ypos in moves:
        vec = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 720, ypos)
        set_value(vec, "X", dx); set_value(vec, "Y", dy); set_value(vec, "Z", dz)
        mul = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_VectorFloat", 920, ypos)
        move = fn(ed, "/Script/Engine.Actor.K2_AddActorWorldOffset", 1140, ypos)
        set_value(move, "bSweep", "true")
        
        connect(vec, "ReturnValue", mul, "A")
        connect(tick, "DeltaSeconds", mul, "B")
        connect(branch, "then", move, "execute")
        connect(mul, "ReturnValue", move, "DeltaLocation")
        
    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log("✅ BP_GGBOM_Player WASD 控制器构建完成！")
    return bp

def update_map_with_playable_player():
    map_path = f"{GEN}/Maps/MAP_GGBOM_Main"
    unreal.EditorLevelLibrary.load_level(map_path)
    world = unreal.EditorLevelLibrary.get_editor_world()
    
    # 移除原本残留的角色
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        lbl = a.get_actor_label()
        if "Player_Medic" in lbl or "BP_GGBOM_Player" in lbl:
            try:
                unreal.EditorLevelLibrary.destroy_actor(a)
            except Exception:
                pass
                
    p_pos = unreal.Vector(0.0, -10.0, -600.0)
    player_bp_cls = unreal.load_class(None, f"{PLAYER_BP_PATH}.BP_GGBOM_Player_C")
    if player_bp_cls:
        player_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(player_bp_cls, p_pos, unreal.Rotator())
        if player_actor:
            player_actor.set_actor_label("BP_GGBOM_Player_WASD")
            player_actor.set_actor_scale3d(unreal.Vector(0.65, 0.65, 0.65))
            player_actor.set_editor_property("auto_possess_player", unreal.AutoReceiveInput.PLAYER0)
            log("🎉 成功在主关卡中生成并激活 WASD 可控主角: BP_GGBOM_Player_WASD (AutoPossess: Player0)")
            
    unreal.EditorLoadingAndSavingUtils.save_map(world, map_path)
    ASSETS.save_directory(GEN, only_if_is_dirty=False, recursive=True)

def main():
    build_wasd_player_blueprint()
    update_map_with_playable_player()

if __name__ == "__main__":
    main()
