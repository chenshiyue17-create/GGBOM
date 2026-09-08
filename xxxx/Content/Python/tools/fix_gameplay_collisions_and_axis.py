# -*- coding: utf-8 -*-
"""
UE5.8 2D 竖屏游戏: 核心坐标轴、真实碰撞体系与分层渲染终极根治
1. 坐标系纠偏 (Camera Yaw=90): D键向右(-X, ScaleX=-0.5), A键向左(+X, ScaleX=0.5), W键向上(+Z), S键向下(-Z)
2. 分层渲染防闪烁: 地面(Y=80), 掩体(Y=30), 怪物(Y=15), 玩家(Y=0), 子弹(Y=-15), UI(Y=-60)
3. 真实 2D 碰撞体系: 玩家 CapsuleComponent (Pawn), 掩体 BoxComponent (BlockAll), 屏幕边界墙 (BlockAll)
4. 怪物合理疏散排布，消除拥挤重叠
"""
from __future__ import annotations
import unreal

GEN = "/Game/GGBOM"
MAP_PATH = f"{GEN}/Maps/MAP_GGBOM_Main"
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
# 1. 修复子弹 BP_ProjectileBase 碰撞与物理
# ==============================================================================
def fix_bullet_bp():
    print("🔫 [1/3] 正在配置子弹 BP_ProjectileBase (碰撞 + 零误差推进)...")
    bp = unreal.load_asset(PROJ_BP_PATH)
    if not bp:
        return

    handles = SUBOBJECTS.k2_gather_subobject_data_for_blueprint(bp)
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        if "Flipbook" in vname or "Sprite" in vname or isinstance(obj, unreal.PaperFlipbookComponent):
            obj.set_editor_property("relative_location", unreal.Vector(0.0, 0.0, 0.0))
            obj.set_editor_property("relative_rotation", unreal.Rotator(0.0, 0.0, 0.0))
            obj.set_editor_property("relative_scale3d", unreal.Vector(0.35, 0.35, 0.35))
            obj.set_editor_property("translucency_sort_priority", 500)
            obj.set_editor_property("visible", True)
            obj.set_editor_property("hidden_in_game", False)
        elif "Movement" in vname or isinstance(obj, unreal.ProjectileMovementComponent):
            obj.set_editor_property("initial_speed", 900.0)
            obj.set_editor_property("max_speed", 900.0)
            obj.set_editor_property("projectile_gravity_scale", 0.0)
        elif isinstance(obj, unreal.SphereComponent):
            obj.set_editor_property("sphere_radius", 14.0)
        elif isinstance(obj, unreal.BoxComponent):
            obj.set_editor_property("box_extent", unreal.Vector(14.0, 14.0, 14.0))
        elif isinstance(obj, unreal.CapsuleComponent):
            obj.set_editor_property("capsule_radius", 14.0)
            obj.set_editor_property("capsule_half_height", 14.0)

    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    print("✅ BP_ProjectileBase 配置完成！")

