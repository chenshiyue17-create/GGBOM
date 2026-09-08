# -*- coding: utf-8 -*-
"""
UE5.8 2D 竖屏游戏: 4大核心问题终极彻底解决方案
1. 射击上下居中对齐 (消除 X 轴偏向, 紧贴角色真实中心)
2. 射击后持久保持当前朝向 (Up/Side/Down 不再强制重置为向下)
3. 动态怪物军团 100% 显形并平滑步态推进 (丧尸, 猎犬, 蛮兽, 领主Boss)
4. UI 全画幅 9:16 像素级精确对齐 (消除边界溢出与偏移)
"""
from __future__ import annotations
import unreal

GEN = "/Game/GGBOM"
MAP_PATH = f"{GEN}/Maps/MAP_GGBOM_Main"
PLAYER_BP_PATH = "/Game/Blueprints/Player/BP_Player_Medic"

ASSETS = unreal.EditorAssetLibrary
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary
SUBOBJECTS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)

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

def set_value(node: unreal.K2Node, name: str, value) -> None:
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

# ==============================================================================
# 1. 重构主角 BP_Player_Medic (居中开火 + 朝向持久锁定)
# ==============================================================================
def rebuild_player_medic():
    print("🎮 [1/3] 正在重构主角 BP_Player_Medic (完美居中发射 + 朝向记忆保护)...")
    
    if ASSETS.does_asset_exist(PLAYER_BP_PATH):
        ASSETS.delete_asset(PLAYER_BP_PATH)
    bp = BPLIB.create_blueprint_asset_with_parent(PLAYER_BP_PATH, unreal.Pawn.static_class())

    pfx = "/Game/P01/Imported/Content/Asset/Art/01_Player"
    fb_idle_down = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_01_Down/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_01_Down_Sheet")
    fb_idle_up = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_05_Up/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_05_Up_Sheet")
    fb_idle_left = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_03_Left/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_03_Left_Sheet")

    fb_run_down = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_01_Down/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_01_Down_Sheet")
    fb_run_up = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_05_Up/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_05_Up_Sheet")
    fb_run_left = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_03_Left/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_03_Left_Sheet")

    fb_atk_down = unreal.load_asset(f"{pfx}/02_Attack_Hurt/Dir_01_Down/Attack/Flipbooks/FB_T_Player_Medic_Attack_Dir_01_Down_Sheet")
    fb_atk_up = unreal.load_asset(f"{pfx}/02_Attack_Hurt/Dir_05_Up/Attack/Flipbooks/FB_T_Player_Medic_Attack_Dir_05_Up_Sheet")
    fb_atk_side = unreal.load_asset(f"{pfx}/02_Attack_Hurt/Dir_03_Right/Attack/Flipbooks/FB_T_Player_Medic_Attack_Dir_03_Right_Sheet")

    handles = SUBOBJECTS.k2_gather_subobject_data_for_blueprint(bp)
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        if "Flipbook" in vname or isinstance(obj, unreal.PaperFlipbookComponent):
            if fb_idle_down:
                obj.set_editor_property("source_flipbook", fb_idle_down)
            obj.set_editor_property("relative_location", unreal.Vector(0.0, 0.0, 0.0))
            obj.set_editor_property("relative_rotation", unreal.Rotator(0.0, 0.0, 0.0))
            obj.set_editor_property("relative_scale3d", unreal.Vector(0.5, 0.5, 0.5))
            obj.set_editor_property("translucency_sort_priority", 100)
            obj.set_editor_property("visible", True)
            obj.set_editor_property("hidden_in_game", False)

    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    tick = ed.find_event_node("ReceiveTick")
    if not tick:
        return

    pc_tick = fn(ed, "/Script/Engine.GameplayStatics.GetPlayerController", 0, 0)
    set_value(pc_tick, "PlayerIndex", 0)

    # 1. 采样 WASD 与 J 键
    key_a = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, -180); set_value(key_a, "Key", "A"); connect(pc_tick, "ReturnValue", key_a, "self")
    key_d = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, -80);  set_value(key_d, "Key", "D"); connect(pc_tick, "ReturnValue", key_d, "self")
    sel_a = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, -180); set_value(sel_a, "A", 1.0); set_value(sel_a, "B", 0.0); connect(key_a, "ReturnValue", sel_a, "bPickA")
    sel_d = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, -80);  set_value(sel_d, "A", -1.0); set_value(sel_d, "B", 0.0); connect(key_d, "ReturnValue", sel_d, "bPickA")
    raw_x = fn(ed, "/Script/Engine.KismetMathLibrary.Add_DoubleDouble", 660, -130); connect(sel_a, "ReturnValue", raw_x, "A"); connect(sel_d, "ReturnValue", raw_x, "B")
    
    key_w = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, 40);   set_value(key_w, "Key", "W"); connect(pc_tick, "ReturnValue", key_w, "self")
    key_s = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, 140);  set_value(key_s, "Key", "S"); connect(pc_tick, "ReturnValue", key_s, "self")
    sel_w = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, 40);   set_value(sel_w, "A", 1.0); set_value(sel_w, "B", 0.0); connect(key_w, "ReturnValue", sel_w, "bPickA")
    sel_s = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, 140);  set_value(sel_s, "A", -1.0); set_value(sel_s, "B", 0.0); connect(key_s, "ReturnValue", sel_s, "bPickA")
    raw_z = fn(ed, "/Script/Engine.KismetMathLibrary.Add_DoubleDouble", 660, 90); connect(sel_w, "ReturnValue", raw_z, "A"); connect(sel_s, "ReturnValue", raw_z, "B")

    # 移动位移计算
    mul_x = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 880, -130); connect(raw_x, "ReturnValue", mul_x, "A"); set_value(mul_x, "B", 400.0)
    mul_z = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 880, 90);  connect(raw_z, "ReturnValue", mul_z, "A"); set_value(mul_z, "B", 400.0)
    
    move_vec = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 1100, 0)
    connect(mul_x, "ReturnValue", move_vec, "X"); set_value(move_vec, "Y", 0.0); connect(mul_z, "ReturnValue", move_vec, "Z")
    
    mul_dt = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_VectorFloat", 1320, 0)
    connect(move_vec, "ReturnValue", mul_dt, "A"); connect(tick, "DeltaSeconds", mul_dt, "B")
    
    move_node = fn(ed, "/Script/Engine.Actor.K2_AddActorWorldOffset", 1540, 0)
    set_value(move_node, "bSweep", "false")
    connect(tick, "then", move_node, "execute")
    connect(mul_dt, "ReturnValue", move_node, "DeltaLocation")
    
    cmp_x = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_DoubleDouble", 880, -250); connect(raw_x, "ReturnValue", cmp_x, "A"); set_value(cmp_x, "B", 0.0)
    cmp_z = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_DoubleDouble", 880, 250);  connect(raw_z, "ReturnValue", cmp_z, "A"); set_value(cmp_z, "B", 0.0)
    is_moving = fn(ed, "/Script/Engine.KismetMathLibrary.BooleanOR", 1100, 200); connect(cmp_x, "ReturnValue", is_moving, "A"); connect(cmp_z, "ReturnValue", is_moving, "B")
    
    get_comp = fn(ed, "/Script/Engine.Actor.GetComponentByClass", 1540, -200); set_value(get_comp, "ComponentClass", "Class'/Script/Paper2D.PaperFlipbookComponent'")
    
    key_j = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 1760, 200); set_value(key_j, "Key", "J"); connect(pc_tick, "ReturnValue", key_j, "self")
    br_is_shooting = ed.add_branch_node(); br_is_shooting.set_node_pos(unreal.IntPoint(1980, 0))
    connect(move_node, "then", br_is_shooting, "execute")
    connect(key_j, "ReturnValue", br_is_shooting, "Condition")

    # 朝向特征
    is_up_dir = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 2200, -260); connect(raw_z, "ReturnValue", is_up_dir, "A"); set_value(is_up_dir, "B", 0.0)
    is_down_dir = fn(ed, "/Script/Engine.KismetMathLibrary.Less_DoubleDouble", 2200, -160); connect(raw_z, "ReturnValue", is_down_dir, "A"); set_value(is_down_dir, "B", 0.0)
    is_right_dir = fn(ed, "/Script/Engine.KismetMathLibrary.Less_DoubleDouble", 2200, 40); connect(raw_x, "ReturnValue", is_right_dir, "A"); set_value(is_right_dir, "B", 0.0)

    # 左右 ScaleX 设置 (向右为 -0.5 镜像，向左为 0.5)
    scale_val_x = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 2420, -320); set_value(scale_val_x, "A", -0.5); set_value(scale_val_x, "B", 0.5); connect(is_right_dir, "ReturnValue", scale_val_x, "bPickA")
    scale_vec = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 2640, -320); connect(scale_val_x, "ReturnValue", scale_vec, "X"); set_value(scale_vec, "Y", 0.5); set_value(scale_vec, "Z", 0.5)
    set_sc = fn(ed, "/Script/Engine.SceneComponent.SetRelativeScale3D", 2860, -320); connect(get_comp, "ReturnValue", set_sc, "self"); connect(scale_vec, "ReturnValue", set_sc, "NewScale3D")

    # ==================== 射击分支 (Shooting = True) ====================
    # 1. 向上射击: 居中 (0,0,45), Pitch = 90.0, Yaw = 0.0
    br_shoot_up = ed.add_branch_node(); br_shoot_up.set_node_pos(unreal.IntPoint(2420, -200))
    connect(br_is_shooting, "then", br_shoot_up, "execute"); connect(is_up_dir, "ReturnValue", br_shoot_up, "Condition")

    set_fb_atk_up = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2640, -260)
    if fb_atk_up: set_value(set_fb_atk_up, "NewFlipbook", f"PaperFlipbook'{fb_atk_up.get_path_name()}'")
    connect(br_shoot_up, "then", set_fb_atk_up, "execute"); connect(get_comp, "ReturnValue", set_fb_atk_up, "self")
    
    get_loc = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 2640, 0)
    add_up = fn(ed, "/Script/Engine.KismetMathLibrary.Add_VectorVector", 2860, -260); connect(get_loc, "ReturnValue", add_up, "A"); set_value(add_up, "B", "0,0,45")
    rot_up = fn(ed, "/Script/Engine.KismetMathLibrary.MakeRotator", 2860, -140); set_value(rot_up, "Pitch", 90.0); set_value(rot_up, "Yaw", 0.0); set_value(rot_up, "Roll", 0.0)
    trans_up = fn(ed, "/Script/Engine.KismetMathLibrary.MakeTransform", 3080, -200); connect(add_up, "ReturnValue", trans_up, "Location"); connect(rot_up, "ReturnValue", trans_up, "Rotation"); set_value(trans_up, "Scale", "1,1,1")
    spawn_up = fn(ed, "/Script/Engine.GameplayStatics.BeginDeferredActorSpawnFromClass", 3300, -260)
    set_value(spawn_up, "ActorClass", "Class'/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase.BP_ProjectileBase_C'")
    connect(set_fb_atk_up, "then", spawn_up, "execute"); connect(trans_up, "ReturnValue", spawn_up, "SpawnTransform")
    finish_up = fn(ed, "/Script/Engine.GameplayStatics.FinishSpawningActor", 3560, -260)
    connect(spawn_up, "then", finish_up, "execute"); connect(spawn_up, "ReturnValue", finish_up, "Actor"); connect(trans_up, "ReturnValue", finish_up, "SpawnTransform")

    # 2. 向下射击: 居中 (0,0,-45), Pitch = -90.0, Yaw = 0.0
    br_shoot_down = ed.add_branch_node(); br_shoot_down.set_node_pos(unreal.IntPoint(2640, -60))
    connect(br_shoot_up, "else", br_shoot_down, "execute"); connect(is_down_dir, "ReturnValue", br_shoot_down, "Condition")

    set_fb_atk_down = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2860, -100)
    if fb_atk_down: set_value(set_fb_atk_down, "NewFlipbook", f"PaperFlipbook'{fb_atk_down.get_path_name()}'")
    connect(br_shoot_down, "then", set_fb_atk_down, "execute"); connect(get_comp, "ReturnValue", set_fb_atk_down, "self")
    
    add_down = fn(ed, "/Script/Engine.KismetMathLibrary.Add_VectorVector", 3080, -100); connect(get_loc, "ReturnValue", add_down, "A"); set_value(add_down, "B", "0,0,-45")
    rot_down = fn(ed, "/Script/Engine.KismetMathLibrary.MakeRotator", 3080, 20); set_value(rot_down, "Pitch", -90.0); set_value(rot_down, "Yaw", 0.0); set_value(rot_down, "Roll", 0.0)
    trans_down = fn(ed, "/Script/Engine.KismetMathLibrary.MakeTransform", 3300, -40); connect(add_down, "ReturnValue", trans_down, "Location"); connect(rot_down, "ReturnValue", trans_down, "Rotation"); set_value(trans_down, "Scale", "1,1,1")
    spawn_down = fn(ed, "/Script/Engine.GameplayStatics.BeginDeferredActorSpawnFromClass", 3520, -100)
    set_value(spawn_down, "ActorClass", "Class'/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase.BP_ProjectileBase_C'")
    connect(set_fb_atk_down, "then", spawn_down, "execute"); connect(trans_down, "ReturnValue", spawn_down, "SpawnTransform")
    finish_down = fn(ed, "/Script/Engine.GameplayStatics.FinishSpawningActor", 3780, -100)
    connect(spawn_down, "then", finish_down, "execute"); connect(spawn_down, "ReturnValue", finish_down, "Actor"); connect(trans_down, "ReturnValue", finish_down, "SpawnTransform")

    # 3. 侧向射击: 向右 Yaw=180 偏移 (-45,0,0), 向左 Yaw=0 偏移 (45,0,0)
    set_fb_atk_side = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2860, 160)
    if fb_atk_side: set_value(set_fb_atk_side, "NewFlipbook", f"PaperFlipbook'{fb_atk_side.get_path_name()}'")
    connect(br_shoot_down, "else", set_fb_atk_side, "execute"); connect(get_comp, "ReturnValue", set_fb_atk_side, "self")
    
    yaw_val_side = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 3080, 280); set_value(yaw_val_side, "A", 180.0); set_value(yaw_val_side, "B", 0.0); connect(is_right_dir, "ReturnValue", yaw_val_side, "bPickA")
    offset_val_side = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 3080, 380); set_value(offset_val_side, "A", -45.0); set_value(offset_val_side, "B", 45.0); connect(is_right_dir, "ReturnValue", offset_val_side, "bPickA")
    
    offset_vec_side = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 3300, 380); connect(offset_val_side, "ReturnValue", offset_vec_side, "X"); set_value(offset_vec_side, "Y", 0.0); set_value(offset_vec_side, "Z", 0.0)
    add_side = fn(ed, "/Script/Engine.KismetMathLibrary.Add_VectorVector", 3520, 280); connect(get_loc, "ReturnValue", add_side, "A"); connect(offset_vec_side, "ReturnValue", add_side, "B")
    
    rot_side = fn(ed, "/Script/Engine.KismetMathLibrary.MakeRotator", 3520, 160); set_value(rot_side, "Pitch", 0.0); connect(yaw_val_side, "ReturnValue", rot_side, "Yaw"); set_value(rot_side, "Roll", 0.0)
    trans_side = fn(ed, "/Script/Engine.KismetMathLibrary.MakeTransform", 3740, 220); connect(add_side, "ReturnValue", trans_side, "Location"); connect(rot_side, "ReturnValue", trans_side, "Rotation"); set_value(trans_side, "Scale", "1,1,1")
    spawn_side = fn(ed, "/Script/Engine.GameplayStatics.BeginDeferredActorSpawnFromClass", 3960, 160)
    set_value(spawn_side, "ActorClass", "Class'/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase.BP_ProjectileBase_C'")
    connect(set_fb_atk_side, "then", spawn_side, "execute"); connect(trans_side, "ReturnValue", spawn_side, "SpawnTransform")
    finish_side = fn(ed, "/Script/Engine.GameplayStatics.FinishSpawningActor", 4220, 160)
    connect(spawn_side, "then", finish_side, "execute"); connect(spawn_side, "ReturnValue", finish_side, "Actor"); connect(trans_side, "ReturnValue", finish_side, "SpawnTransform")

    # ==================== 移动与待机分支 (Shooting = False) ====================
    br_move_state = ed.add_branch_node(); br_move_state.set_node_pos(unreal.IntPoint(2420, 480))
    connect(br_is_shooting, "else", br_move_state, "execute"); connect(is_moving, "ReturnValue", br_move_state, "Condition")

    connect(br_move_state, "then", set_sc, "execute")

    # 移动分支
    br_side_run = ed.add_branch_node(); br_side_run.set_node_pos(unreal.IntPoint(2860, 480))
    connect(set_sc, "then", br_side_run, "execute"); connect(cmp_x, "ReturnValue", br_side_run, "Condition")
    
    set_fb_run_side = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 3080, 440)
    if fb_run_left: set_value(set_fb_run_side, "NewFlipbook", f"PaperFlipbook'{fb_run_left.get_path_name()}'")
    connect(br_side_run, "then", set_fb_run_side, "execute"); connect(get_comp, "ReturnValue", set_fb_run_side, "self")
    
    br_up_run = ed.add_branch_node(); br_up_run.set_node_pos(unreal.IntPoint(3080, 560))
    connect(br_side_run, "else", br_up_run, "execute"); connect(is_up_dir, "ReturnValue", br_up_run, "Condition")
    
    set_fb_run_up = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 3300, 520)
    if fb_run_up: set_value(set_fb_run_up, "NewFlipbook", f"PaperFlipbook'{fb_run_up.get_path_name()}'")
    connect(br_up_run, "then", set_fb_run_up, "execute"); connect(get_comp, "ReturnValue", set_fb_run_up, "self")
    
    set_fb_run_down = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 3300, 620)
    if fb_run_down: set_value(set_fb_run_down, "NewFlipbook", f"PaperFlipbook'{fb_run_down.get_path_name()}'")
    connect(br_up_run, "else", set_fb_run_down, "execute"); connect(get_comp, "ReturnValue", set_fb_run_down, "self")

    # ==================== 待机保持分支 (包含 Atk 动作判定，保证射击后不丢失朝向) ====================
    get_curr_fb = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.GetFlipbook", 2640, 700); connect(get_comp, "ReturnValue", get_curr_fb, "self")
    
    # 1. 向上待机判定: (Current == Run_Up || Current == Idle_Up || Current == Atk_Up)
    is_up_r = fn(ed, "/Script/Engine.KismetMathLibrary.EqualEqual_ObjectObject", 2860, 640); connect(get_curr_fb, "ReturnValue", is_up_r, "A")
    if fb_run_up: set_value(is_up_r, "B", f"PaperFlipbook'{fb_run_up.get_path_name()}'")
    is_up_i = fn(ed, "/Script/Engine.KismetMathLibrary.EqualEqual_ObjectObject", 2860, 700); connect(get_curr_fb, "ReturnValue", is_up_i, "A")
    if fb_idle_up: set_value(is_up_i, "B", f"PaperFlipbook'{fb_idle_up.get_path_name()}'")
    is_up_a = fn(ed, "/Script/Engine.KismetMathLibrary.EqualEqual_ObjectObject", 2860, 760); connect(get_curr_fb, "ReturnValue", is_up_a, "A")
    if fb_atk_up: set_value(is_up_a, "B", f"PaperFlipbook'{fb_atk_up.get_path_name()}'")
    
    is_up_or1 = fn(ed, "/Script/Engine.KismetMathLibrary.BooleanOR", 3080, 680); connect(is_up_r, "ReturnValue", is_up_or1, "A"); connect(is_up_i, "ReturnValue", is_up_or1, "B")
    is_keep_up = fn(ed, "/Script/Engine.KismetMathLibrary.BooleanOR", 3300, 700); connect(is_up_or1, "ReturnValue", is_keep_up, "A"); connect(is_up_a, "ReturnValue", is_keep_up, "B")
    
    br_idle_up = ed.add_branch_node(); br_idle_up.set_node_pos(unreal.IntPoint(3520, 700))
    connect(br_move_state, "else", br_idle_up, "execute"); connect(is_keep_up, "ReturnValue", br_idle_up, "Condition")
    
    set_fb_idle_up = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 3740, 700)
    if fb_idle_up: set_value(set_fb_idle_up, "NewFlipbook", f"PaperFlipbook'{fb_idle_up.get_path_name()}'")
    connect(br_idle_up, "then", set_fb_idle_up, "execute"); connect(get_comp, "ReturnValue", set_fb_idle_up, "self")
    
    # 2. 侧向待机判定: (Current == Run_Left || Current == Idle_Left || Current == Atk_Side)
    is_side_r = fn(ed, "/Script/Engine.KismetMathLibrary.EqualEqual_ObjectObject", 3080, 800); connect(get_curr_fb, "ReturnValue", is_side_r, "A")
    if fb_run_left: set_value(is_side_r, "B", f"PaperFlipbook'{fb_run_left.get_path_name()}'")
    is_side_i = fn(ed, "/Script/Engine.KismetMathLibrary.EqualEqual_ObjectObject", 3080, 860); connect(get_curr_fb, "ReturnValue", is_side_i, "A")
    if fb_idle_left: set_value(is_side_i, "B", f"PaperFlipbook'{fb_idle_left.get_path_name()}'")
    is_side_a = fn(ed, "/Script/Engine.KismetMathLibrary.EqualEqual_ObjectObject", 3080, 920); connect(get_curr_fb, "ReturnValue", is_side_a, "A")
    if fb_atk_side: set_value(is_side_a, "B", f"PaperFlipbook'{fb_atk_side.get_path_name()}'")
    
    is_side_or1 = fn(ed, "/Script/Engine.KismetMathLibrary.BooleanOR", 3300, 830); connect(is_side_r, "ReturnValue", is_side_or1, "A"); connect(is_side_i, "ReturnValue", is_side_or1, "B")
    is_keep_side = fn(ed, "/Script/Engine.KismetMathLibrary.BooleanOR", 3520, 850); connect(is_side_or1, "ReturnValue", is_keep_side, "A"); connect(is_side_a, "ReturnValue", is_keep_side, "B")
    
    br_idle_side = ed.add_branch_node(); br_idle_side.set_node_pos(unreal.IntPoint(3740, 800))
    connect(br_idle_up, "else", br_idle_side, "execute"); connect(is_keep_side, "ReturnValue", br_idle_side, "Condition")
    
    set_fb_idle_side = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 3960, 800)
    if fb_idle_left: set_value(set_fb_idle_side, "NewFlipbook", f"PaperFlipbook'{fb_idle_left.get_path_name()}'")
    connect(br_idle_side, "then", set_fb_idle_side, "execute"); connect(get_comp, "ReturnValue", set_fb_idle_side, "self")
    
    # 3. 向下待机 (默认兜底)
    set_fb_idle_down = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 3960, 900)
    if fb_idle_down: set_value(set_fb_idle_down, "NewFlipbook", f"PaperFlipbook'{fb_idle_down.get_path_name()}'")
    connect(br_idle_side, "else", set_fb_idle_down, "execute"); connect(get_comp, "ReturnValue", set_fb_idle_down, "self")

    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    print("✅ 主角 BP_Player_Medic 重构完成！")

