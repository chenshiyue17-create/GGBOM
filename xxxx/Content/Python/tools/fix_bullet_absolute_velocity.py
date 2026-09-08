# -*- coding: utf-8 -*-
"""
UE5.8 2D 竖屏游戏: 彻底根治子弹发射方向
根本原因: InitialVelocityInLocalSpace 不可靠，放弃旋转推导速度方式
解决方案: Spawn 后直接对 ProjectileMovementComponent 赋世界坐标绝对速度向量
  - 屏幕向右 (D键): velocity = (-850, 0, 0)  [世界-X = 屏幕右]
  - 屏幕向左 (A键): velocity = (+850, 0, 0)  [世界+X = 屏幕左]
  - 屏幕向上 (W键): velocity = (0, 0, +850)  [世界+Z = 屏幕上]
  - 屏幕向下 (S键): velocity = (0, 0, -850)  [世界-Z = 屏幕下]

枪口坐标 (考虑胶囊体体积, 角色原点在胶囊体中心):
  - 左右射击: X = Loc_X +/- 45, Z = Loc_Z + 0 (身体中心), Y = -15 (子弹层)
  - 向上射击: X = Loc_X, Z = Loc_Z + 55 (头顶以上), Y = -15
  - 向下射击: X = Loc_X, Z = Loc_Z - 55 (脚底以下), Y = -15
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

def spawn_bullet_with_velocity(ed, prev_exec, get_loc, vx, vz, muzzle_x_offset, muzzle_z_offset, fb_obj, get_comp, node_x, node_y, label):
    """
    生成一颗子弹并直接赋予世界坐标绝对速度向量。
    vx, vz: 速度分量 (世界坐标)
    muzzle_x_offset, muzzle_z_offset: 相对角色中心的枪口偏移
    """
    # 枪口世界坐标 = 角色坐标 + 偏移 (Y 固定为子弹层 Y=-15, 即世界 Y 值与玩家相同)
    muzzle_vec = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", node_x, node_y + 100)
    set_value(muzzle_vec, "X", float(muzzle_x_offset))
    set_value(muzzle_vec, "Y", 0.0)
    set_value(muzzle_vec, "Z", float(muzzle_z_offset))
    
    add_muzzle = fn(ed, "/Script/Engine.KismetMathLibrary.Add_VectorVector", node_x + 220, node_y + 100)
    connect(get_loc, "ReturnValue", add_muzzle, "A")
    connect(muzzle_vec, "ReturnValue", add_muzzle, "B")

    # 单位旋转（不影响速度方向，速度直接赋绝对值）
    rot_zero = fn(ed, "/Script/Engine.KismetMathLibrary.MakeRotator", node_x + 220, node_y + 200)
    set_value(rot_zero, "Pitch", 0.0); set_value(rot_zero, "Yaw", 0.0); set_value(rot_zero, "Roll", 0.0)

    # Transform
    trans = fn(ed, "/Script/Engine.KismetMathLibrary.MakeTransform", node_x + 440, node_y + 100)
    connect(add_muzzle, "ReturnValue", trans, "Location")
    connect(rot_zero, "ReturnValue", trans, "Rotation")
    set_value(trans, "Scale", "1,1,1")

    # SetFlipbook (攻击动画)
    if fb_obj:
        set_fb = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", node_x, node_y)
        set_value(set_fb, "NewFlipbook", f"PaperFlipbook'{fb_obj.get_path_name()}'")
        connect(prev_exec, "then", set_fb, "execute")
        connect(get_comp, "ReturnValue", set_fb, "self")
        prev_exec = set_fb

    # Spawn
    spawn_n = fn(ed, "/Script/Engine.GameplayStatics.BeginDeferredActorSpawnFromClass", node_x + 660, node_y)
    set_value(spawn_n, "ActorClass", "Class'/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase.BP_ProjectileBase_C'")
    connect(prev_exec, "then", spawn_n, "execute")
    connect(trans, "ReturnValue", spawn_n, "SpawnTransform")

    finish_n = fn(ed, "/Script/Engine.GameplayStatics.FinishSpawningActor", node_x + 900, node_y)
    connect(spawn_n, "then", finish_n, "execute")
    connect(spawn_n, "ReturnValue", finish_n, "Actor")
    connect(trans, "ReturnValue", finish_n, "SpawnTransform")

    # 获取 ProjectileMovementComponent 并直接赋世界速度
    get_pm = fn(ed, "/Script/Engine.Actor.GetComponentByClass", node_x + 1120, node_y)
    set_value(get_pm, "ComponentClass", "Class'/Script/Engine.ProjectileMovementComponent'")
    connect(finish_n, "ReturnValue", get_pm, "self")

    vel_vec = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", node_x + 1120, node_y + 120)
    set_value(vel_vec, "X", float(vx)); set_value(vel_vec, "Y", 0.0); set_value(vel_vec, "Z", float(vz))

    set_vel = fn(ed, "/Script/Engine.MovementComponent.RequestDirectMove", node_x + 1360, node_y)
    connect(finish_n, "then", set_vel, "execute")
    connect(get_pm, "ReturnValue", set_vel, "self")
    connect(vel_vec, "ReturnValue", set_vel, "MoveVelocity")
    set_value(set_vel, "bForceMaxSpeed", True)

    return set_vel

def fix_projectile_base_clean():
    print("🔫 [1/2] 清理 BP_ProjectileBase 冲突组件，禁用 InitialVelocityInLocalSpace...")
    bp = unreal.load_asset(PROJ_BP_PATH)
    if not bp:
        return
    bullet_fb = unreal.load_asset("/Game/P01/Imported/Content/Asset/Art/03_Weapons/01_KineticPistol/Flipbooks/FB_T_Bullet_KineticPistol_Sheet")
    if not bullet_fb:
        bullet_fb = unreal.load_asset("/Game/P01/Imported/Intermediate/P01/Generated/ProjectileFlight4/01_KineticPistol/Flipbooks/FB_T_Bullet_KineticPistol_02_Flight_Strict4")

    handles = SUBOBJECTS.k2_gather_subobject_data_for_blueprint(bp)
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        if isinstance(obj, unreal.PaperSpriteComponent):
            # 禁用静态 Sprite, 消除重叠冲突
            obj.set_editor_property("visible", False)
            obj.set_editor_property("hidden_in_game", True)
        elif isinstance(obj, unreal.PaperFlipbookComponent):
            if bullet_fb:
                obj.set_editor_property("source_flipbook", bullet_fb)
            obj.set_editor_property("relative_location", unreal.Vector(0.0, 0.0, 0.0))
            obj.set_editor_property("relative_rotation", unreal.Rotator(0.0, 0.0, 0.0))
            obj.set_editor_property("relative_scale3d", unreal.Vector(0.45, 0.45, 0.45))
            obj.set_editor_property("translucency_sort_priority", 500)
            obj.set_editor_property("visible", True)
            obj.set_editor_property("hidden_in_game", False)
        elif isinstance(obj, unreal.ProjectileMovementComponent):
            obj.set_editor_property("initial_speed", 850.0)
            obj.set_editor_property("max_speed", 850.0)
            obj.set_editor_property("projectile_gravity_scale", 0.0)
            # 关键: 禁用 LocalSpace，使用绝对世界速度
            try:
                obj.set_editor_property("initial_velocity_in_local_space", False)
                obj.set_editor_property("rotation_follows_velocity", True)
            except Exception:
                pass
        elif isinstance(obj, unreal.SphereComponent):
            obj.set_editor_property("sphere_radius", 14.0)
        elif isinstance(obj, unreal.BoxComponent):
            obj.set_editor_property("box_extent", unreal.Vector(14.0, 14.0, 14.0))

    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    print("✅ BP_ProjectileBase 清理完成！")

def rebuild_player_with_absolute_velocity():
    print("🎮 [2/2] 重构 BP_Player_Medic: 绝对世界速度发射 + 胶囊体枪口修正...")
    bp = unreal.load_asset(PLAYER_BP_PATH)
    if not bp:
        return

    pfx = "/Game/P01/Imported/Content/Asset/Art/01_Player"
    fb_idle_down = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_01_Down/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_01_Down_Sheet")
    fb_idle_up   = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_05_Up/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_05_Up_Sheet")
    fb_idle_left = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_03_Left/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_03_Left_Sheet")
    fb_run_down  = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_01_Down/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_01_Down_Sheet")
    fb_run_up    = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_05_Up/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_05_Up_Sheet")
    fb_run_left  = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_03_Left/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_03_Left_Sheet")
    fb_atk_down  = unreal.load_asset(f"{pfx}/02_Attack_Hurt/Dir_01_Down/Attack/Flipbooks/FB_T_Player_Medic_Attack_Dir_01_Down_Sheet")
    fb_atk_up    = unreal.load_asset(f"{pfx}/02_Attack_Hurt/Dir_05_Up/Attack/Flipbooks/FB_T_Player_Medic_Attack_Dir_05_Up_Sheet")
    fb_atk_side  = unreal.load_asset(f"{pfx}/02_Attack_Hurt/Dir_03_Right/Attack/Flipbooks/FB_T_Player_Medic_Attack_Dir_03_Right_Sheet")

    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    
    tick = ed.find_event_node("ReceiveTick")
    pc_tick = fn(ed, "/Script/Engine.GameplayStatics.GetPlayerController", 0, 0)
    set_value(pc_tick, "PlayerIndex", 0)

    # ============================================================
    # 1. WASD 输入采样
    # Camera Yaw=90: 屏幕右 = 世界-X, 屏幕左 = 世界+X
    # ============================================================
    key_a = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, -180)
    set_value(key_a, "Key", "A"); connect(pc_tick, "ReturnValue", key_a, "self")
    key_d = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, -80)
    set_value(key_d, "Key", "D"); connect(pc_tick, "ReturnValue", key_d, "self")
    sel_a = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, -180)
    set_value(sel_a, "A", 1.0); set_value(sel_a, "B", 0.0); connect(key_a, "ReturnValue", sel_a, "bPickA")
    sel_d = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, -80)
    set_value(sel_d, "A", -1.0); set_value(sel_d, "B", 0.0); connect(key_d, "ReturnValue", sel_d, "bPickA")
    raw_x = fn(ed, "/Script/Engine.KismetMathLibrary.Add_DoubleDouble", 660, -130)
    connect(sel_a, "ReturnValue", raw_x, "A"); connect(sel_d, "ReturnValue", raw_x, "B")
    
    key_w = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, 40)
    set_value(key_w, "Key", "W"); connect(pc_tick, "ReturnValue", key_w, "self")
    key_s = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, 140)
    set_value(key_s, "Key", "S"); connect(pc_tick, "ReturnValue", key_s, "self")
    sel_w = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, 40)
    set_value(sel_w, "A", 1.0); set_value(sel_w, "B", 0.0); connect(key_w, "ReturnValue", sel_w, "bPickA")
    sel_s = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, 140)
    set_value(sel_s, "A", -1.0); set_value(sel_s, "B", 0.0); connect(key_s, "ReturnValue", sel_s, "bPickA")
    raw_z = fn(ed, "/Script/Engine.KismetMathLibrary.Add_DoubleDouble", 660, 90)
    connect(sel_w, "ReturnValue", raw_z, "A"); connect(sel_s, "ReturnValue", raw_z, "B")

    # ============================================================
    # 2. 移动
    # ============================================================
    mul_x = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 880, -130)
    connect(raw_x, "ReturnValue", mul_x, "A"); set_value(mul_x, "B", 420.0)
    mul_z = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 880, 90)
    connect(raw_z, "ReturnValue", mul_z, "A"); set_value(mul_z, "B", 420.0)
    move_vec = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 1100, 0)
    connect(mul_x, "ReturnValue", move_vec, "X"); set_value(move_vec, "Y", 0.0); connect(mul_z, "ReturnValue", move_vec, "Z")
    mul_dt = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_VectorFloat", 1320, 0)
    connect(move_vec, "ReturnValue", mul_dt, "A"); connect(tick, "DeltaSeconds", mul_dt, "B")
    move_node = fn(ed, "/Script/Engine.Actor.K2_AddActorWorldOffset", 1540, 0)
    set_value(move_node, "bSweep", "true")
    connect(tick, "then", move_node, "execute")
    connect(mul_dt, "ReturnValue", move_node, "DeltaLocation")

    # ============================================================
    # 3. 方向判定 & 镜像
    # ============================================================
    cmp_x = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_DoubleDouble", 880, -250)
    connect(raw_x, "ReturnValue", cmp_x, "A"); set_value(cmp_x, "B", 0.0)
    cmp_z = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_DoubleDouble", 880, 250)
    connect(raw_z, "ReturnValue", cmp_z, "A"); set_value(cmp_z, "B", 0.0)
    is_moving = fn(ed, "/Script/Engine.KismetMathLibrary.BooleanOR", 1100, 200)
    connect(cmp_x, "ReturnValue", is_moving, "A"); connect(cmp_z, "ReturnValue", is_moving, "B")

    get_comp = fn(ed, "/Script/Engine.Actor.GetComponentByClass", 1540, -200)
    set_value(get_comp, "ComponentClass", "Class'/Script/Paper2D.PaperFlipbookComponent'")

    # is_right_dir = (raw_x < 0), 即按了 D 键
    is_up_dir    = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 2200, -260)
    connect(raw_z, "ReturnValue", is_up_dir, "A"); set_value(is_up_dir, "B", 0.0)
    is_down_dir  = fn(ed, "/Script/Engine.KismetMathLibrary.Less_DoubleDouble",    2200, -160)
    connect(raw_z, "ReturnValue", is_down_dir, "A"); set_value(is_down_dir, "B", 0.0)
    is_right_dir = fn(ed, "/Script/Engine.KismetMathLibrary.Less_DoubleDouble",    2200, 40)
    connect(raw_x, "ReturnValue", is_right_dir, "A"); set_value(is_right_dir, "B", 0.0)

    # ScaleX: D键向右时镜像 -0.5，A键向左时正向 +0.5
    scale_val_x = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 2420, -320)
    set_value(scale_val_x, "A", -0.5); set_value(scale_val_x, "B", 0.5); connect(is_right_dir, "ReturnValue", scale_val_x, "bPickA")
    scale_vec = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 2640, -320)
    connect(scale_val_x, "ReturnValue", scale_vec, "X"); set_value(scale_vec, "Y", 0.5); set_value(scale_vec, "Z", 0.5)
    set_sc = fn(ed, "/Script/Engine.SceneComponent.SetRelativeScale3D", 2860, -320)
    connect(get_comp, "ReturnValue", set_sc, "self"); connect(scale_vec, "ReturnValue", set_sc, "NewScale3D")

    # ============================================================
    # 4. J 键射击分支
    # ============================================================
    key_j = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 1760, 200)
    set_value(key_j, "Key", "J"); connect(pc_tick, "ReturnValue", key_j, "self")
    br_shoot = ed.add_branch_node(); br_shoot.set_node_pos(unreal.IntPoint(1980, 0))
    connect(move_node, "then", br_shoot, "execute"); connect(key_j, "ReturnValue", br_shoot, "Condition")

    get_loc = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 2640, 0)

    # ============================================================
    # 5. 射击分支树 (绝对世界速度, 枪口考虑胶囊体半径 r=26, 半高 h=36)
    #
    # 胶囊体原点 = 角色中心
    # 枪口偏移规则:
    #   左右: X 偏移 = ±(26 + 20) = ±46 (超出胶囊边缘), Z = 0 (身体中心高度)
    #   向上: X = 0, Z = +(36 + 25) = +61 (超出头顶)
    #   向下: X = 0, Z = -(36 + 25) = -61 (超出脚底)
    #
    # 世界速度绝对值 (Camera Yaw=90, 屏幕右 = 世界-X):
    #   向右(D): vx = -850, vz = 0
    #   向左(A): vx = +850, vz = 0
    #   向上(W): vx =    0, vz = +850
    #   向下(S): vx =    0, vz = -850
    # ============================================================

    # 向上分支
    br_up = ed.add_branch_node(); br_up.set_node_pos(unreal.IntPoint(2420, -200))
    connect(br_shoot, "then", br_up, "execute"); connect(is_up_dir, "ReturnValue", br_up, "Condition")
    end_up = spawn_bullet_with_velocity(ed, br_up, get_loc, vx=0, vz=850, muzzle_x_offset=0, muzzle_z_offset=61, fb_obj=fb_atk_up, get_comp=get_comp, node_x=2640, node_y=-300, label="Up")

    # 向下分支
    br_down = ed.add_branch_node(); br_down.set_node_pos(unreal.IntPoint(2640, 60))
    connect(br_up, "else", br_down, "execute"); connect(is_down_dir, "ReturnValue", br_down, "Condition")
    end_down = spawn_bullet_with_velocity(ed, br_down, get_loc, vx=0, vz=-850, muzzle_x_offset=0, muzzle_z_offset=-61, fb_obj=fb_atk_down, get_comp=get_comp, node_x=2860, node_y=-60, label="Down")

    # 右侧分支 (D键)
    br_right = ed.add_branch_node(); br_right.set_node_pos(unreal.IntPoint(2860, 320))
    connect(br_down, "else", br_right, "execute"); connect(is_right_dir, "ReturnValue", br_right, "Condition")
    # 向右: 枪口在胶囊体右侧 (-46, 0, 0), 世界速度 (-850, 0, 0)
    end_right = spawn_bullet_with_velocity(ed, br_right, get_loc, vx=-850, vz=0, muzzle_x_offset=-46, muzzle_z_offset=0, fb_obj=fb_atk_side, get_comp=get_comp, node_x=3080, node_y=200, label="Right")

    # 向左: 枪口在胶囊体左侧 (+46, 0, 0), 世界速度 (+850, 0, 0)
    end_left = spawn_bullet_with_velocity(ed, br_right, get_loc, vx=850, vz=0, muzzle_x_offset=46, muzzle_z_offset=0, fb_obj=fb_atk_side, get_comp=get_comp, node_x=3080, node_y=540, label="Left")
    # 连接 else
    connect(br_right, "else", end_left, "execute")

    # ============================================================
    # 6. 非射击分支: 移动动画与待机
    # ============================================================
    br_move = ed.add_branch_node(); br_move.set_node_pos(unreal.IntPoint(2420, 900))
    connect(br_shoot, "else", br_move, "execute"); connect(is_moving, "ReturnValue", br_move, "Condition")
    connect(br_move, "then", set_sc, "execute")

    br_side_run = ed.add_branch_node(); br_side_run.set_node_pos(unreal.IntPoint(2860, 900))
    connect(set_sc, "then", br_side_run, "execute"); connect(cmp_x, "ReturnValue", br_side_run, "Condition")
    set_fb_run_side = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 3080, 860)
    if fb_run_left: set_value(set_fb_run_side, "NewFlipbook", f"PaperFlipbook'{fb_run_left.get_path_name()}'")
    connect(br_side_run, "then", set_fb_run_side, "execute"); connect(get_comp, "ReturnValue", set_fb_run_side, "self")

    br_up_run = ed.add_branch_node(); br_up_run.set_node_pos(unreal.IntPoint(3080, 980))
    connect(br_side_run, "else", br_up_run, "execute"); connect(is_up_dir, "ReturnValue", br_up_run, "Condition")
    set_fb_run_up = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 3300, 940)
    if fb_run_up: set_value(set_fb_run_up, "NewFlipbook", f"PaperFlipbook'{fb_run_up.get_path_name()}'")
    connect(br_up_run, "then", set_fb_run_up, "execute"); connect(get_comp, "ReturnValue", set_fb_run_up, "self")
    set_fb_run_down = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 3300, 1060)
    if fb_run_down: set_value(set_fb_run_down, "NewFlipbook", f"PaperFlipbook'{fb_run_down.get_path_name()}'")
    connect(br_up_run, "else", set_fb_run_down, "execute"); connect(get_comp, "ReturnValue", set_fb_run_down, "self")

    # 待机状态保持
    get_curr_fb = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.GetFlipbook", 2640, 1180)
    connect(get_comp, "ReturnValue", get_curr_fb, "self")
    
    is_up_r = fn(ed, "/Script/Engine.KismetMathLibrary.EqualEqual_ObjectObject", 2860, 1120); connect(get_curr_fb, "ReturnValue", is_up_r, "A")
    if fb_run_up: set_value(is_up_r, "B", f"PaperFlipbook'{fb_run_up.get_path_name()}'")
    is_up_i = fn(ed, "/Script/Engine.KismetMathLibrary.EqualEqual_ObjectObject", 2860, 1180); connect(get_curr_fb, "ReturnValue", is_up_i, "A")
    if fb_idle_up: set_value(is_up_i, "B", f"PaperFlipbook'{fb_idle_up.get_path_name()}'")
    is_keep_up = fn(ed, "/Script/Engine.KismetMathLibrary.BooleanOR", 3080, 1150); connect(is_up_r, "ReturnValue", is_keep_up, "A"); connect(is_up_i, "ReturnValue", is_keep_up, "B")
    br_idle_up = ed.add_branch_node(); br_idle_up.set_node_pos(unreal.IntPoint(3300, 1140))
    connect(br_move, "else", br_idle_up, "execute"); connect(is_keep_up, "ReturnValue", br_idle_up, "Condition")
    set_fb_idle_up = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 3520, 1140)
    if fb_idle_up: set_value(set_fb_idle_up, "NewFlipbook", f"PaperFlipbook'{fb_idle_up.get_path_name()}'")
    connect(br_idle_up, "then", set_fb_idle_up, "execute"); connect(get_comp, "ReturnValue", set_fb_idle_up, "self")

    is_down_r = fn(ed, "/Script/Engine.KismetMathLibrary.EqualEqual_ObjectObject", 3080, 1260); connect(get_curr_fb, "ReturnValue", is_down_r, "A")
    if fb_run_down: set_value(is_down_r, "B", f"PaperFlipbook'{fb_run_down.get_path_name()}'")
    is_down_i = fn(ed, "/Script/Engine.KismetMathLibrary.EqualEqual_ObjectObject", 3080, 1320); connect(get_curr_fb, "ReturnValue", is_down_i, "A")
    if fb_idle_down: set_value(is_down_i, "B", f"PaperFlipbook'{fb_idle_down.get_path_name()}'")
    is_keep_down = fn(ed, "/Script/Engine.KismetMathLibrary.BooleanOR", 3300, 1290); connect(is_down_r, "ReturnValue", is_keep_down, "A"); connect(is_down_i, "ReturnValue", is_keep_down, "B")
    br_idle_down = ed.add_branch_node(); br_idle_down.set_node_pos(unreal.IntPoint(3520, 1260))
    connect(br_idle_up, "else", br_idle_down, "execute"); connect(is_keep_down, "ReturnValue", br_idle_down, "Condition")
    set_fb_idle_down = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 3740, 1260)
    if fb_idle_down: set_value(set_fb_idle_down, "NewFlipbook", f"PaperFlipbook'{fb_idle_down.get_path_name()}'")
    connect(br_idle_down, "then", set_fb_idle_down, "execute"); connect(get_comp, "ReturnValue", set_fb_idle_down, "self")
    set_fb_idle_side = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 3740, 1380)
    if fb_idle_left: set_value(set_fb_idle_side, "NewFlipbook", f"PaperFlipbook'{fb_idle_left.get_path_name()}'")
    connect(br_idle_down, "else", set_fb_idle_side, "execute"); connect(get_comp, "ReturnValue", set_fb_idle_side, "self")

    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    print("✅ BP_Player_Medic 绝对速度发射重构完成！")

def main():
    fix_projectile_base_clean()
    rebuild_player_with_absolute_velocity()
    ASSETS.save_directory(GEN, only_if_is_dirty=False, recursive=True)
    ASSETS.save_directory("/Game/Blueprints", only_if_is_dirty=False, recursive=True)
    print("ALL_ABSOLUTE_VELOCITY_BULLET_FIX_COMPLETE")

if __name__ == "__main__":
    main()
