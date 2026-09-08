# -*- coding: utf-8 -*-
"""
================================================================================
彻底重建 100% 纯净单组件主角蓝图 BP_Player_Medic
- 确保内部仅有 1 个 PaperFlipbookComponent (SingleFlipbook)
- 精准绑定 8 方向 WASD 移动与 Idle/Run 动画流转
- 绑定 GameMode 与关卡
================================================================================
"""
from __future__ import annotations
from typing import Any
import unreal

BLUEPRINT_PATH = "/Game/Blueprints/Player/BP_Player_Medic"
GAMEMODE_PATH = "/Game/GGBOM/Blueprints/BP_GGBOM_GameMode"
MAP_PATH = "/Game/GGBOM/Maps/MAP_GGBOM_Main"

ASSETS = unreal.EditorAssetLibrary
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
SUBOBJECTS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)

def log(msg: str):
    print(f"[REBUILD-MEDIC] {msg}")

def pin(node: unreal.K2Node, name: str, output: bool) -> unreal.BlueprintGraphPin:
    values = BPLIB.list_output_pins(node) if output else BPLIB.list_input_pins(node)
    wanted = name.lower()
    exact = [p for p in values if str(PINLIB.get_pin_name(p)).lower() == wanted]
    if len(exact) == 1:
        return exact[0]
    raise RuntimeError(f"Pin {name} not found; available={[str(PINLIB.get_pin_name(p)) for p in values]}")

def set_value(node: unreal.K2Node, name: str, value: Any) -> None:
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

def add_single_subobject(bp: unreal.Blueprint, parent_handle, name: str, cls: unreal.Class):
    params = unreal.AddNewSubobjectParams()
    params.set_editor_property("parent_handle", parent_handle)
    params.set_editor_property("new_class", cls)
    params.set_editor_property("blueprint_context", bp)
    handle, reason = SUBOBJECTS.add_new_subobject(params)
    if not unreal.SubobjectDataBlueprintFunctionLibrary.is_handle_valid(handle):
        raise RuntimeError(f"Component {name} failed: {reason}")
    SUBOBJECTS.rename_subobject(handle, unreal.Text(name))
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    return handle, unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)