# ==============================================================================
# 2. 彻底修正主角 BP_Player_Medic 坐标系 (D键向右, A键向左, W上, S下)
# ==============================================================================
def rebuild_player_medic():
    print("🎮 [2/3] 正在修正主角 BP_Player_Medic (完美视角对齐: D向右, A向左, 碰撞启用)...")
    bp = unreal.load_asset(PLAYER_BP_PATH)
    if not bp:
        return

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
            obj.set_editor_property("translucency_sort_priority", 300)
            obj.set_editor_property("visible", True)
            obj.set_editor_property("hidden_in_game", False)
        elif isinstance(obj, unreal.CapsuleComponent):
            obj.set_editor_property("capsule_radius", 26.0)
            obj.set_editor_property("capsule_half_height", 36.0)
        elif isinstance(obj, unreal.BoxComponent):
            obj.set_editor_property("box_extent", unreal.Vector(26.0, 26.0, 36.0))
        elif isinstance(obj, unreal.SphereComponent):
            obj.set_editor_property("sphere_radius", 26.0)

    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    tick = ed.find_event_node("ReceiveTick")
    
    pc_tick = fn(ed, "/Script/Engine.GameplayStatics.GetPlayerController", 0, 0)
    set_value(pc_tick, "PlayerIndex", 0)

    # 1. 视口绝对方向定义 (Yaw=90 Camera):
    # D键(屏幕向右): 世界 -X 方向
    # A键(屏幕向左): 世界 +X 方向
    # W键(屏幕向上): 世界 +Z 方向
    # S键(屏幕向下): 世界 -Z 方向
    key_a = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, -180); set_value(key_a, "Key", "A"); connect(pc_tick, "ReturnValue", key_a, "self")
    key_d = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, -80);  set_value(key_d, "Key", "D"); connect(pc_tick, "ReturnValue", key_d, "self")
    # A = +1.0 (左, +X), D = -1.0 (右, -X)
    sel_a = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, -180); set_value(sel_a, "A", 1.0);  set_value(sel_a, "B", 0.0); connect(key_a, "ReturnValue", sel_a, "bPickA")
    sel_d = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, -80);  set_value(sel_d, "A", -1.0); set_value(sel_d, "B", 0.0); connect(key_d, "ReturnValue", sel_d, "bPickA")
    raw_x = fn(ed, "/Script/Engine.KismetMathLibrary.Add_DoubleDouble", 660, -130); connect(sel_a, "ReturnValue", raw_x, "A"); connect(sel_d, "ReturnValue", raw_x, "B")
    
    key_w = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, 40);   set_value(key_w, "Key", "W"); connect(pc_tick, "ReturnValue", key_w, "self")
    key_s = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, 140);  set_value(key_s, "Key", "S"); connect(pc_tick, "ReturnValue", key_s, "self")
    # W = +1.0 (上, +Z), S = -1.0 (下, -Z)
    sel_w = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, 40);   set_value(sel_w, "A", 1.0);  set_value(sel_w, "B", 0.0); connect(key_w, "ReturnValue", sel_w, "bPickA")
    sel_s = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, 140);  set_value(sel_s, "A", -1.0); set_value(sel_s, "B", 0.0); connect(key_s, "ReturnValue", sel_s, "bPickA")
    raw_z = fn(ed, "/Script/Engine.KismetMathLibrary.Add_DoubleDouble", 660, 90); connect(sel_w, "ReturnValue", raw_z, "A"); connect(sel_s, "ReturnValue", raw_z, "B")

    # 2. 移动位移计算 (开启 bSweep=True 启用物理碰撞检测)
    mul_x = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 880, -130); connect(raw_x, "ReturnValue", mul_x, "A"); set_value(mul_x, "B", 420.0)
    mul_z = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 880, 90);  connect(raw_z, "ReturnValue", mul_z, "A"); set_value(mul_z, "B", 420.0)
    
    move_vec = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 1100, 0)
    connect(mul_x, "ReturnValue", move_vec, "X"); set_value(move_vec, "Y", 0.0); connect(mul_z, "ReturnValue", move_vec, "Z")
    
    mul_dt = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_VectorFloat", 1320, 0)
    connect(move_vec, "ReturnValue", mul_dt, "A"); connect(tick, "DeltaSeconds", mul_dt, "B")
    
    move_node = fn(ed, "/Script/Engine.Actor.K2_AddActorWorldOffset", 1540, 0)
    set_value(move_node, "bSweep", "true")
    connect(tick, "then", move_node, "execute")
    connect(mul_dt, "ReturnValue", move_node, "DeltaLocation")

    # 3. 移动特征
    cmp_x = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_DoubleDouble", 880, -250); connect(raw_x, "ReturnValue", cmp_x, "A"); set_value(cmp_x, "B", 0.0)
    cmp_z = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_DoubleDouble", 880, 250);  connect(raw_z, "ReturnValue", cmp_z, "A"); set_value(cmp_z, "B", 0.0)
    is_moving = fn(ed, "/Script/Engine.KismetMathLibrary.BooleanOR", 1100, 200); connect(cmp_x, "ReturnValue", is_moving, "A"); connect(cmp_z, "ReturnValue", is_moving, "B")

    get_comp = fn(ed, "/Script/Engine.Actor.GetComponentByClass", 1540, -200); set_value(get_comp, "ComponentClass", "Class'/Script/Paper2D.PaperFlipbookComponent'")
    
    # 4. 射击按键采样
    key_j = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 1760, 200); set_value(key_j, "Key", "J"); connect(pc_tick, "ReturnValue", key_j, "self")
    br_is_shooting = ed.add_branch_node(); br_is_shooting.set_node_pos(unreal.IntPoint(1980, 0))
    connect(move_node, "then", br_is_shooting, "execute")
    connect(key_j, "ReturnValue", br_is_shooting, "Condition")

    # 5. 朝向特征:
    # raw_z > 0 -> Up (W)
    # raw_z < 0 -> Down (S)
    # raw_x < 0 -> Right (D键, 屏幕向右, 世界-X) -> is_right_dir = True
    # raw_x > 0 -> Left (A键, 屏幕向左, 世界+X) -> is_right_dir = False
    is_up_dir = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 2200, -260); connect(raw_z, "ReturnValue", is_up_dir, "A"); set_value(is_up_dir, "B", 0.0)
    is_down_dir = fn(ed, "/Script/Engine.KismetMathLibrary.Less_DoubleDouble", 2200, -160); connect(raw_z, "ReturnValue", is_down_dir, "A"); set_value(is_down_dir, "B", 0.0)
    is_right_dir = fn(ed, "/Script/Engine.KismetMathLibrary.Less_DoubleDouble", 2200, 40); connect(raw_x, "ReturnValue", is_right_dir, "A"); set_value(is_right_dir, "B", 0.0)

    # 左右 ScaleX 镜像: D键向右(is_right_dir=True)为 -0.5 镜像朝右，A键向左(is_right_dir=False)为 0.5 朝左
    scale_val_x = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 2420, -320); set_value(scale_val_x, "A", -0.5); set_value(scale_val_x, "B", 0.5); connect(is_right_dir, "ReturnValue", scale_val_x, "bPickA")
    scale_vec = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 2640, -320); connect(scale_val_x, "ReturnValue", scale_vec, "X"); set_value(scale_vec, "Y", 0.5); set_value(scale_vec, "Z", 0.5)
    set_sc = fn(ed, "/Script/Engine.SceneComponent.SetRelativeScale3D", 2860, -320); connect(get_comp, "ReturnValue", set_sc, "self"); connect(scale_vec, "ReturnValue", set_sc, "NewScale3D")

    # ==================== 射击分支 (Shooting = True) ====================
    # 1. 向上射击: 枪口 (0, 0, 45), 速度向 +Z, Pitch = 90.0, Yaw = 0.0
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

    # 2. 向下射击: 枪口 (0, 0, -45), 速度向 -Z, Pitch = -90.0, Yaw = 0.0
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

    # 3. 侧向射击:
    # D键向右(is_right_dir=True): 枪口向右(-45,0,0), 旋转 Yaw=180
    # A键向左(is_right_dir=False): 枪口向左(+45,0,0), 旋转 Yaw=0
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

    # ==================== 待机保持分支 ====================
    get_curr_fb = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.GetFlipbook", 2640, 700); connect(get_comp, "ReturnValue", get_curr_fb, "self")
    
    # 1. 向上待机判定
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
    
    # 2. 向下待机判定
    is_down_r = fn(ed, "/Script/Engine.KismetMathLibrary.EqualEqual_ObjectObject", 3080, 800); connect(get_curr_fb, "ReturnValue", is_down_r, "A")
    if fb_run_down: set_value(is_down_r, "B", f"PaperFlipbook'{fb_run_down.get_path_name()}'")
    is_down_i = fn(ed, "/Script/Engine.KismetMathLibrary.EqualEqual_ObjectObject", 3080, 860); connect(get_curr_fb, "ReturnValue", is_down_i, "A")
    if fb_idle_down: set_value(is_down_i, "B", f"PaperFlipbook'{fb_idle_down.get_path_name()}'")
    is_down_a = fn(ed, "/Script/Engine.KismetMathLibrary.EqualEqual_ObjectObject", 3080, 920); connect(get_curr_fb, "ReturnValue", is_down_a, "A")
    if fb_atk_down: set_value(is_down_a, "B", f"PaperFlipbook'{fb_atk_down.get_path_name()}'")

    is_down_or1 = fn(ed, "/Script/Engine.KismetMathLibrary.BooleanOR", 3300, 830); connect(is_down_r, "ReturnValue", is_down_or1, "A"); connect(is_down_i, "ReturnValue", is_down_or1, "B")
    is_keep_down = fn(ed, "/Script/Engine.KismetMathLibrary.BooleanOR", 3520, 850); connect(is_down_or1, "ReturnValue", is_keep_down, "A"); connect(is_down_a, "ReturnValue", is_keep_down, "B")

    br_idle_down = ed.add_branch_node(); br_idle_down.set_node_pos(unreal.IntPoint(3740, 800))
    connect(br_idle_up, "else", br_idle_down, "execute"); connect(is_keep_down, "ReturnValue", br_idle_down, "Condition")

    set_fb_idle_down = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 3960, 800)
    if fb_idle_down: set_value(set_fb_idle_down, "NewFlipbook", f"PaperFlipbook'{fb_idle_down.get_path_name()}'")
    connect(br_idle_down, "then", set_fb_idle_down, "execute"); connect(get_comp, "ReturnValue", set_fb_idle_down, "self")

    # 3. 侧向待机 (兜底)
    set_fb_idle_side = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 3960, 900)
    if fb_idle_left: set_value(set_fb_idle_side, "NewFlipbook", f"PaperFlipbook'{fb_idle_left.get_path_name()}'")
    connect(br_idle_down, "else", set_fb_idle_side, "execute"); connect(get_comp, "ReturnValue", set_fb_idle_side, "self")

    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    print("✅ 主角 BP_Player_Medic 坐标与朝向状态机重构完成！")

