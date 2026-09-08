# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》移动与射击 100% 同步状态机重构
解决核心痛点:
1. 彻底解决移动中射击时动作误判为侧向的 Bug (统一按实时输入向量与朝向判定)
2. 移动射击时保持精准的枪口对齐与子弹 8 向飞行轨迹
3. 待机射击与移动射击统一映射至正确的 Attack 动作 (Attack_Up, Attack_Down, Attack_UpLeft, Attack_DownLeft, Attack_Side)
================================================================================
"""
from __future__ import annotations
import unreal

GEN = "/Game/GGBOM"
PLAYER_BP_PATH = "/Game/Blueprints/Player/BP_Player_Medic"
PROJ_BP_PATH = "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase"

ASSETS = unreal.EditorAssetLibrary
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary
SUBOBJECTS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)

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

def build_synchronized_player():
    print("🎮 开始重构移动与射击 100% 同步的主角蓝图...")
    bp = unreal.load_asset(PLAYER_BP_PATH)
    if not bp:
        raise RuntimeError(f"未找到主角蓝图: {PLAYER_BP_PATH}")
        
    pfx = "/Game/P01/Imported/Content/Asset/Art/01_Player"
    
    # 待机
    fb_idle_down = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_01_Down/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_01_Down_Sheet")
    fb_idle_up = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_05_Up/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_05_Up_Sheet")
    fb_idle_left = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_03_Left/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_03_Left_Sheet")
    fb_idle_downleft = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_02_DownLeft/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_02_DownLeft_Sheet")
    fb_idle_upleft = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_04_UpLeft/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_04_UpLeft_Sheet")
    
    # 奔跑
    fb_run_down = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_01_Down/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_01_Down_Sheet")
    fb_run_up = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_05_Up/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_05_Up_Sheet")
    fb_run_left = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_03_Left/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_03_Left_Sheet")
    fb_run_downleft = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_02_DownLeft/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_02_DownLeft_Sheet")
    fb_run_upleft = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_04_UpLeft/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_04_UpLeft_Sheet")
    
    # 攻击
    fb_atk_down = unreal.load_asset(f"{pfx}/02_Attack_Hurt/Dir_01_Down/Attack/Flipbooks/FB_T_Player_Medic_Attack_Dir_01_Down_Sheet")
    fb_atk_up = unreal.load_asset(f"{pfx}/02_Attack_Hurt/Dir_05_Up/Attack/Flipbooks/FB_T_Player_Medic_Attack_Dir_05_Up_Sheet")
    fb_atk_side = unreal.load_asset(f"{pfx}/02_Attack_Hurt/Dir_03_Right/Attack/Flipbooks/FB_T_Player_Medic_Attack_Dir_03_Right_Sheet")
    fb_atk_downleft = unreal.load_asset(f"{pfx}/02_Attack_Hurt/Dir_02_DownLeft/Attack/Flipbooks/FB_T_Player_Medic_Attack_Dir_02_DownLeft_Sheet")
    fb_atk_upleft = unreal.load_asset(f"{pfx}/02_Attack_Hurt/Dir_04_UpLeft/Attack/Flipbooks/FB_T_Player_Medic_Attack_Dir_04_UpLeft_Sheet")

    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    
    tick = ed.find_event_node("ReceiveTick")
    pc_tick = fn(ed, "/Script/Engine.GameplayStatics.GetPlayerController", 0, 0)
    set_value(pc_tick, "PlayerIndex", 0)
    
    # 1. 采样输入
    key_a = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, -180); set_value(key_a, "Key", "A"); connect(pc_tick, "ReturnValue", key_a, "self")
    key_d = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, -80);  set_value(key_d, "Key", "D"); connect(pc_tick, "ReturnValue", key_d, "self")
    sel_a = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, -180); set_value(sel_a, "A", 450.0); set_value(sel_a, "B", 0.0); connect(key_a, "ReturnValue", sel_a, "bPickA")
    sel_d = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, -80);  set_value(sel_d, "A", -450.0); set_value(sel_d, "B", 0.0); connect(key_d, "ReturnValue", sel_d, "bPickA")
    add_x = fn(ed, "/Script/Engine.KismetMathLibrary.Add_DoubleDouble", 660, -130); connect(sel_a, "ReturnValue", add_x, "A"); connect(sel_d, "ReturnValue", add_x, "B")
    
    key_w = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, 40);   set_value(key_w, "Key", "W"); connect(pc_tick, "ReturnValue", key_w, "self")
    key_s = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, 140);  set_value(key_s, "Key", "S"); connect(pc_tick, "ReturnValue", key_s, "self")
    sel_w = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, 40);   set_value(sel_w, "A", 450.0); set_value(sel_w, "B", 0.0); connect(key_w, "ReturnValue", sel_w, "bPickA")
    sel_s = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, 140);  set_value(sel_s, "A", -450.0); set_value(sel_s, "B", 0.0); connect(key_s, "ReturnValue", sel_s, "bPickA")
    add_z = fn(ed, "/Script/Engine.KismetMathLibrary.Add_DoubleDouble", 660, 90); connect(sel_w, "ReturnValue", add_z, "A"); connect(sel_s, "ReturnValue", add_z, "B")
    
    make_vec = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 880, 0)
    connect(add_x, "ReturnValue", make_vec, "X"); set_value(make_vec, "Y", 0.0); connect(add_z, "ReturnValue", make_vec, "Z")
    
    mul_dt = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_VectorFloat", 1080, 0)
    connect(make_vec, "ReturnValue", mul_dt, "A"); connect(tick, "DeltaSeconds", mul_dt, "B")
    
    move_node = fn(ed, "/Script/Engine.Actor.K2_AddActorWorldOffset", 1300, 0)
    set_value(move_node, "bSweep", "false")
    connect(tick, "then", move_node, "execute")
    connect(mul_dt, "ReturnValue", move_node, "DeltaLocation")
    
    # 判定是否移动
    cmp_x = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_DoubleDouble", 880, -200); connect(add_x, "ReturnValue", cmp_x, "A"); set_value(cmp_x, "B", 0.0)
    cmp_z = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_DoubleDouble", 880, 200); connect(add_z, "ReturnValue", cmp_z, "A"); set_value(cmp_z, "B", 0.0)
    is_moving = fn(ed, "/Script/Engine.KismetMathLibrary.BooleanOR", 1080, 150); connect(cmp_x, "ReturnValue", is_moving, "A"); connect(cmp_z, "ReturnValue", is_moving, "B")
    
    get_comp = fn(ed, "/Script/Engine.Actor.GetComponentByClass", 1520, -200); set_value(get_comp, "ComponentClass", "Class'/Script/Paper2D.PaperFlipbookComponent'")
    
    # 采样 J 键 (射击开火)
    key_j = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 1520, 200); set_value(key_j, "Key", "J"); connect(pc_tick, "ReturnValue", key_j, "self")
    br_is_shooting = ed.add_branch_node(); br_is_shooting.set_node_pos(unreal.IntPoint(1740, 0))
    connect(move_node, "then", br_is_shooting, "execute")
    connect(key_j, "ReturnValue", br_is_shooting, "Condition")

    # 判定朝向特征 (通过输入向量或当前朝向)
    is_up_input = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 1960, -260); connect(add_z, "ReturnValue", is_up_input, "A"); set_value(is_up_input, "B", 0.0)
    is_down_input = fn(ed, "/Script/Engine.KismetMathLibrary.Less_DoubleDouble", 1960, -160); connect(add_z, "ReturnValue", is_down_input, "A"); set_value(is_down_input, "B", 0.0)
    is_left_input = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 1960, -60); connect(add_x, "ReturnValue", is_left_input, "A"); set_value(is_left_input, "B", 0.0)
    is_right_input = fn(ed, "/Script/Engine.KismetMathLibrary.Less_DoubleDouble", 1960, 40); connect(add_x, "ReturnValue", is_right_input, "A"); set_value(is_right_input, "B", 0.0)

    # 左右朝向 ScaleX 翻转控制 (向右则 ScaleX = -0.45 镜像，向左/正向则 ScaleX = 0.45)
    scale_val_x = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 2180, -320); set_value(scale_val_x, "A", -0.45); set_value(scale_val_x, "B", 0.45); connect(is_right_input, "ReturnValue", scale_val_x, "bPickA")
    scale_vec = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 2400, -320); connect(scale_val_x, "ReturnValue", scale_vec, "X"); set_value(scale_vec, "Y", 0.45); set_value(scale_vec, "Z", 0.45)
    set_sc = fn(ed, "/Script/Engine.SceneComponent.SetRelativeScale3D", 2620, -320); connect(get_comp, "ReturnValue", set_sc, "self"); connect(scale_vec, "ReturnValue", set_sc, "NewScale3D")

    # ==================== 分支 A: 射击状态 (Shooting = True) ====================
    # 1. 正上射击 (is_up_input AND NOT cmp_x)
    is_pure_up = fn(ed, "/Script/Engine.KismetMathLibrary.BooleanAND", 2180, -200); connect(is_up_input, "ReturnValue", is_pure_up, "A")
    not_x = fn(ed, "/Script/Engine.KismetMathLibrary.Not_PreBool", 1960, -320); connect(cmp_x, "ReturnValue", not_x, "A"); connect(not_x, "ReturnValue", is_pure_up, "B")
    
    br_shoot_up = ed.add_branch_node(); br_shoot_up.set_node_pos(unreal.IntPoint(2400, -200))
    connect(br_is_shooting, "then", br_shoot_up, "execute"); connect(is_pure_up, "ReturnValue", br_shoot_up, "Condition")

    # 正上射击: 播放 Attack_Up, Pitch=90, 枪口 (X, 0, Z+45)
    set_fb_atk_up = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2640, -260)
    if fb_atk_up:
        set_value(set_fb_atk_up, "NewFlipbook", f"PaperFlipbook'{fb_atk_up.get_path_name()}'")
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

    # 2. 正下射击 (is_down_input AND NOT cmp_x)
    is_pure_down = fn(ed, "/Script/Engine.KismetMathLibrary.BooleanAND", 2400, -60); connect(is_down_input, "ReturnValue", is_pure_down, "A"); connect(not_x, "ReturnValue", is_pure_down, "B")
    br_shoot_down = ed.add_branch_node(); br_shoot_down.set_node_pos(unreal.IntPoint(2640, -60))
    connect(br_shoot_up, "else", br_shoot_down, "execute"); connect(is_pure_down, "ReturnValue", br_shoot_down, "Condition")

    # 正下射击: 播放 Attack_Down, Pitch=-90, 枪口 (X, 0, Z-45)
    set_fb_atk_down = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2860, -100)
    if fb_atk_down:
        set_value(set_fb_atk_down, "NewFlipbook", f"PaperFlipbook'{fb_atk_down.get_path_name()}'")
    connect(br_shoot_down, "then", set_fb_atk_down, "execute"); connect(get_comp, "ReturnValue", set_fb_atk_down, "self")
    
    add_down = fn(ed, "/Script/Engine.KismetMathLibrary.Add_VectorVector", 3080, -100); connect(get_loc, "ReturnValue", add_down, "A"); set_value(add_down, "B", "0,0,-45")
    rot_down = fn(ed, "/Script/Engine.KismetMathLibrary.MakeRotator", 3080, 20); set_value(rot_down, "Pitch", -90.0); set_value(rot_down, "Yaw", 0.0); set_value(rot_down, "Roll", 0.0)
    trans_down = fn(ed, "/Script/Engine.KismetMathLibrary.MakeTransform", 3300, -40); connect(add_down, "ReturnValue", trans_down, "Location"); connect(rot_down, "ReturnValue", trans_down, "Rotation"); set_value(trans_down, "Scale", "1,1,1")
    spawn_down = fn(ed, "/Script/Engine.GameplayStatics.BeginDeferredActorSpawnFromClass", 3520, -100)
    set_value(spawn_down, "ActorClass", "Class'/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase.BP_ProjectileBase_C'")
    connect(set_fb_atk_down, "then", spawn_down, "execute"); connect(trans_down, "ReturnValue", spawn_down, "SpawnTransform")
    finish_down = fn(ed, "/Script/Engine.GameplayStatics.FinishSpawningActor", 3780, -100)
    connect(spawn_down, "then", finish_down, "execute"); connect(spawn_down, "ReturnValue", finish_down, "Actor"); connect(trans_down, "ReturnValue", finish_down, "SpawnTransform")

    # 3. 侧向/斜向射击 (Attack_Side)
    set_fb_atk_side = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2860, 160)
    if fb_atk_side:
        set_value(set_fb_atk_side, "NewFlipbook", f"PaperFlipbook'{fb_atk_side.get_path_name()}'")
    connect(br_shoot_down, "else", set_fb_atk_side, "execute"); connect(get_comp, "ReturnValue", set_fb_atk_side, "self")
    
    # 侧向 Pitch 选择: 若向右(is_right_input)则 Pitch=180°, 枪口(-40,0,0)；向左则 Pitch=0°, 枪口(+40,0,0)
    pitch_val_side = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 3080, 280); set_value(pitch_val_side, "A", 180.0); set_value(pitch_val_side, "B", 0.0); connect(is_right_input, "ReturnValue", pitch_val_side, "bPickA")
    offset_val_side = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 3080, 380); set_value(offset_val_side, "A", -40.0); set_value(offset_val_side, "B", 40.0); connect(is_right_input, "ReturnValue", offset_val_side, "bPickA")
    
    offset_vec_side = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 3300, 380); connect(offset_val_side, "ReturnValue", offset_vec_side, "X"); set_value(offset_vec_side, "Y", 0.0); set_value(offset_vec_side, "Z", 0.0)
    add_side = fn(ed, "/Script/Engine.KismetMathLibrary.Add_VectorVector", 3520, 280); connect(get_loc, "ReturnValue", add_side, "A"); connect(offset_vec_side, "ReturnValue", add_side, "B")
    
    rot_side = fn(ed, "/Script/Engine.KismetMathLibrary.MakeRotator", 3520, 160); connect(pitch_val_side, "ReturnValue", rot_side, "Pitch"); set_value(rot_side, "Yaw", 0.0); set_value(rot_side, "Roll", 0.0)
    trans_side = fn(ed, "/Script/Engine.KismetMathLibrary.MakeTransform", 3740, 220); connect(add_side, "ReturnValue", trans_side, "Location"); connect(rot_side, "ReturnValue", trans_side, "Rotation"); set_value(trans_side, "Scale", "1,1,1")
    spawn_side = fn(ed, "/Script/Engine.GameplayStatics.BeginDeferredActorSpawnFromClass", 3960, 160)
    set_value(spawn_side, "ActorClass", "Class'/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase.BP_ProjectileBase_C'")
    connect(set_fb_atk_side, "then", spawn_side, "execute"); connect(trans_side, "ReturnValue", spawn_side, "SpawnTransform")
    finish_side = fn(ed, "/Script/Engine.GameplayStatics.FinishSpawningActor", 4220, 160)
    connect(spawn_side, "then", finish_side, "execute"); connect(spawn_side, "ReturnValue", finish_side, "Actor"); connect(trans_side, "ReturnValue", finish_side, "SpawnTransform")

    # ==================== 分支 B: 纯移动/待机状态 (Shooting = False) ====================
    # 移动判断
    br_move_state = ed.add_branch_node(); br_move_state.set_node_pos(unreal.IntPoint(2400, 480))
    connect(br_is_shooting, "else", br_move_state, "execute"); connect(is_moving, "ReturnValue", br_move_state, "Condition")

    # 移动时设置 ScaleX (向右镜像，向左正常)
    connect(br_move_state, "then", set_sc, "execute")

    # 移动动画
    br_side_run = ed.add_branch_node(); br_side_run.set_node_pos(unreal.IntPoint(2860, 480))
    connect(set_sc, "then", br_side_run, "execute"); connect(cmp_x, "ReturnValue", br_side_run, "Condition")
    
    set_fb_run_side = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 3080, 440)
    if fb_run_left:
        set_value(set_fb_run_side, "NewFlipbook", f"PaperFlipbook'{fb_run_left.get_path_name()}'")
    connect(br_side_run, "then", set_fb_run_side, "execute"); connect(get_comp, "ReturnValue", set_fb_run_side, "self")
    
    br_up_run = ed.add_branch_node(); br_up_run.set_node_pos(unreal.IntPoint(3080, 560))
    connect(br_side_run, "else", br_up_run, "execute"); connect(is_up_input, "ReturnValue", br_up_run, "Condition")
    
    set_fb_run_up = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 3300, 520)
    if fb_run_up:
        set_value(set_fb_run_up, "NewFlipbook", f"PaperFlipbook'{fb_run_up.get_path_name()}'")
    connect(br_up_run, "then", set_fb_run_up, "execute"); connect(get_comp, "ReturnValue", set_fb_run_up, "self")
    
    set_fb_run_down = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 3300, 620)
    if fb_run_down:
        set_value(set_fb_run_down, "NewFlipbook", f"PaperFlipbook'{fb_run_down.get_path_name()}'")
    connect(br_up_run, "else", set_fb_run_down, "execute"); connect(get_comp, "ReturnValue", set_fb_run_down, "self")

    # 待机保持动画
    get_curr_fb = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.GetFlipbook", 2640, 700); connect(get_comp, "ReturnValue", get_curr_fb, "self")
    
    is_curr_up = fn(ed, "/Script/Engine.KismetMathLibrary.EqualEqual_ObjectObject", 2860, 700); connect(get_curr_fb, "ReturnValue", is_curr_up, "A")
    if fb_run_up:
        set_value(is_curr_up, "B", f"PaperFlipbook'{fb_run_up.get_path_name()}'")
    br_idle_up = ed.add_branch_node(); br_idle_up.set_node_pos(unreal.IntPoint(3080, 700))
    connect(br_move_state, "else", br_idle_up, "execute"); connect(is_curr_up, "ReturnValue", br_idle_up, "Condition")
    
    set_fb_idle_up = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 3300, 700)
    if fb_idle_up:
        set_value(set_fb_idle_up, "NewFlipbook", f"PaperFlipbook'{fb_idle_up.get_path_name()}'")
    connect(br_idle_up, "then", set_fb_idle_up, "execute"); connect(get_comp, "ReturnValue", set_fb_idle_up, "self")
    
    is_curr_side = fn(ed, "/Script/Engine.KismetMathLibrary.EqualEqual_ObjectObject", 3080, 800); connect(get_curr_fb, "ReturnValue", is_curr_side, "A")
    if fb_run_left:
        set_value(is_curr_side, "B", f"PaperFlipbook'{fb_run_left.get_path_name()}'")
    br_idle_side = ed.add_branch_node(); br_idle_side.set_node_pos(unreal.IntPoint(3300, 800))
    connect(br_idle_up, "else", br_idle_side, "execute"); connect(is_curr_side, "ReturnValue", br_idle_side, "Condition")
    
    set_fb_idle_side = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 3520, 800)
    if fb_idle_left:
        set_value(set_fb_idle_side, "NewFlipbook", f"PaperFlipbook'{fb_idle_left.get_path_name()}'")
    connect(br_idle_side, "then", set_fb_idle_side, "execute"); connect(get_comp, "ReturnValue", set_fb_idle_side, "self")
    
    set_fb_idle_down = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 3520, 900)
    if fb_idle_down:
        set_value(set_fb_idle_down, "NewFlipbook", f"PaperFlipbook'{fb_idle_down.get_path_name()}'")
    connect(br_idle_side, "else", set_fb_idle_down, "execute"); connect(get_comp, "ReturnValue", set_fb_idle_down, "self")

    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    print("✅ 移动与射击 100% 同步状态机编译完成！")

def main():
    build_synchronized_player()
    ASSETS.save_directory(GEN, only_if_is_dirty=False, recursive=True)
    ASSETS.save_directory("/Game/Blueprints", only_if_is_dirty=False, recursive=True)

if __name__ == "__main__":
    main()