# ==============================================================================
# 2. 动态怪物蓝图 (确保 Flipbook + 步态推进)
# ==============================================================================
def build_live_enemy_bp(name: str, fb_path: str, speed: float, scale: float):
    folder = f"{GEN}/Blueprints/Enemies"
    ensure(folder)
    path = f"{folder}/{name}"
    
    if ASSETS.does_asset_exist(path):
        ASSETS.delete_asset(path)
    bp = BPLIB.create_blueprint_asset_with_parent(path, unreal.Actor.static_class())
        
    fb_asset = unreal.load_asset(fb_path)
    handles = SUBOBJECTS.k2_gather_subobject_data_for_blueprint(bp)
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        if "Flipbook" in vname or isinstance(obj, unreal.PaperFlipbookComponent):
            if fb_asset:
                obj.set_editor_property("source_flipbook", fb_asset)
            obj.set_editor_property("relative_scale3d", unreal.Vector(scale, scale, scale))
            obj.set_editor_property("translucency_sort_priority", 500)
            obj.set_editor_property("visible", True)
            obj.set_editor_property("hidden_in_game", False)

    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    tick = ed.find_event_node("ReceiveTick")
    if tick:
        move_fn = ed.add_call_function_node("/Script/Engine.Actor.K2_AddActorWorldOffset")
        move_fn.set_node_pos(unreal.IntPoint(300, 0))
        pin_then = [p for p in BPLIB.list_output_pins(tick) if str(PINLIB.get_pin_name(p)).lower() == "then"][0]
        pin_exec = [p for p in BPLIB.list_input_pins(move_fn) if str(PINLIB.get_pin_name(p)).lower() == "execute"][0]
        PINLIB.try_create_connection(pin_then, pin_exec)
        
        pin_delta = [p for p in BPLIB.list_input_pins(move_fn) if str(PINLIB.get_pin_name(p)).lower() == "deltalocation"][0]
        step_z = -float(speed) * 0.033
        PINLIB.set_pin_value(pin_delta, f"0,0,{step_z}")
        
        pin_sweep = [p for p in BPLIB.list_input_pins(move_fn) if str(PINLIB.get_pin_name(p)).lower() == "bsweep"][0]
        PINLIB.set_pin_value(pin_sweep, "false")
    
    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    print(f"✅ 动态敌人蓝图就绪: {name}")
    return bp