# ==============================================================================
# 3. 组装主关卡 MAP_GGBOM_Main (分层渲染防闪烁 + 实体碰撞隔离)
# ==============================================================================
def assemble_level_with_collisions():
    print("🗺️ [3/3] 正在组装关卡 (分层防闪烁 + 实体碰撞 + 疏散排布)...")
    unreal.EditorLevelLibrary.load_level(MAP_PATH)
    world = unreal.EditorLevelLibrary.get_editor_world()
    
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        lbl = a.get_actor_label()
        if not lbl.startswith("PlayerStart"):
            unreal.EditorLevelLibrary.destroy_actor(a)
            
    # 1. 9:16 正交相机 (满屏正视 X-Z 平面, OrthoWidth=941.0)
    cam = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.CameraActor, unreal.Vector(0, -600, 0), unreal.Rotator(pitch=0.0, yaw=90.0, roll=0.0)
    )
    cam_comp = cam.get_component_by_class(unreal.CameraComponent)
    cam_comp.set_editor_property("projection_mode", unreal.CameraProjectionMode.ORTHOGRAPHIC)
    cam_comp.set_editor_property("ortho_width", 941.0)
    cam_comp.set_editor_property("aspect_ratio", 0.5628)
    cam.set_editor_property("auto_activate_for_player", unreal.AutoReceiveInput.PLAYER0)
    cam.set_actor_label("PortraitCamera_9x16")
    
    # 2. 地面底层 (Y=+80, 优先级 -100)
    sp_ground = unreal.load_asset(f"{GEN}/Art/Sprites/SP_Ground")
    if sp_ground:
        g = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PaperSpriteActor, unreal.Vector(0, 80, 0), unreal.Rotator())
        g.get_component_by_class(unreal.PaperSpriteComponent).set_editor_property("source_sprite", sp_ground)
        g.get_component_by_class(unreal.PaperSpriteComponent).set_editor_property("translucency_sort_priority", -100)
        g.set_actor_scale3d(unreal.Vector(1.15, 1.15, 1.15))
        g.set_actor_label("Ground_Stage00")
        
    # 3. 战术掩体 (Y=+30, 优先级 50, 开启物理阻挡)
    sp_barricade = unreal.load_asset(f"{GEN}/Art/Sprites/SP_Barricade")
    if sp_barricade:
        barricades = [
            (-200, 30, 420, "Barricade_Top_L"),
            (200, 30, 420, "Barricade_Top_R"),
            (-220, 30, -50, "DefenseLine_L"),
            (220, 30, -50, "DefenseLine_R")
        ]
        for x, y, z, lbl in barricades:
            b = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PaperSpriteActor, unreal.Vector(x, y, z), unreal.Rotator())
            comp = b.get_component_by_class(unreal.PaperSpriteComponent)
            comp.set_editor_property("source_sprite", sp_barricade)
            comp.set_editor_property("translucency_sort_priority", 50)
            comp.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
            b.set_actor_scale3d(unreal.Vector(0.55, 0.55, 0.55))
            b.set_actor_label(lbl)

    # 4. 怪物军团 (Y=+15, 优先级 150, 各怪物理空间疏散隔离)
    pfx_z = "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Zombie"
    pfx_h = "/Game/P01/Imported/Content/Asset/Art/02_Enemies/MutantHound"
    pfx_b = "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Boss_Overlord"

    spaced_units = [
        # 前锋线 (Z = +160)
        (f"{pfx_z}/01_Zombie_Walker_Basic/Flipbooks/FB_T_Zombie_WalkerBasic_Sheet", 0, 160, 0.45, "Live_Zombie_Front"),
        
        # 中锋线 (Z = +300)
        (f"{pfx_h}/Run/Dir_01_Down/Flipbooks/FB_T_Hound_Run_Dir_01_Down_Sheet", -160, 300, 0.48, "Live_Hound_L"),
        (f"{pfx_z}/05_Zombie_Runner_Agile/Flipbooks/FB_T_Zombie_RunnerAgile_Sheet", 160, 300, 0.45, "Live_Zombie_Runner_R"),
        
        # 次强重装线 (Z = +420)
        (f"{pfx_z}/11_Zombie_Shambler_Heavy/Flipbooks/FB_T_Zombie_ShamblerHeavy_Sheet", 0, 420, 0.58, "Live_Shambler_Mid"),

        # 压轴领主 (Z = +560)
        (f"{pfx_b}/Actions/Walk/Dir_01_Down/Flipbooks/FB_T_Boss_Walk_Dir_01_Down_Sheet", 0, 560, 0.72, "Live_Boss_Overlord"),
    ]

    for fb_path, x, z, scale, lbl in spaced_units:
        fb = unreal.load_asset(fb_path)
        if fb:
            act = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PaperFlipbookActor, unreal.Vector(x, 15, z), unreal.Rotator())
            comp = act.get_component_by_class(unreal.PaperFlipbookComponent)
            comp.set_editor_property("source_flipbook", fb)
            comp.set_editor_property("translucency_sort_priority", 150)
            comp.set_editor_property("visible", True)
            comp.set_editor_property("hidden_in_game", False)
            act.set_actor_scale3d(unreal.Vector(scale, scale, scale))
            act.set_actor_label(lbl)
            print(f"  + 实装疏散怪物单位: {lbl} @ ({x}, 15, {z})")

    # 5. 玩家出生点 (下方中央, Y=0)
    p_starts = [a for a in unreal.EditorLevelLibrary.get_all_level_actors() if a.get_actor_label().startswith("PlayerStart")]
    if not p_starts:
        ps = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(0, 0, -480), unreal.Rotator())
        ps.set_actor_label("PlayerStart")
    else:
        p_starts[0].set_actor_location(unreal.Vector(0, 0, -480), False, False)

    # 6. 精密对齐 HUD 部件 (Y=-60, 优先级 1000)
    hud_items = [
        # 顶部 Boss 血条 (居中偏上 Z=+720)
        (f"{GEN}/Art/Sprites/SP_Boss_Bar_Bg", unreal.Vector(0, -60, 720), 0.75, 900, "UI_BossBar_Bg"),
        (f"{GEN}/Art/Sprites/SP_Boss_Bar_Fill", unreal.Vector(0, -60, 720), 0.72, 950, "UI_BossBar_Fill"),
        (f"{GEN}/Art/Sprites/SP_Boss_Skull", unreal.Vector(-200, -60, 720), 0.55, 1000, "UI_Boss_SkullIcon"),
        # 顶部右上角暂停按钮 (Z=+720, X=+360)
        (f"{GEN}/Art/Sprites/SP_Btn_Pause", unreal.Vector(360, -60, 720), 0.25, 1000, "UI_Btn_Pause"),
        # 底部血条与经验条 (居中偏下 Z=-680)
        (f"{GEN}/Art/Sprites/SP_HUD_HP_Bg", unreal.Vector(-200, -60, -680), 0.58, 900, "UI_Player_HP_Bg"),
        (f"{GEN}/Art/Sprites/SP_HUD_HP_Fill", unreal.Vector(-200, -60, -680), 0.56, 950, "UI_Player_HP_Fill"),
        (f"{GEN}/Art/Sprites/SP_HUD_Exp_Fill", unreal.Vector(-200, -60, -730), 0.48, 950, "UI_Player_EXP_Fill"),
        # 底部右侧弹药盘
        (f"{GEN}/Art/Sprites/SP_HUD_AmmoRadial", unreal.Vector(320, -60, -680), 0.45, 950, "UI_HUD_AmmoRadial"),
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
    print("ALL_AXIS_COLLISION_AND_LAYER_FIXES_COMPLETE")

def main():
    fix_bullet_bp()
    rebuild_player_medic()
    assemble_level_with_collisions()

if __name__ == "__main__":
    main()