def main():
    log("✨ 1. 创建 100% 崭新纯净 Pawn 蓝图...")
    if not ASSETS.does_directory_exist("/Game/Blueprints/Player"):
        ASSETS.make_directory("/Game/Blueprints/Player")
        
    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", unreal.Pawn.static_class())
    bp = TOOLS.create_asset("BP_Player_Medic", "/Game/Blueprints/Player", unreal.Blueprint, factory)
    
    if not bp:
        raise RuntimeError("创建 BP_Player_Medic 失败！")

    # 配置 CDO 接收输入与拥有玩家
    cdo = unreal.get_default_object(bp.generated_class())
    cdo.set_editor_property("auto_receive_input", unreal.AutoReceiveInput.PLAYER0)
    cdo.set_editor_property("auto_possess_player", unreal.AutoReceiveInput.PLAYER0)

    # 载入动作 Flipbook 资源
    pfx = "/Game/P01/Imported/Content/Asset/Art/01_Player"
    fb_idle_down = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_01_Down/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_01_Down_Sheet")
    fb_run_down = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_01_Down/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_01_Down_Sheet")
    fb_run_up = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_05_Up/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_05_Up_Sheet")
    fb_run_left = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_03_Left/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_03_Left_Sheet")
    mat = unreal.load_asset("/Paper2D/TranslucentUnlitSpriteMaterial")

    # 2. 仅添加单体组件结构: Root -> PlayerCollision -> SingleFlipbook
    log("📦 2. 挂载单体 Collision 与 唯一 PaperFlipbookComponent...")
    handles = SUBOBJECTS.k2_gather_subobject_data_for_blueprint(bp)
    root_handle = handles[0]
    
    col_handle, col_comp = add_single_subobject(bp, root_handle, "PlayerCollision", unreal.BoxComponent.static_class())
    col_comp.set_editor_property("box_extent", unreal.Vector(36.0, 24.0, 50.0))
    col_comp.set_editor_property("relative_location", unreal.Vector(0.0, 0.0, 50.0))
    
    fb_handle, fb_comp = add_single_subobject(bp, col_handle, "SingleFlipbook", unreal.PaperFlipbookComponent.static_class())
    if fb_idle_down:
        fb_comp.set_editor_property("source_flipbook", fb_idle_down)
    if mat:
        fb_comp.set_material(0, mat)
    fb_comp.set_editor_property("relative_scale3d", unreal.Vector(0.45, 0.45, 0.45))
    fb_comp.set_editor_property("translucency_sort_priority", 2000)
    fb_comp.set_editor_property("visible", True)
    fb_comp.set_editor_property("hidden_in_game", False)

    # 3. 构建 Event Graph (平滑 8 向移动与待机/奔跑动画无缝切换)
    log("🎮 3. 构建蓝图 Event Graph 动作状态机...")
    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    
    tick = ed.find_event_node("ReceiveTick")
    pc_tick = fn(ed, "/Script/Engine.GameplayStatics.GetPlayerController", 0, 0)
    set_value(pc_tick, "PlayerIndex", 0)
    
    # A/D
    key_a = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, -180); set_value(key_a, "Key", "A"); connect(pc_tick, "ReturnValue", key_a, "self")
    key_d = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, -80);  set_value(key_d, "Key", "D"); connect(pc_tick, "ReturnValue", key_d, "self")
    sel_a = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, -180); set_value(sel_a, "A", 450.0); set_value(sel_a, "B", 0.0); connect(key_a, "ReturnValue", sel_a, "bPickA")
    sel_d = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, -80);  set_value(sel_d, "A", -450.0); set_value(sel_d, "B", 0.0); connect(key_d, "ReturnValue", sel_d, "bPickA")
    add_x = fn(ed, "/Script/Engine.KismetMathLibrary.Add_DoubleDouble", 660, -130); connect(sel_a, "ReturnValue", add_x, "A"); connect(sel_d, "ReturnValue", add_x, "B")
    
    # W/S
    key_w = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, 40);   set_value(key_w, "Key", "W"); connect(pc_tick, "ReturnValue", key_w, "self")
    key_s = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, 140);  set_value(key_s, "Key", "S"); connect(pc_tick, "ReturnValue", key_s, "self")
    sel_w = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, 40);   set_value(sel_w, "A", 450.0); set_value(sel_w, "B", 0.0); connect(key_w, "ReturnValue", sel_w, "bPickA")
    sel_s = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, 140);  set_value(sel_s, "A", -450.0); set_value(sel_s, "B", 0.0); connect(key_s, "ReturnValue", sel_s, "bPickA")
    add_z = fn(ed, "/Script/Engine.KismetMathLibrary.Add_DoubleDouble", 660, 90); connect(sel_w, "ReturnValue", add_z, "A"); connect(sel_s, "ReturnValue", add_z, "B")
    
    # Move
    make_vec = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 880, 0)
    connect(add_x, "ReturnValue", make_vec, "X")
    set_value(make_vec, "Y", 0.0)
    connect(add_z, "ReturnValue", make_vec, "Z")
    
    mul_dt = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_VectorFloat", 1080, 0)
    connect(make_vec, "ReturnValue", mul_dt, "A")
    connect(tick, "DeltaSeconds", mul_dt, "B")
    
    move_node = fn(ed, "/Script/Engine.Actor.K2_AddActorWorldOffset", 1300, 0)
    set_value(move_node, "bSweep", "true")
    connect(tick, "then", move_node, "execute")
    connect(mul_dt, "ReturnValue", move_node, "DeltaLocation")
    
    # 状态判定
    cmp_x = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_DoubleDouble", 880, -200); connect(add_x, "ReturnValue", cmp_x, "A"); set_value(cmp_x, "B", 0.0)
    cmp_z = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_DoubleDouble", 880, 200); connect(add_z, "ReturnValue", cmp_z, "A"); set_value(cmp_z, "B", 0.0)
    is_moving = fn(ed, "/Script/Engine.KismetMathLibrary.BooleanOR", 1080, 150); connect(cmp_x, "ReturnValue", is_moving, "A"); connect(cmp_z, "ReturnValue", is_moving, "B")
    
    br_moving = ed.add_branch_node(); br_moving.set_node_pos(unreal.IntPoint(1520, 0))
    connect(move_node, "then", br_moving, "execute")
    connect(is_moving, "ReturnValue", br_moving, "Condition")
    
    # 移动分支
    is_right = fn(ed, "/Script/Engine.KismetMathLibrary.Less_DoubleDouble", 1080, -100); connect(add_x, "ReturnValue", is_right, "A"); set_value(is_right, "B", 0.0)
    scale_val_x = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 1280, -100); set_value(scale_val_x, "A", -0.45); set_value(scale_val_x, "B", 0.45); connect(is_right, "ReturnValue", scale_val_x, "bPickA")
    scale_move_vec = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 1480, -100); connect(scale_val_x, "ReturnValue", scale_move_vec, "X"); set_value(scale_move_vec, "Y", 0.45); set_value(scale_move_vec, "Z", 0.45)
    
    get_comp_move = fn(ed, "/Script/Engine.Actor.GetComponentByClass", 1520, -200); set_value(get_comp_move, "ComponentClass", "Class'/Script/Paper2D.PaperFlipbookComponent'")
    set_sc_move = fn(ed, "/Script/Engine.SceneComponent.SetRelativeScale3D", 1740, -100)
    connect(br_moving, "then", set_sc_move, "execute")
    connect(get_comp_move, "ReturnValue", set_sc_move, "self")
    connect(scale_move_vec, "ReturnValue", set_sc_move, "NewScale3D")
    
    br_side = ed.add_branch_node(); br_side.set_node_pos(unreal.IntPoint(1960, -100))
    connect(set_sc_move, "then", br_side, "execute")
    connect(cmp_x, "ReturnValue", br_side, "Condition")
    
    get_curr_fb = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.GetFlipbook", 1960, -250)
    connect(get_comp_move, "ReturnValue", get_curr_fb, "self")
    
    # 左右奔跑
    is_diff_side = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_ObjectObject", 2180, -250)
    connect(get_curr_fb, "ReturnValue", is_diff_side, "A")
    if fb_run_left:
        set_value(is_diff_side, "B", f"PaperFlipbook'{fb_run_left.get_path_name()}'")
    br_diff_side = ed.add_branch_node(); br_diff_side.set_node_pos(unreal.IntPoint(2400, -200))
    connect(br_side, "then", br_diff_side, "execute")
    connect(is_diff_side, "ReturnValue", br_diff_side, "Condition")
    set_fb_side = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2620, -200)
    if fb_run_left:
        set_value(set_fb_side, "NewFlipbook", f"PaperFlipbook'{fb_run_left.get_path_name()}'")
    connect(br_diff_side, "then", set_fb_side, "execute")
    connect(get_comp_move, "ReturnValue", set_fb_side, "self")
    
    # 上下奔跑
    is_up = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 1960, 50); connect(add_z, "ReturnValue", is_up, "A"); set_value(is_up, "B", 0.0)
    br_up = ed.add_branch_node(); br_up.set_node_pos(unreal.IntPoint(2180, 0))
    connect(br_side, "else", br_up, "execute")
    connect(is_up, "ReturnValue", br_up, "Condition")
    
    # 上跑
    is_diff_up = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_ObjectObject", 2400, -80)
    connect(get_curr_fb, "ReturnValue", is_diff_up, "A")
    if fb_run_up:
        set_value(is_diff_up, "B", f"PaperFlipbook'{fb_run_up.get_path_name()}'")
    br_diff_up = ed.add_branch_node(); br_diff_up.set_node_pos(unreal.IntPoint(2620, -80))
    connect(br_up, "then", br_diff_up, "execute")
    connect(is_diff_up, "ReturnValue", br_diff_up, "Condition")
    set_fb_up = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2840, -80)
    if fb_run_up:
        set_value(set_fb_up, "NewFlipbook", f"PaperFlipbook'{fb_run_up.get_path_name()}'")
    connect(br_diff_up, "then", set_fb_up, "execute")
    connect(get_comp_move, "ReturnValue", set_fb_up, "self")
    
    # 下跑
    is_diff_down = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_ObjectObject", 2400, 80)
    connect(get_curr_fb, "ReturnValue", is_diff_down, "A")
    if fb_run_down:
        set_value(is_diff_down, "B", f"PaperFlipbook'{fb_run_down.get_path_name()}'")
    br_diff_down = ed.add_branch_node(); br_diff_down.set_node_pos(unreal.IntPoint(2620, 80))
    connect(br_up, "else", br_diff_down, "execute")
    connect(is_diff_down, "ReturnValue", br_diff_down, "Condition")
    set_fb_down = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2840, 80)
    if fb_run_down:
        set_value(set_fb_down, "NewFlipbook", f"PaperFlipbook'{fb_run_down.get_path_name()}'")
    connect(br_diff_down, "then", set_fb_down, "execute")
    connect(get_comp_move, "ReturnValue", set_fb_down, "self")
    
    # 待机分支
    get_comp_idle = fn(ed, "/Script/Engine.Actor.GetComponentByClass", 1520, 200); set_value(get_comp_idle, "ComponentClass", "Class'/Script/Paper2D.PaperFlipbookComponent'")
    scale_idle_vec = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 1520, 300); set_value(scale_idle_vec, "X", 0.45); set_value(scale_idle_vec, "Y", 0.45); set_value(scale_idle_vec, "Z", 0.45)
    set_sc_idle = fn(ed, "/Script/Engine.SceneComponent.SetRelativeScale3D", 1740, 200)
    connect(br_moving, "else", set_sc_idle, "execute")
    connect(get_comp_idle, "ReturnValue", set_sc_idle, "self")
    connect(scale_idle_vec, "ReturnValue", set_sc_idle, "NewScale3D")
    
    get_curr_idle_fb = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.GetFlipbook", 1960, 280)
    connect(get_comp_idle, "ReturnValue", get_curr_idle_fb, "self")
    is_diff_idle = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_ObjectObject", 2180, 280)
    connect(get_curr_idle_fb, "ReturnValue", is_diff_idle, "A")
    if fb_idle_down:
        set_value(is_diff_idle, "B", f"PaperFlipbook'{fb_idle_down.get_path_name()}'")
    br_diff_idle = ed.add_branch_node(); br_diff_idle.set_node_pos(unreal.IntPoint(2400, 200))
    connect(set_sc_idle, "then", br_diff_idle, "execute")
    connect(is_diff_idle, "ReturnValue", br_diff_idle, "Condition")
    
    set_fb_idle = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2620, 200)
    if fb_idle_down:
        set_value(set_fb_idle, "NewFlipbook", f"PaperFlipbook'{fb_idle_down.get_path_name()}'")
    connect(br_diff_idle, "then", set_fb_idle, "execute")
    connect(get_comp_idle, "ReturnValue", set_fb_idle, "self")

    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log("✅ 崭新纯净 BP_Player_Medic 编译并保存成功！")

    # 4. 更新 GameMode
    log("🎮 4. 同步 GameMode 的 DefaultPawnClass...")
    gm_bp = unreal.load_asset(GAMEMODE_PATH)
    if gm_bp:
        gm_cdo = unreal.get_default_object(gm_bp.generated_class())
        if gm_cdo:
            gm_cdo.set_editor_property("default_pawn_class", bp.generated_class())
        BPLIB.compile_blueprint(gm_bp)
        ASSETS.save_loaded_asset(gm_bp, only_if_is_dirty=False)

    # 5. 保存关卡与所有资产
    if ASSETS.does_asset_exist(MAP_PATH):
        unreal.EditorLevelLibrary.load_level(MAP_PATH)
        world = unreal.EditorLevelLibrary.get_editor_world()
        unreal.EditorLoadingAndSavingUtils.save_map(world, MAP_PATH)
    ASSETS.save_directory("/Game/GGBOM", only_if_is_dirty=False, recursive=True)
    ASSETS.save_directory("/Game/Blueprints", only_if_is_dirty=False, recursive=True)
    log("🎉 全量资产与关卡保存完毕！")

if __name__ == "__main__":
    main()
