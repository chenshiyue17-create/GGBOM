# -*- coding: utf-8 -*-
"""
终末医疗兵 (GGBOM) - 视口与世界坐标数学底层根治方案
=====================================================
【根本物理成因与坐标系真相】
1. 关卡正交相机位于 (0, -600, 0), 朝向 Yaw=90 (面向世界 +Y 轴)
2. 在虚幻引擎左手笛卡尔坐标系中, 面向 +Y 轴时:
   - 屏幕右方 (Camera Right) = 世界 -X 轴 !
   - 屏幕左方 (Camera Left)  = 世界 +X 轴 !
   - 屏幕上方 (Camera Up)    = 世界 +Z 轴 !
   - 屏幕下方 (Camera Down)  = 世界 -Z 轴 !
3. 角色永不消失铁律:
   - 2D PaperFlipbook 是 XZ 平面单薄片, 绝对严禁调用 SetActorRotation (任何 Yaw/Pitch 旋转都会让薄片切向相机变成厚度为 0 而消失)!
   - Actor 旋转死死锁定在 (0, 0, 0)!
   - 左右朝向变更 100% 依靠 SetRelativeScale3D(X=-0.5 镜像朝右, X=0.5 朝左)!
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
    raise RuntimeError(f"Pin '{name}' not found; available={[str(PINLIB.get_pin_name(p)) for p in values]}")

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

def clean_and_configure_bullet():
    print("🔫 [1/3] 配置子弹 BP_ProjectileBase (穿透忽略玩家胶囊体, 零物理反弹)...")
    bp = unreal.load_asset(PROJ_BP_PATH)
    if not bp:
        return

    bullet_fb = unreal.load_asset("/Game/P01/Imported/Content/Asset/Art/03_Weapons/01_KineticPistol/Flipbooks/FB_T_Bullet_KineticPistol_Sheet")
    if not bullet_fb:
        bullet_fb = unreal.load_asset("/Game/P01/Representative/Intermediate/P01/Generated/ProjectileFlight4/01_KineticPistol/Flipbooks/FB_T_Bullet_KineticPistol_02_Flight_Strict4")

    handles = SUBOBJECTS.k2_gather_subobject_data_for_blueprint(bp)
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)

        if isinstance(obj, unreal.SphereComponent):
            obj.set_editor_property("sphere_radius", 6.0)
            obj.set_editor_property("relative_location", unreal.Vector(0.0, 0.0, 0.0))
            obj.set_editor_property("relative_rotation", unreal.Rotator(0.0, 0.0, 0.0))
            try:
                bi = obj.get_editor_property("body_instance")
                bi.set_editor_property("collision_profile_name", "OverlapAllDynamic")
                bi.set_editor_property("collision_enabled", unreal.CollisionEnabled.QUERY_ONLY)
            except:
                pass

        elif isinstance(obj, (unreal.PaperFlipbookComponent, unreal.PaperSpriteComponent)):
            try:
                bi = obj.get_editor_property("body_instance")
                bi.set_editor_property("collision_profile_name", "NoCollision")
                bi.set_editor_property("collision_enabled", unreal.CollisionEnabled.NO_COLLISION)
            except:
                pass
            obj.set_editor_property("relative_location", unreal.Vector(0.0, 0.0, 0.0))
            obj.set_editor_property("relative_rotation", unreal.Rotator(0.0, 0.0, 0.0))
            obj.set_editor_property("relative_scale3d", unreal.Vector(0.18, 0.18, 0.18))
            obj.set_editor_property("translucency_sort_priority", 500)
            if isinstance(obj, unreal.PaperFlipbookComponent) and bullet_fb:
                obj.set_editor_property("source_flipbook", bullet_fb)
                obj.set_editor_property("visible", True)
                obj.set_editor_property("hidden_in_game", False)
            elif isinstance(obj, unreal.PaperSpriteComponent):
                obj.set_editor_property("visible", False)
                obj.set_editor_property("hidden_in_game", True)

        elif isinstance(obj, unreal.ProjectileMovementComponent):
            obj.set_editor_property("initial_speed", 1600.0)
            obj.set_editor_property("max_speed", 1600.0)
            obj.set_editor_property("velocity", unreal.Vector(1600.0, 0.0, 0.0))
            obj.set_editor_property("initial_velocity_in_local_space", True)
            obj.set_editor_property("rotation_follows_velocity", True)
            obj.set_editor_property("should_bounce", False)
            obj.set_editor_property("projectile_gravity_scale", 0.0)

    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    print("✅ BP_ProjectileBase 配置完成！")

def rebuild_player_medic_clean():
    print("🎮 [2/3] 底层根治主角 BP_Player_Medic (纯正视口映射, 100%可见永不消失)...")
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

    handles = SUBOBJECTS.k2_gather_subobject_data_for_blueprint(bp)
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)

        if isinstance(obj, (unreal.CapsuleComponent, unreal.BoxComponent, unreal.SphereComponent)):
            if isinstance(obj, unreal.CapsuleComponent):
                obj.set_editor_property("capsule_radius", 26.0)
                obj.set_editor_property("capsule_half_height", 36.0)
            elif isinstance(obj, unreal.BoxComponent):
                obj.set_editor_property("box_extent", unreal.Vector(26.0, 26.0, 36.0))
            obj.set_editor_property("relative_location", unreal.Vector(0.0, 0.0, 0.0))
            obj.set_editor_property("relative_rotation", unreal.Rotator(0.0, 0.0, 0.0))
            try:
                bi = obj.get_editor_property("body_instance")
                bi.set_editor_property("collision_profile_name", "Pawn")
                bi.set_editor_property("collision_enabled", unreal.CollisionEnabled.QUERY_AND_PHYSICS)
            except:
                pass
        elif isinstance(obj, unreal.PaperFlipbookComponent):
            try:
                bi = obj.get_editor_property("body_instance")
                bi.set_editor_property("collision_profile_name", "NoCollision")
                bi.set_editor_property("collision_enabled", unreal.CollisionEnabled.NO_COLLISION)
            except:
                pass
            obj.set_editor_property("relative_location", unreal.Vector(0.0, 0.0, 0.0))
            obj.set_editor_property("relative_rotation", unreal.Rotator(0.0, 0.0, 0.0))
            obj.set_editor_property("relative_scale3d", unreal.Vector(0.5, 0.5, 0.5))
            obj.set_editor_property("translucency_sort_priority", 300)
            if fb_idle_up:
                obj.set_editor_property("source_flipbook", fb_idle_up)

    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    
    # 强制在 BeginPlay 重置角色旋转为 (0,0,0)，彻底杜绝任何历史旋转残留
    begin_play = ed.find_event_node("ReceiveBeginPlay")
    if not begin_play:
        begin_play = ed.add_event_node("ReceiveBeginPlay")
    begin_play.set_node_pos(unreal.IntPoint(-400, -350))
    reset_rot = fn(ed, "/Script/Engine.Actor.K2_SetActorRotation", -150, -350)
    set_value(reset_rot, "NewRotation", "0,0,0")
    set_value(reset_rot, "bTeleportPhysics", "true")
    connect(begin_play, "then", reset_rot, "execute")

    tick = ed.find_event_node("ReceiveTick")
    if not tick:
        tick = ed.add_event_node("ReceiveTick")
    tick.set_node_pos(unreal.IntPoint(-200, 0))

    pc = fn(ed, "/Script/Engine.GameplayStatics.GetPlayerController", 0, -200)
    set_value(pc, "PlayerIndex", 0)

    # 1. 键盘输入采样 (A, D, W, S, J)
    key_a = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, -250); set_value(key_a, "Key", "A"); connect(pc, "ReturnValue", key_a, "self")
    key_d = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, -150); set_value(key_d, "Key", "D"); connect(pc, "ReturnValue", key_d, "self")
    key_w = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, -50);  set_value(key_w, "Key", "W"); connect(pc, "ReturnValue", key_w, "self")
    key_s = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, 50);   set_value(key_s, "Key", "S"); connect(pc, "ReturnValue", key_s, "self")
    key_j = fn(ed, "/Script/Engine.PlayerController.WasInputKeyJustPressed", 220, 150); set_value(key_j, "Key", "J"); connect(pc, "ReturnValue", key_j, "self")

    # 【核心数学真理映射 (Camera Facing +Y, Left-Handed)】:
    # 屏幕右方 = 世界 -X (按 D 键: -1.0)
    # 屏幕左方 = 世界 +X (按 A 键: +1.0)
    # 屏幕上方 = 世界 +Z (按 W 键: +1.0)
    # 屏幕下方 = 世界 -Z (按 S 键: -1.0)
    sel_d = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, -250); set_value(sel_d, "A", -1.0); set_value(sel_d, "B", 0.0); connect(key_d, "ReturnValue", sel_d, "bPickA")
    sel_a = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, -150); set_value(sel_a, "A", 1.0);  set_value(sel_a, "B", 0.0); connect(key_a, "ReturnValue", sel_a, "bPickA")
    axis_x = fn(ed, "/Script/Engine.KismetMathLibrary.Add_DoubleDouble", 660, -200); connect(sel_d, "ReturnValue", axis_x, "A"); connect(sel_a, "ReturnValue", axis_x, "B")

    sel_w = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, -50);  set_value(sel_w, "A", 1.0);  set_value(sel_w, "B", 0.0); connect(key_w, "ReturnValue", sel_w, "bPickA")
    sel_s = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, 50);   set_value(sel_s, "A", -1.0); set_value(sel_s, "B", 0.0); connect(key_s, "ReturnValue", sel_s, "bPickA")
    axis_z = fn(ed, "/Script/Engine.KismetMathLibrary.Add_DoubleDouble", 660, 0); connect(sel_w, "ReturnValue", axis_z, "A"); connect(sel_s, "ReturnValue", axis_z, "B")

    # 2. 移动位移计算 (Sweep=True 启用物理滑动)
    mul_x = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 880, -200); connect(axis_x, "ReturnValue", mul_x, "A"); set_value(mul_x, "B", 420.0)
    mul_z = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 880, 0);    connect(axis_z, "ReturnValue", mul_z, "A"); set_value(mul_z, "B", 420.0)

    move_vec = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 1100, -100)
    connect(mul_x, "ReturnValue", move_vec, "X"); set_value(move_vec, "Y", 0.0); connect(mul_z, "ReturnValue", move_vec, "Z")

    delta_mv = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_VectorFloat", 1320, -100)
    connect(move_vec, "ReturnValue", delta_mv, "A"); connect(tick, "DeltaSeconds", delta_mv, "B")

    move_act = fn(ed, "/Script/Engine.Actor.K2_AddActorWorldOffset", 1540, -100)
    set_value(move_act, "bSweep", "true")
    connect(tick, "then", move_act, "execute")
    connect(delta_mv, "ReturnValue", move_act, "DeltaLocation")

    # 3. 移动判定
    cmp_x = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_DoubleDouble", 880, -320); connect(axis_x, "ReturnValue", cmp_x, "A"); set_value(cmp_x, "B", 0.0)
    cmp_z = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_DoubleDouble", 880, 100);  connect(axis_z, "ReturnValue", cmp_z, "A"); set_value(cmp_z, "B", 0.0)
    is_moving = fn(ed, "/Script/Engine.KismetMathLibrary.BooleanOR", 1100, -20); connect(cmp_x, "ReturnValue", is_moving, "A"); connect(cmp_z, "ReturnValue", is_moving, "B")

    get_comp = fn(ed, "/Script/Engine.Actor.GetComponentByClass", 1540, -260)
    set_value(get_comp, "ComponentClass", "Class'/Script/Paper2D.PaperFlipbookComponent'")

    # 4. 射击分支 (J 键按下单发触发: 永远只向屏幕上方怪物群发射)
    br_shoot = ed.add_branch_node(); br_shoot.set_node_pos(unreal.IntPoint(1760, 0))
    connect(move_act, "then", br_shoot, "execute")
    connect(key_j, "ReturnValue", br_shoot, "Condition")

    get_loc = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 1760, -200)

    # 【唯一射击逻辑: 永远朝向屏幕上方 +Z 开火】
    set_fb_atk_up = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2000, -200)
    if fb_atk_up: set_value(set_fb_atk_up, "NewFlipbook", f"PaperFlipbook'{fb_atk_up.get_path_name()}'")
    connect(br_shoot, "then", set_fb_atk_up, "execute"); connect(get_comp, "ReturnValue", set_fb_atk_up, "self")

    # 枪口: 屏幕上方完全脱离安全区 (0, 0, +95) -> 彻底高出头顶 25 单位，绝不覆盖身体!
    muzzle_u_rel = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 2220, -100)
    set_value(muzzle_u_rel, "X", 0.0); set_value(muzzle_u_rel, "Y", 0.0); set_value(muzzle_u_rel, "Z", 95.0)
    muzzle_u_w = fn(ed, "/Script/Engine.KismetMathLibrary.Add_VectorVector", 2440, -160)
    connect(get_loc, "ReturnValue", muzzle_u_w, "A"); connect(muzzle_u_rel, "ReturnValue", muzzle_u_w, "B")
    rot_u = fn(ed, "/Script/Engine.KismetMathLibrary.MakeRotator", 2440, -40)
    set_value(rot_u, "Pitch", 90.0); set_value(rot_u, "Yaw", 0.0); set_value(rot_u, "Roll", 0.0) # Pitch=90 唯一向上飞!
    trans_u = fn(ed, "/Script/Engine.KismetMathLibrary.MakeTransform", 2660, -100)
    connect(muzzle_u_w, "ReturnValue", trans_u, "Location"); connect(rot_u, "ReturnValue", trans_u, "Rotation"); set_value(trans_u, "Scale", "1,1,1")

    spawn_u = fn(ed, "/Script/Engine.GameplayStatics.BeginDeferredActorSpawnFromClass", 2880, -200)
    set_value(spawn_u, "ActorClass", "Class'/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase.BP_ProjectileBase_C'")
    connect(set_fb_atk_up, "then", spawn_u, "execute"); connect(trans_u, "ReturnValue", spawn_u, "SpawnTransform")
    finish_u = fn(ed, "/Script/Engine.GameplayStatics.FinishSpawningActor", 3140, -200)
    connect(spawn_u, "then", finish_u, "execute"); connect(spawn_u, "ReturnValue", finish_u, "Actor"); connect(trans_u, "ReturnValue", finish_u, "SpawnTransform")

    # 5. 非射击状态 (Shooting = False): 奔跑与待机状态机
    br_moving = ed.add_branch_node(); br_moving.set_node_pos(unreal.IntPoint(2000, 300))
    connect(br_shoot, "else", br_moving, "execute"); connect(is_moving, "ReturnValue", br_moving, "Condition")

    # 向上走 (W)
    br_run_w = ed.add_branch_node(); br_run_w.set_node_pos(unreal.IntPoint(2220, 640))
    connect(br_moving, "then", br_run_w, "execute"); connect(key_w, "ReturnValue", br_run_w, "Condition")
    set_fb_run_w = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2440, 600)
    if fb_run_up: set_value(set_fb_run_w, "NewFlipbook", f"PaperFlipbook'{fb_run_up.get_path_name()}'")
    connect(br_run_w, "then", set_fb_run_w, "execute"); connect(get_comp, "ReturnValue", set_fb_run_w, "self")

    # 向下走 (S)
    br_run_s = ed.add_branch_node(); br_run_s.set_node_pos(unreal.IntPoint(2440, 700))
    connect(br_run_w, "else", br_run_s, "execute"); connect(key_s, "ReturnValue", br_run_s, "Condition")
    set_fb_run_s = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2660, 660)
    if fb_run_down: set_value(set_fb_run_s, "NewFlipbook", f"PaperFlipbook'{fb_run_down.get_path_name()}'")
    connect(br_run_s, "then", set_fb_run_s, "execute"); connect(get_comp, "ReturnValue", set_fb_run_s, "self")

    # 侧向走 (A 或 D)
    set_fb_run_side = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2660, 760)
    if fb_run_left: set_value(set_fb_run_side, "NewFlipbook", f"PaperFlipbook'{fb_run_left.get_path_name()}'")
    connect(br_run_s, "else", set_fb_run_side, "execute"); connect(get_comp, "ReturnValue", set_fb_run_side, "self")

    # 动态切换左右 ScaleX (按 D 向右镜像 -0.5, 按 A 向左正常 0.5)
    sel_run_sc = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 2880, 840)
    set_value(sel_run_sc, "A", -0.5); set_value(sel_run_sc, "B", 0.5); connect(key_d, "ReturnValue", sel_run_sc, "bPickA")
    make_run_sc = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 3100, 840)
    connect(sel_run_sc, "ReturnValue", make_run_sc, "X"); set_value(make_run_sc, "Y", 0.5); set_value(make_run_sc, "Z", 0.5)

    br_is_side_move = ed.add_branch_node(); br_is_side_move.set_node_pos(unreal.IntPoint(2880, 760))
    connect(set_fb_run_side, "then", br_is_side_move, "execute"); connect(cmp_x, "ReturnValue", br_is_side_move, "Condition")
    set_sc_run = fn(ed, "/Script/Engine.SceneComponent.SetRelativeScale3D", 3100, 760)
    connect(br_is_side_move, "then", set_sc_run, "execute"); connect(get_comp, "ReturnValue", set_sc_run, "self")
    connect(make_run_sc, "ReturnValue", set_sc_run, "NewScale3D")

    # 待机中 (Moving = False)
    get_curr_fb = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.GetFlipbook", 2220, 960)
    connect(get_comp, "ReturnValue", get_curr_fb, "self")

    is_down_r = fn(ed, "/Script/Engine.KismetMathLibrary.EqualEqual_ObjectObject", 2440, 920); connect(get_curr_fb, "ReturnValue", is_down_r, "A")
    if fb_run_down: set_value(is_down_r, "B", f"PaperFlipbook'{fb_run_down.get_path_name()}'")
    is_down_i = fn(ed, "/Script/Engine.KismetMathLibrary.EqualEqual_ObjectObject", 2440, 980); connect(get_curr_fb, "ReturnValue", is_down_i, "A")
    if fb_idle_down: set_value(is_down_i, "B", f"PaperFlipbook'{fb_idle_down.get_path_name()}'")
    is_keep_down = fn(ed, "/Script/Engine.KismetMathLibrary.BooleanOR", 2660, 950); connect(is_down_r, "ReturnValue", is_keep_down, "A"); connect(is_down_i, "ReturnValue", is_keep_down, "B")

    br_idle_down = ed.add_branch_node(); br_idle_down.set_node_pos(unreal.IntPoint(2880, 920))
    connect(br_moving, "else", br_idle_down, "execute"); connect(is_keep_down, "ReturnValue", br_idle_down, "Condition")
    set_fb_idle_down = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 3100, 920)
    if fb_idle_down: set_value(set_fb_idle_down, "NewFlipbook", f"PaperFlipbook'{fb_idle_down.get_path_name()}'")
    connect(br_idle_down, "then", set_fb_idle_down, "execute"); connect(get_comp, "ReturnValue", set_fb_idle_down, "self")

    # 默认回落向上待机 (朝向怪物)
    set_fb_idle_up = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 3100, 1040)
    if fb_idle_up: set_value(set_fb_idle_up, "NewFlipbook", f"PaperFlipbook'{fb_idle_up.get_path_name()}'")
    connect(br_idle_down, "else", set_fb_idle_up, "execute"); connect(get_comp, "ReturnValue", set_fb_idle_up, "self")

    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    print("✅ BP_Player_Medic 视口精准重构完成！")

def ensure_player_in_world():
    print("🌍 [3/3] 检查并确保玩家出生点在屏幕正下方中央道路上 (X=0, Y=0, Z=-480)...")
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
    if not world:
        return

    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    has_ps = False
    for a in actors:
        if a.get_actor_label().startswith("PlayerStart"):
            a.set_actor_location(unreal.Vector(0.0, 0.0, -480.0), sweep=False, teleport=True)
            a.set_actor_rotation(unreal.Rotator(0.0, 0.0, 0.0), teleport_physics=True)
            has_ps = True
            print("  已校准 PlayerStart 到 (0, 0, -480)")

    if not has_ps:
        ps = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(0.0, 0.0, -480.0), unreal.Rotator(0.0, 0.0, 0.0))
        ps.set_actor_label("PlayerStart")
        print("  已新建 PlayerStart 到 (0, 0, -480)")

    unreal.EditorLoadingAndSavingUtils.save_map(world, MAP_PATH)
    ASSETS.save_directory(GEN, only_if_is_dirty=False, recursive=True)
    ASSETS.save_directory("/Game/Blueprints", only_if_is_dirty=False, recursive=True)
    print("✅ 地图与资产保存完成！")

def main():
    clean_and_configure_bullet()
    rebuild_player_medic_clean()
    ensure_player_in_world()
    print("\n🎯 GROUND_TRUTH_DEFINITIVE_FIX_COMPLETED")

if __name__ == "__main__":
    main()
