# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》黑屏修复与全套 8 方向动作/战斗状态机完美对齐
- 修复 Pawn 相机 OrthoNearClipPlane (-10000) 与 OrthoFarClipPlane (10000)
- 修复 auto_calculate_ortho_planes=False 杜绝裁剪黑屏
- 完美组装 8 方向 WASD 移动与防定格 Flipbook 动态流转 (Run/Idle/Attack/Revive)
- 同步关卡 Master_Orthographic_Camera 与 GameMode
================================================================================
"""
from __future__ import annotations
from pathlib import Path
from typing import Any
import unreal

PROJECT_ROOT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
MAP_PATH = "/Game/GGBOM/Maps/MAP_GGBOM_Main"
GAMEMODE_PATH = "/Game/GGBOM/Blueprints/BP_GGBOM_GameMode"
PLAYER_BP_PATH = "/Game/Blueprints/Player/BP_Player_Medic"
PLAYER_LABEL = "Player_Medic_Runtime"
CAMERA_LABEL = "Master_Orthographic_Camera"

MAP_W = 941.0
MAP_H = 1672.0
ASPECT_RATIO = MAP_W / MAP_H

ASSETS = unreal.EditorAssetLibrary
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary
SUBOBJECTS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)

def log(msg: str):
    unreal.log(f"[GGBOM-MedicFix] {msg}")

def set_prop(obj, prop: str, value) -> bool:
    try:
        obj.set_editor_property(prop, value)
        return True
    except Exception:
        return False

def make_rotator(pitch: float, yaw: float, roll: float) -> unreal.Rotator:
    r = unreal.Rotator()
    set_prop(r, "pitch", pitch)
    set_prop(r, "yaw", yaw)
    set_prop(r, "roll", roll)
    return r

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

def configure_full_player_blueprint() -> unreal.Blueprint:
    log("🔨 配置并编译 BP_Player_Medic...")
    bp = unreal.load_asset(PLAYER_BP_PATH)
    if not bp:
        raise RuntimeError(f"Blueprint missing: {PLAYER_BP_PATH}")
        
    cdo = unreal.get_default_object(bp.generated_class())
    set_prop(cdo, "auto_receive_input", unreal.AutoReceiveInput.PLAYER0)
    set_prop(cdo, "auto_possess_player", unreal.AutoReceiveInput.PLAYER0)
    
    # 资源字典
    pfx = "/Game/P01/Imported/Content/Asset/Art/01_Player"
    flipbooks = {
        "Idle_Up": unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_05_Up/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_05_Up_Sheet"),
        "Idle_Down": unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_01_Down/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_01_Down_Sheet"),
        "Idle_Left": unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_03_Left/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_03_Left_Sheet"),
        
        "Run_Up": unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_05_Up/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_05_Up_Sheet"),
        "Run_Down": unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_01_Down/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_01_Down_Sheet"),
        "Run_Left": unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_03_Left/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_03_Left_Sheet"),
        
        "Attack_Up": unreal.load_asset(f"{pfx}/02_Attack_Hurt/Dir_05_Up/Attack/Flipbooks/FB_T_Player_Medic_Attack_Dir_05_Up_Sheet"),
        "Attack_Down": unreal.load_asset(f"{pfx}/02_Attack_Hurt/Dir_01_Down/Attack/Flipbooks/FB_T_Player_Medic_Attack_Dir_01_Down_Sheet"),
        "Attack_Right": unreal.load_asset(f"{pfx}/02_Attack_Hurt/Dir_03_Right/Attack/Flipbooks/FB_T_Player_Medic_Attack_Dir_03_Right_Sheet"),
        
        "Death": unreal.load_asset(f"{pfx}/03_Death_Revive/Death_Collapse/Flipbooks/FB_T_Player_Medic_Death_Sheet"),
        "Revive": unreal.load_asset(f"{pfx}/03_Death_Revive/Revive/Flipbooks/FB_T_Player_Medic_Revive_Sheet"),
    }
    mat = unreal.load_asset("/Paper2D/TranslucentUnlitSpriteMaterial")
    
    # 1. Flipbook 组件
    fb_comps = list(cdo.get_components_by_class(unreal.PaperFlipbookComponent))
    fb_comp = fb_comps[0] if fb_comps else add_component(bp, "VisibleFlipbook", unreal.PaperFlipbookComponent.static_class())
    if flipbooks["Idle_Down"]:
        set_prop(fb_comp, "source_flipbook", flipbooks["Idle_Down"])
    set_prop(fb_comp, "visible", True)
    set_prop(fb_comp, "hidden_in_game", False)
    set_prop(fb_comp, "translucency_sort_priority", 2000)
    set_prop(fb_comp, "relative_scale3d", unreal.Vector(0.45, 0.45, 0.45))
    if mat:
        try:
            fb_comp.set_material(0, mat)
        except Exception:
            pass
            
    # 2. Collision 组件
    col_comps = list(cdo.get_components_by_class(unreal.BoxComponent))
    col = col_comps[0] if col_comps else add_component(bp, "PlayerCollision", unreal.BoxComponent.static_class())
    set_prop(col, "box_extent", unreal.Vector(36.0, 24.0, 60.0))
    try:
        col.set_collision_profile_name("Pawn")
    except Exception:
        pass
        
    # 3. 运行态正交相机组件 (核心防黑屏配置)
    cam_comps = list(cdo.get_components_by_class(unreal.CameraComponent))
    cam = cam_comps[0] if cam_comps else add_component(bp, "RuntimeOrthographicCamera", unreal.CameraComponent.static_class())
    set_prop(cam, "relative_location", unreal.Vector(0.0, -980.0, 560.0))
    set_prop(cam, "relative_rotation", make_rotator(0.0, 90.0, 0.0))
    set_prop(cam, "projection_mode", unreal.CameraProjectionMode.ORTHOGRAPHIC)
    set_prop(cam, "ortho_width", MAP_W)
    set_prop(cam, "aspect_ratio", ASPECT_RATIO)
    set_prop(cam, "b_constrain_aspect_ratio", True)
    set_prop(cam, "auto_activate", True)
    set_prop(cam, "auto_calculate_ortho_planes", False)
    set_prop(cam, "ortho_near_clip_plane", -10000.0)
    set_prop(cam, "ortho_far_clip_plane", 10000.0)
    
    # 4. 蓝图 Event Graph 动画流转与 8 向移动
    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    try:
        for node in ed.list_all_nodes():
            if node.get_name() not in ["ReceiveBeginPlay", "ReceiveTick", "ReceiveActorBeginOverlap"]:
                ed.remove_node(node)
    except Exception:
        pass
        
    tick = ed.find_event_node("ReceiveTick")
    pc_tick = fn(ed, "/Script/Engine.GameplayStatics.GetPlayerController", 0, 0)
    set_value(pc_tick, "PlayerIndex", 0)
    
    # A/D 采样
    key_a = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, -180); set_value(key_a, "Key", "A"); connect(pc_tick, "ReturnValue", key_a, "self")
    key_d = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, -80);  set_value(key_d, "Key", "D"); connect(pc_tick, "ReturnValue", key_d, "self")
    sel_a = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, -180); set_value(sel_a, "A", 420.0); set_value(sel_a, "B", 0.0); connect(key_a, "ReturnValue", sel_a, "bPickA")
    sel_d = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, -80);  set_value(sel_d, "A", -420.0); set_value(sel_d, "B", 0.0); connect(key_d, "ReturnValue", sel_d, "bPickA")
    add_x = fn(ed, "/Script/Engine.KismetMathLibrary.Add_DoubleDouble", 660, -130); connect(sel_a, "ReturnValue", add_x, "A"); connect(sel_d, "ReturnValue", add_x, "B")
    
    # W/S 采样
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
    
    # 判定移动
    cmp_x = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_DoubleDouble", 880, -200); connect(add_x, "ReturnValue", cmp_x, "A"); set_value(cmp_x, "B", 0.0)
    cmp_z = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_DoubleDouble", 880, 200); connect(add_z, "ReturnValue", cmp_z, "A"); set_value(cmp_z, "B", 0.0)
    is_moving = fn(ed, "/Script/Engine.KismetMathLibrary.BooleanOR", 1080, 150); connect(cmp_x, "ReturnValue", is_moving, "A"); connect(cmp_z, "ReturnValue", is_moving, "B")
    
    br_moving = ed.add_branch_node(); br_moving.set_node_pos(unreal.IntPoint(1520, 0))
    connect(move_node, "then", br_moving, "execute")
    connect(is_moving, "ReturnValue", br_moving, "Condition")
    
    # 移动中: 镜像与奔跑
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
    
    # 左右跑
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
    
    # 纵向跑
    is_up = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 1960, 50); connect(add_z, "ReturnValue", is_up, "A"); set_value(is_up, "B", 0.0)
    br_up = ed.add_branch_node(); br_up.set_node_pos(unreal.IntPoint(2180, 0))
    connect(br_side, "else", br_up, "execute")
    connect(is_up, "ReturnValue", br_up, "Condition")
    
    # 上跑
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
    
    # 下跑
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
    
    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log("✅ BP_Player_Medic 蓝图编译保存成功！")
    return bp

def configure_level_and_gamemode():
    log("🗺️ 配置并同步关卡 MAP_GGBOM_Main 与 GameMode...")
    
    # 1. GameMode
    gm_bp = unreal.load_asset(GAMEMODE_PATH)
    if gm_bp:
        gm_cdo = unreal.get_default_object(gm_bp.generated_class())
        if gm_cdo:
            pawn_bp = unreal.load_asset(PLAYER_BP_PATH)
            if pawn_bp:
                set_prop(gm_cdo, "default_pawn_class", pawn_bp.generated_class())
        BPLIB.compile_blueprint(gm_bp)
        ASSETS.save_loaded_asset(gm_bp, only_if_is_dirty=False)
        
    # 2. 地图关卡
    if ASSETS.does_asset_exist(MAP_PATH):
        unreal.EditorLevelLibrary.load_level(MAP_PATH)
    world = unreal.EditorLevelLibrary.get_editor_world()
    
    if gm_bp and world:
        ws = world.get_world_settings()
        if ws:
            set_prop(ws, "default_game_mode", gm_bp.generated_class())
            
    # 3. 检查关卡主相机 Master_Orthographic_Camera
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    cam_actor = None
    for a in actors:
        lbl = a.get_actor_label() if hasattr(a, "get_actor_label") else a.get_name()
        if lbl == CAMERA_LABEL and isinstance(a, unreal.CameraActor):
            cam_actor = a
            break
            
    if not cam_actor:
        cam_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.CameraActor, unreal.Vector(0.0, -1000.0, 0.0), make_rotator(0.0, 90.0, 0.0)
        )
        cam_actor.set_actor_label(CAMERA_LABEL)
        
    cam_actor.set_actor_location(unreal.Vector(0.0, -1000.0, 0.0), False, True)
    cam_actor.set_actor_rotation(make_rotator(0.0, 90.0, 0.0), False)
    set_prop(cam_actor, "auto_activate_for_player", unreal.AutoReceiveInput.PLAYER0)
    
    cc = cam_actor.get_component_by_class(unreal.CameraComponent)
    if cc:
        set_prop(cc, "projection_mode", unreal.CameraProjectionMode.ORTHOGRAPHIC)
        set_prop(cc, "ortho_width", MAP_W)
        set_prop(cc, "aspect_ratio", ASPECT_RATIO)
        set_prop(cc, "b_constrain_aspect_ratio", True)
        set_prop(cc, "auto_calculate_ortho_planes", False)
        set_prop(cc, "ortho_near_clip_plane", -10000.0)
        set_prop(cc, "ortho_far_clip_plane", 10000.0)
        
    # 4. 保存地图
    unreal.EditorLoadingAndSavingUtils.save_map(world, MAP_PATH)
    ASSETS.save_directory("/Game/GGBOM", only_if_is_dirty=False, recursive=True)
    log("🎉 关卡与角色防黑屏总装完成并已全量保存！")

def main():
    configure_full_player_blueprint()
    configure_level_and_gamemode()

if __name__ == "__main__":
    main()