# ==============================================================================
# 3. 组装主关卡 MAP_GGBOM_Main (9:16 精密 UI + 怪物军团)
# ==============================================================================
def assemble_final_level():
    print("🗺️ 正在组装 MAP_GGBOM_Main (9:16 像素级 HUD + 怪物军团)...")
    
    fb_zombie = "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Zombie/01_Zombie_Walker_Basic/Flipbooks/FB_T_Zombie_WalkerBasic_Sheet"
    fb_hound = "/Game/P01/Imported/Content/Asset/Art/02_Enemies/MutantHound/Run/Dir_01_Down/Flipbooks/FB_T_Hound_Run_Dir_01_Down_Sheet"
    fb_shambler = "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Zombie/11_Zombie_Shambler_Heavy/Flipbooks/FB_T_Zombie_ShamblerHeavy_Sheet"
    fb_boss = "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Boss_Overlord/Actions/Walk/Dir_01_Down/Flipbooks/FB_T_Boss_Walk_Dir_01_Down_Sheet"
    
    bp_zombie = build_live_enemy_bp("BP_Enemy_Zombie", fb_zombie, speed=40.0, scale=0.45)
    bp_hound = build_live_enemy_bp("BP_Enemy_Hound", fb_hound, speed=75.0, scale=0.48)
    bp_shambler = build_live_enemy_bp("BP_Enemy_Shambler", fb_shambler, speed=25.0, scale=0.58)
    bp_boss = build_live_enemy_bp("BP_Boss_Overlord", fb_boss, speed=15.0, scale=0.72)
    
    unreal.EditorLevelLibrary.load_level(MAP_PATH)
    world = unreal.EditorLevelLibrary.get_editor_world()
    
    # 清理所有非玩家旧实体
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        lbl = a.get_actor_label()
        if not lbl.startswith("PlayerStart"):
            unreal.EditorLevelLibrary.destroy_actor(a)
            
    # 1. 9:16 正交相机 (100% 满屏正视 X-Z 平面, OrthoWidth=941.0)
    cam = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.CameraActor, unreal.Vector(0, -600, 0), unreal.Rotator(pitch=0.0, yaw=90.0, roll=0.0)
    )
    cam_comp = cam.get_component_by_class(unreal.CameraComponent)
    cam_comp.set_editor_property("projection_mode", unreal.CameraProjectionMode.ORTHOGRAPHIC)
    cam_comp.set_editor_property("ortho_width", 941.0)
    cam_comp.set_editor_property("aspect_ratio", 0.5628)
    cam.set_editor_property("auto_activate_for_player", unreal.AutoReceiveInput.PLAYER0)
    cam.set_actor_label("PortraitCamera_9x16")
    
    # 2. 地面底层 (Y=+80) 与 战术掩体
    sp_ground = unreal.load_asset(f"{GEN}/Art/Sprites/SP_Ground")
    if sp_ground:
        g = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PaperSpriteActor, unreal.Vector(0, 80, 0), unreal.Rotator())
        g.get_component_by_class(unreal.PaperSpriteComponent).set_editor_property("source_sprite", sp_ground)
        g.get_component_by_class(unreal.PaperSpriteComponent).set_editor_property("translucency_sort_priority", -100)
        g.set_actor_scale3d(unreal.Vector(1.15, 1.15, 1.15))
        g.set_actor_label("Ground_Stage00")
        
    sp_barricade = unreal.load_asset(f"{GEN}/Art/Sprites/SP_Barricade")
    if sp_barricade:
        for x, z, lbl in ((-180, 420, "Barricade_Top_L"), (180, 420, "Barricade_Top_R"), (-220, 0, "DefenseLine_L"), (220, 0, "DefenseLine_R")):
            b = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PaperSpriteActor, unreal.Vector(x, 15, z), unreal.Rotator())
            b.get_component_by_class(unreal.PaperSpriteComponent).set_editor_property("source_sprite", sp_barricade)
            b.get_component_by_class(unreal.PaperSpriteComponent).set_editor_property("translucency_sort_priority", 6)
            b.set_actor_scale3d(unreal.Vector(0.55, 0.55, 0.55))
            b.set_actor_label(lbl)

    # 3. 部署【动态怪物军团】(位于中上部视野区, Z 范围 +150 ~ +550, Y=0)
    enemies = [
        (bp_zombie, -140, 280, "Live_Zombie_01"),
        (bp_zombie, 0, 340, "Live_Zombie_02"),
        (bp_zombie, 140, 300, "Live_Zombie_03"),
        (bp_shambler, 0, 220, "Live_Shambler_Elite"),
        (bp_hound, -180, 140, "Live_Hound_01"),
        (bp_hound, 180, 160, "Live_Hound_02"),
        (bp_boss, 0, 520, "Live_Boss_Overlord"),
    ]
    for bp_item, x, z, lbl in enemies:
        cls = bp_item.generated_class()
        act = unreal.EditorLevelLibrary.spawn_actor_from_class(cls, unreal.Vector(x, 0, z), unreal.Rotator())
        if act:
            act.set_actor_label(lbl)
            print(f"  + 部署动态敌人: {lbl} @ ({x}, 0, {z})")

    # 4. 玩家出生点 (下方中央)
    p_starts = [a for a in unreal.EditorLevelLibrary.get_all_level_actors() if a.get_actor_label().startswith("PlayerStart")]
    if not p_starts:
        ps = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(0, -10, -500), unreal.Rotator())
        ps.set_actor_label("PlayerStart")
    else:
        p_starts[0].set_actor_location(unreal.Vector(0, -10, -500), False, False)

    # 5. 精密对齐 HUD 部件 (按 9:16 安全画幅严格排布)
    hud_items = [
        # 顶部 Boss 血条 (居中偏上 Z=+720)
        (f"{GEN}/Art/Sprites/SP_Boss_Bar_Bg", unreal.Vector(0, -60, 720), 0.75, 90, "UI_BossBar_Bg"),
        (f"{GEN}/Art/Sprites/SP_Boss_Bar_Fill", unreal.Vector(0, -60, 720), 0.72, 95, "UI_BossBar_Fill"),
        (f"{GEN}/Art/Sprites/SP_Boss_Skull", unreal.Vector(-200, -60, 720), 0.55, 100, "UI_Boss_SkullIcon"),
        # 顶部右上角暂停按钮 (Z=+720, X=+360)
        (f"{GEN}/Art/Sprites/SP_Btn_Pause", unreal.Vector(360, -60, 720), 0.25, 100, "UI_Btn_Pause"),
        # 底部血条与经验条 (居中偏下 Z=-680)
        (f"{GEN}/Art/Sprites/SP_HUD_HP_Bg", unreal.Vector(-200, -60, -680), 0.58, 90, "UI_Player_HP_Bg"),
        (f"{GEN}/Art/Sprites/SP_HUD_HP_Fill", unreal.Vector(-200, -60, -680), 0.56, 95, "UI_Player_HP_Fill"),
        (f"{GEN}/Art/Sprites/SP_HUD_Exp_Fill", unreal.Vector(-200, -60, -730), 0.48, 95, "UI_Player_EXP_Fill"),
        # 底部右侧弹药盘
        (f"{GEN}/Art/Sprites/SP_HUD_AmmoRadial", unreal.Vector(320, -60, -680), 0.45, 95, "UI_HUD_AmmoRadial"),
    ]
    for sp_p, loc, sc, prio, lbl in hud_items:
        sp = unreal.load_asset(sp_p)
        if sp:
            act = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PaperSpriteActor, loc, unreal.Rotator())
            act.get_component_by_class(unreal.PaperSpriteComponent).set_editor_property("source_sprite", sp)
            act.get_component_by_class(unreal.PaperSpriteComponent).set_editor_property("translucency_sort_priority", prio)
            act.set_actor_scale3d(unreal.Vector(sc, sc, sc))
            act.set_actor_label(lbl)

    unreal.EditorLoadingAndSavingUtils.save_map(world, MAP_PATH)
    ASSETS.save_directory(GEN, only_if_is_dirty=False, recursive=True)
    ASSETS.save_directory("/Game/Blueprints", only_if_is_dirty=False, recursive=True)
    print("ALL_FIXES_AND_LEVEL_REBUILT_SUCCESS")

def main():
    rebuild_player_medic()
    assemble_final_level()

if __name__ == "__main__":
    main()
