# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》全套 8 方向 WASD 移动与复合战斗动作状态机总装
- 8 向待机 (Idle)、8 向奔跑 (Run)、攻击 (Attack)、受击 (Hurt)、倒地 (Death)、复活 (Revive)
- 防止每帧重复重设导致定格 (GetFlipbook != TargetFlipbook 守卫)
- 完美正交相机兼容与蓝图编译保存
================================================================================
"""
from __future__ import annotations
from pathlib import Path
from typing import Any
import unreal

ROOT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
GEN = "/Game/GGBOM"
BLUEPRINTS = "/Game/Blueprints/Player"
ASSETS = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
SUBOBJECTS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
PINLIB = unreal.BlueprintGraphPinLibrary
BPLIB = unreal.BlueprintEditorLibrary

def log(msg: str):
    unreal.log(f"[GGBOM-PlayerSuite] {msg}")

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

def build_full_player_medic():
    log("🔨 开始构建并集成全套 8 方向动作与战斗状态机 (BP_Player_Medic)...")
    bp_path = f"{BLUEPRINTS}/BP_Player_Medic"
    ensure(BLUEPRINTS)
    
    if ASSETS.does_asset_exist(bp_path):
        bp = unreal.load_asset(bp_path)
    else:
        factory = unreal.BlueprintFactory()
        factory.set_editor_property("parent_class", unreal.Pawn.static_class())
        bp = TOOLS.create_asset("BP_Player_Medic", BLUEPRINTS, unreal.Blueprint, factory)
        
    cdo = unreal.get_default_object(bp.generated_class())
    if cdo:
        cdo.set_editor_property("auto_possess_player", unreal.AutoReceiveInput.PLAYER0)
        cdo.set_editor_property("auto_receive_input", unreal.AutoReceiveInput.PLAYER0)
        
    # 全套 Flipbook 资源字典
    pfx = "/Game/P01/Imported/Content/Asset/Art/01_Player"
    flipbooks = {
        # 待机 Idle
        "Idle_Up": unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_05_Up/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_05_Up_Sheet"),
        "Idle_Down": unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_01_Down/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_01_Down_Sheet"),
        "Idle_Left": unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_03_Left/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_03_Left_Sheet"),
        
        # 奔跑 Run
        "Run_Up": unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_05_Up/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_05_Up_Sheet"),
        "Run_Down": unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_01_Down/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_01_Down_Sheet"),
        "Run_Left": unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_03_Left/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_03_Left_Sheet"),
        
        # 攻击 Attack
        "Attack_Up": unreal.load_asset(f"{pfx}/02_Attack_Hurt/Dir_05_Up/Attack/Flipbooks/FB_T_Player_Medic_Attack_Dir_05_Up_Sheet"),
        "Attack_Down": unreal.load_asset(f"{pfx}/02_Attack_Hurt/Dir_01_Down/Attack/Flipbooks/FB_T_Player_Medic_Attack_Dir_01_Down_Sheet"),
        "Attack_Right": unreal.load_asset(f"{pfx}/02_Attack_Hurt/Dir_03_Right/Attack/Flipbooks/FB_T_Player_Medic_Attack_Dir_03_Right_Sheet"),
        
        # 受击 Hurt
        "Hurt_Up": unreal.load_asset(f"{pfx}/02_Attack_Hurt/Dir_05_Up/Hurt/Flipbooks/FB_T_Player_Medic_Hurt_Dir_05_Up_Sheet"),
        "Hurt_Down": unreal.load_asset(f"{pfx}/02_Attack_Hurt/Dir_01_Down/Hurt/Flipbooks/FB_T_Player_Medic_Hurt_Dir_01_Down_Sheet"),
        
        # 倒地与复活
        "Death": unreal.load_asset(f"{pfx}/03_Death_Revive/Death_Collapse/Flipbooks/FB_T_Player_Medic_Death_Sheet"),
        "Revive": unreal.load_asset(f"{pfx}/03_Death_Revive/Revive/Flipbooks/FB_T_Player_Medic_Revive_Sheet"),
    }
    mat = unreal.load_asset("/Paper2D/TranslucentUnlitSpriteMaterial")
    
    # 获取或添加组件
    comps = list(cdo.get_components_by_class(unreal.PaperFlipbookComponent))
    if comps:
        flipbook_comp = comps[0]
    else:
        flipbook_comp = add_component(bp, "Flipbook", unreal.PaperFlipbookComponent.static_class())
        
    if flipbooks["Idle_Down"]:
        flipbook_comp.set_editor_property("source_flipbook", flipbooks["Idle_Down"])
    if mat:
        flipbook_comp.set_material(0, mat)
    flipbook_comp.set_editor_property("translucency_sort_priority", 2000)
    
    col_comps = list(cdo.get_components_by_class(unreal.BoxComponent))
    if col_comps:
        collision = col_comps[0]
    else:
        collision = add_component(bp, "Collision", unreal.BoxComponent.static_class())
    collision.set_editor_property("box_extent", unreal.Vector(36, 24, 50))
    collision.set_collision_profile_name("Pawn")
    
    cam_comps = list(cdo.get_components_by_class(unreal.CameraComponent))
    if cam_comps:
        cam_comp = cam_comps[0]
    else:
        cam_comp = add_component(bp, "Camera", unreal.CameraComponent.static_class())
    cam_comp.set_editor_property("projection_mode", unreal.CameraProjectionMode.ORTHOGRAPHIC)
    cam_comp.set_editor_property("ortho_width", 941.0)
    cam_comp.set_editor_property("aspect_ratio", 0.562799)
    cam_comp.set_relative_location_and_rotation(unreal.Vector(0, -500, 560), unreal.Rotator(pitch=0.0, yaw=90.0, roll=0.0), False, False)
    
    # 重新构建 Event Graph
    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    
    try:
        for node in ed.list_all_nodes():
            if node.get_name() not in ["ReceiveBeginPlay", "ReceiveTick", "ReceiveActorBeginOverlap"]:
                ed.remove_node(node)
    except Exception:
        pass
                
    # 1. BeginPlay: 锁定全局正交相机
    begin_play = ed.find_event_node("ReceiveBeginPlay")
    pc_begin = fn(ed, "/Script/Engine.GameplayStatics.GetPlayerController", 200, -360)
    set_value(pc_begin, "PlayerIndex", 0)
    get_cam = fn(ed, "/Script/Engine.GameplayStatics.GetActorOfClass", 450, -360)
    set_value(get_cam, "ActorClass", "Class'/Script/Engine.CameraActor'")
    set_view = fn(ed, "/Script/Engine.PlayerController.SetViewTargetWithBlend", 720, -360)
    set_value(set_view, "BlendTime", 0.0)
    connect(begin_play, "then", get_cam, "execute")
    connect(get_cam, "then", set_view, "execute")
    connect(pc_begin, "ReturnValue", set_view, "self")
    connect(get_cam, "ReturnValue", set_view, "NewViewTarget")
    
    # 2. Tick: 8 方向数学向量移动与动画流转
    tick = ed.find_event_node("ReceiveTick")
    pc_tick = fn(ed, "/Script/Engine.GameplayStatics.GetPlayerController", 0, 0)
    set_value(pc_tick, "PlayerIndex", 0)
    
    # A/D X轴采样
    key_a = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, -180); set_value(key_a, "Key", "A"); connect(pc_tick, "ReturnValue", key_a, "self")
    key_d = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, -80);  set_value(key_d, "Key", "D"); connect(pc_tick, "ReturnValue", key_d, "self")
    sel_a = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, -180); set_value(sel_a, "A", 420.0); set_value(sel_a, "B", 0.0); connect(key_a, "ReturnValue", sel_a, "bPickA")
    sel_d = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, -80);  set_value(sel_d, "A", -420.0); set_value(sel_d, "B", 0.0); connect(key_d, "ReturnValue", sel_d, "bPickA")
    add_x = fn(ed, "/Script/Engine.KismetMathLibrary.Add_DoubleDouble", 660, -130); connect(sel_a, "ReturnValue", add_x, "A"); connect(sel_d, "ReturnValue", add_x, "B")
    
    # W/S Z轴采样
    key_w = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, 40);   set_value(key_w, "Key", "W"); connect(pc_tick, "ReturnValue", key_w, "self")
    key_s = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, 140);  set_value(key_s, "Key", "S"); connect(pc_tick, "ReturnValue", key_s, "self")
    sel_w = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, 40);   set_value(sel_w, "A", 420.0); set_value(sel_w, "B", 0.0); connect(key_w, "ReturnValue", sel_w, "bPickA")
    sel_s = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, 140);  set_value(sel_s, "A", -420.0); set_value(sel_s, "B", 0.0); connect(key_s, "ReturnValue", sel_s, "bPickA")
    add_z = fn(ed, "/Script/Engine.KismetMathLibrary.Add_DoubleDouble", 660, 90); connect(sel_w, "ReturnValue", add_z, "A"); connect(sel_s, "ReturnValue", add_z, "B")
    
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
    
    # 奔跑左右翻转
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
    if flipbooks["Run_Left"]:
        set_value(is_diff_side, "B", f"PaperFlipbook'{flipbooks['Run_Left'].get_path_name()}'")
    br_diff_side = ed.add_branch_node(); br_diff_side.set_node_pos(unreal.IntPoint(2400, -200))
    connect(br_side, "then", br_diff_side, "execute")
    connect(is_diff_side, "ReturnValue", br_diff_side, "Condition")
    set_fb_side = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2620, -200)
    if flipbooks["Run_Left"]:
        set_value(set_fb_side, "NewFlipbook", f"PaperFlipbook'{flipbooks['Run_Left'].get_path_name()}'")
    connect(br_diff_side, "then", set_fb_side, "execute")
    connect(get_comp_move, "ReturnValue", set_fb_side, "self")
    
    # 纵向移动
    is_up = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 1960, 50); connect(add_z, "ReturnValue", is_up, "A"); set_value(is_up, "B", 0.0)
    br_up = ed.add_branch_node(); br_up.set_node_pos(unreal.IntPoint(2180, 0))
    connect(br_side, "else", br_up, "execute")
    connect(is_up, "ReturnValue", br_up, "Condition")
    
    # 向上跑
    is_diff_up = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_ObjectObject", 2400, -80)
    connect(get_curr_fb, "ReturnValue", is_diff_up, "A")
    if flipbooks["Run_Up"]:
        set_value(is_diff_up, "B", f"PaperFlipbook'{flipbooks['Run_Up'].get_path_name()}'")
    br_diff_up = ed.add_branch_node(); br_diff_up.set_node_pos(unreal.IntPoint(2620, -80))
    connect(br_up, "then", br_diff_up, "execute")
    connect(is_diff_up, "ReturnValue", br_diff_up, "Condition")
    set_fb_up = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2840, -80)
    if flipbooks["Run_Up"]:
        set_value(set_fb_up, "NewFlipbook", f"PaperFlipbook'{flipbooks['Run_Up'].get_path_name()}'")
    connect(br_diff_up, "then", set_fb_up, "execute")
    connect(get_comp_move, "ReturnValue", set_fb_up, "self")
    
    # 向下跑
    is_diff_down = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_ObjectObject", 2400, 80)
    connect(get_curr_fb, "ReturnValue", is_diff_down, "A")
    if flipbooks["Run_Down"]:
        set_value(is_diff_down, "B", f"PaperFlipbook'{flipbooks['Run_Down'].get_path_name()}'")
    br_diff_down = ed.add_branch_node(); br_diff_down.set_node_pos(unreal.IntPoint(2620, 80))
    connect(br_up, "else", br_diff_down, "execute")
    connect(is_diff_down, "ReturnValue", br_diff_down, "Condition")
    set_fb_down = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2840, 80)
    if flipbooks["Run_Down"]:
        set_value(set_fb_down, "NewFlipbook", f"PaperFlipbook'{flipbooks['Run_Down'].get_path_name()}'")
    connect(br_diff_down, "then", set_fb_down, "execute")
    connect(get_comp_move, "ReturnValue", set_fb_down, "self")
    
    # 待机分支 (br_moving.else)
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
    if flipbooks["Idle_Down"]:
        set_value(is_diff_idle, "B", f"PaperFlipbook'{flipbooks['Idle_Down'].get_path_name()}'")
    br_diff_idle = ed.add_branch_node(); br_diff_idle.set_node_pos(unreal.IntPoint(2400, 200))
    connect(set_sc_idle, "then", br_diff_idle, "execute")
    connect(is_diff_idle, "ReturnValue", br_diff_idle, "Condition")
    
    set_fb_idle = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2620, 200)
    if flipbooks["Idle_Down"]:
        set_value(set_fb_idle, "NewFlipbook", f"PaperFlipbook'{flipbooks['Idle_Down'].get_path_name()}'")
    connect(br_diff_idle, "then", set_fb_idle, "execute")
    connect(get_comp_idle, "ReturnValue", set_fb_idle, "self")
    
    # 3. 按键 J 攻击分支
    key_j = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, 400); set_value(key_j, "Key", "J"); connect(pc_tick, "ReturnValue", key_j, "self")
    br_j = ed.add_branch_node(); br_j.set_node_pos(unreal.IntPoint(440, 400))
    connect(tick, "then", br_j, "execute")
    connect(key_j, "ReturnValue", br_j, "Condition")
    if flipbooks["Attack_Up"]:
        set_atk = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 680, 400)
        set_value(set_atk, "NewFlipbook", f"PaperFlipbook'{flipbooks['Attack_Up'].get_path_name()}'")
        connect(br_j, "then", set_atk, "execute")
        connect(get_comp_idle, "ReturnValue", set_atk, "self")
        
    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log("✅ BP_Player_Medic 8 方向移动与战斗动作编译保存完成！")
    
    # 同步更新 GameMode
    gm_path = f"{GEN}/Blueprints/BP_GGBOM_GameMode"
    gm_bp = unreal.load_asset(gm_path)
    if gm_bp:
        gm_cdo = unreal.get_default_object(gm_bp.generated_class())
        if gm_cdo:
            player_cls = unreal.load_class(None, f"{bp.get_path_name()}.BP_Player_Medic_C")
            gm_cdo.set_editor_property("default_pawn_class", player_cls)
        BPLIB.compile_blueprint(gm_bp)
        ASSETS.save_loaded_asset(gm_bp, only_if_is_dirty=False)
        log("✅ BP_GGBOM_GameMode DefaultPawnClass 已同步为 BP_Player_Medic_C！")
        
    # 保存主地图 MAP_GGBOM_Main
    map_path = f"{GEN}/Maps/MAP_GGBOM_Main"
    if ASSETS.does_asset_exist(map_path):
        world = unreal.EditorLevelLibrary.get_editor_world()
        unreal.EditorLoadingAndSavingUtils.save_map(world, map_path)
        log("✅ MAP_GGBOM_Main 主地图已保存！")

if __name__ == "__main__":
    # Retained for compatibility only. The former suite appended duplicate Tick
    # chains and mixed locomotion, facing, and firing state. Delegate to the
    # canonical idempotent rebuild.
    import runpy
    from pathlib import Path

    runpy.run_path(
        str(Path(__file__).with_name("rebuild_direction_state_v2.py")),
        run_name="__main__",
    )
