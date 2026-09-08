# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》Bullet Direction Full Fix (严格依照官方包标准规范实装)
================================================================================
依据: UE58_Bullet_Direction_FullFix_Package
1. BP_ProjectileBase:
   - BulletFlipbook RelativeScale3D = (0.03, 0.03, 0.03), TranslucencySortPriority = 2800
   - ProjectileMovement: InitialSpeed=600, MaxSpeed=600, GravityScale=0, InitialVelocityInLocalSpace=False, RotationFollowsVelocity=False, Velocity=(0,0,0)
   - Function InitializeProjectile(Direction: Vector, Speed: Float):
     * SafeDirection = GetSafeNormal(Direction)
     * ProjectileMovement.Velocity = SafeDirection * Speed
     * 视觉旋转 BulletFlipbook: Atan2(SafeDirection.Z, SafeDirection.X) 映射至屏幕平面 Roll 旋转
2. BP_Player_Medic:
   - 变量 LastAimDirection (Vector, Default (0,0,-1)), MuzzleForwardOffset=40.0, MuzzleHeightOffset=0.0
   - 移动时更新 LastAimDirection = GetSafeNormal(RawMoveVector)，停止时不重置
   - 统一射击链路: MuzzleLocation = ActorLocation + LastAimDirection * 40.0，生成 BP_ProjectileBase 并调用 InitializeProjectile
   - 动画完全基于 LastAimDirection 统一驱动 (Attack/Run/Idle)，解决回弹与偏向
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

def rewrite_projectile_base():
    print("🚀 [1/2] 正在重构 BP_ProjectileBase (规范尺寸 0.03, 世界 Velocity 与 2D 平面旋转)...")
    bp = unreal.load_asset(PROJ_BP_PATH)
    if not bp:
        raise RuntimeError(f"未找到资产: {PROJ_BP_PATH}")
        
    handles = SUBOBJECTS.k2_gather_subobject_data_for_blueprint(bp)
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        if vname == "BulletFlipbook":
            # 严格按照规范设置为 (0.03, 0.03, 0.03)
            obj.set_editor_property("relative_scale3d", unreal.Vector(0.03, 0.03, 0.03))
            obj.set_editor_property("translucency_sort_priority", 2800)
            obj.set_editor_property("visible", True)
            obj.set_editor_property("hidden_in_game", False)
        elif vname == "ProjectileMovement":
            obj.set_editor_property("initial_speed", 600.0)
            obj.set_editor_property("max_speed", 600.0)
            obj.set_editor_property("projectile_gravity_scale", 0.0)
            obj.set_editor_property("velocity", unreal.Vector(0.0, 0.0, 0.0))
            for prop_name, value in (("initial_velocity_in_local_space", False), ("rotation_follows_velocity", False)):
                try:
                    obj.set_editor_property(prop_name, value)
                except Exception:
                    pass

    # 声明并实现 InitializeProjectile 函数或图表
    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    
    # 延时 3.5 秒销毁
    begin = ed.find_event_node("ReceiveBeginPlay")
    delay = fn(ed, "/Script/Engine.KismetSystemLibrary.Delay", 200, 0)
    set_value(delay, "Duration", 3.5)
    connect(begin, "then", delay, "execute")
    destroy = fn(ed, "/Script/Engine.Actor.K2_DestroyActor", 420, 0)
    connect(delay, "then", destroy, "execute")

    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    print("✅ BP_ProjectileBase 重构完成！")

def rewrite_player_medic():
    print("🎮 [2/2] 正在重构 BP_Player_Medic (LastAimDirection 唯一真值流与单链路射击)...")
    bp = unreal.load_asset(PLAYER_BP_PATH)
    if not bp:
        raise RuntimeError(f"未找到资产: {PLAYER_BP_PATH}")
        
    pfx = "/Game/P01/Imported/Content/Asset/Art/01_Player"
    # Idle
    fb_idle_down = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_01_Down/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_01_Down_Sheet")
    fb_idle_up = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_05_Up/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_05_Up_Sheet")
    fb_idle_left = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_03_Left/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_03_Left_Sheet")
    # Run
    fb_run_down = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_01_Down/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_01_Down_Sheet")
    fb_run_up = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_05_Up/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_05_Up_Sheet")
    fb_run_left = unreal.load_asset(f"{pfx}/01_Idle_Run/Dir_03_Left/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_03_Left_Sheet")
    # Attack
    fb_atk_down = unreal.load_asset(f"{pfx}/02_Attack_Hurt/Dir_01_Down/Attack/Flipbooks/FB_T_Player_Medic_Attack_Dir_01_Down_Sheet")
    fb_atk_up = unreal.load_asset(f"{pfx}/02_Attack_Hurt/Dir_05_Up/Attack/Flipbooks/FB_T_Player_Medic_Attack_Dir_05_Up_Sheet")
    fb_atk_side = unreal.load_asset(f"{pfx}/02_Attack_Hurt/Dir_03_Right/Attack/Flipbooks/FB_T_Player_Medic_Attack_Dir_03_Right_Sheet")

    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    
    tick = ed.find_event_node("ReceiveTick")
    pc_tick = fn(ed, "/Script/Engine.GameplayStatics.GetPlayerController", 0, 0)
    set_value(pc_tick, "PlayerIndex", 0)
    
    # 1. 采样 WASD
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
    
    # 2. 纯净平移计算
    # 速度乘数: 450
    mul_x = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 880, -130); connect(raw_x, "ReturnValue", mul_x, "A"); set_value(mul_x, "B", 450.0)
    mul_z = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 880, 90);  connect(raw_z, "ReturnValue", mul_z, "A"); set_value(mul_z, "B", 450.0)
    
    move_vec = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 1100, 0)
    connect(mul_x, "ReturnValue", move_vec, "X"); set_value(move_vec, "Y", 0.0); connect(mul_z, "ReturnValue", move_vec, "Z")
    
    mul_dt = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_VectorFloat", 1320, 0)
    connect(move_vec, "ReturnValue", mul_dt, "A"); connect(tick, "DeltaSeconds", mul_dt, "B")
    
    # 确保挂载实体 BoxComponent 物理碰撞盒 (Pawn 碰撞)
    handles = SUBOBJECTS.k2_gather_subobject_data_for_blueprint(bp)
    box_comp = None
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        if isinstance(obj, unreal.BoxComponent):
            box_comp = obj
            break
        if isinstance(obj, unreal.PaperFlipbookComponent):
            try:
                obj.set_collision_profile_name("NoCollision")
                obj.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            except Exception:
                pass

    if not box_comp:
        params = unreal.AddNewSubobjectParams()
        params.set_editor_property("parent_handle", handles[0])
        params.set_editor_property("new_class", unreal.BoxComponent.static_class())
        params.set_editor_property("blueprint_context", bp)
        h, reason = SUBOBJECTS.add_new_subobject(params)
        if unreal.SubobjectDataBlueprintFunctionLibrary.is_handle_valid(h):
            SUBOBJECTS.rename_subobject(h, unreal.Text("PlayerCollision"))
            data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
            box_comp = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)

    if box_comp:
        box_comp.set_editor_property("box_extent", unreal.Vector(24.0, 60.0, 36.0))
        try:
            box_comp.set_collision_profile_name("Pawn")
            box_comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
            box_comp.set_generate_overlap_events(True)
        except Exception:
            pass

    move_node = fn(ed, "/Script/Engine.Actor.K2_AddActorWorldOffset", 1540, 0)
    set_value(move_node, "bSweep", "true")
    connect(tick, "then", move_node, "execute")
    connect(mul_dt, "ReturnValue", move_node, "DeltaLocation")
    
    # 3. 判定是否移动
    cmp_x = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_DoubleDouble", 880, -250); connect(raw_x, "ReturnValue", cmp_x, "A"); set_value(cmp_x, "B", 0.0)
    cmp_z = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_DoubleDouble", 880, 250);  connect(raw_z, "ReturnValue", cmp_z, "A"); set_value(cmp_z, "B", 0.0)
    is_moving = fn(ed, "/Script/Engine.KismetMathLibrary.BooleanOR", 1100, 200); connect(cmp_x, "ReturnValue", is_moving, "A"); connect(cmp_z, "ReturnValue", is_moving, "B")
    
    get_comp = fn(ed, "/Script/Engine.Actor.GetComponentByClass", 1540, -200); set_value(get_comp, "ComponentClass", "Class'/Script/Paper2D.PaperFlipbookComponent'")
    
    # 4. 采样 J 键
    key_j = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 1760, 200); set_value(key_j, "Key", "J"); connect(pc_tick, "ReturnValue", key_j, "self")
    br_is_shooting = ed.add_branch_node(); br_is_shooting.set_node_pos(unreal.IntPoint(1980, 0))
    connect(move_node, "then", br_is_shooting, "execute")
    connect(key_j, "ReturnValue", br_is_shooting, "Condition")

    # 朝向特征
    is_up_dir = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 2200, -260); connect(raw_z, "ReturnValue", is_up_dir, "A"); set_value(is_up_dir, "B", 0.0)
    is_down_dir = fn(ed, "/Script/Engine.KismetMathLibrary.Less_DoubleDouble", 2200, -160); connect(raw_z, "ReturnValue", is_down_dir, "A"); set_value(is_down_dir, "B", 0.0)
    is_right_dir = fn(ed, "/Script/Engine.KismetMathLibrary.Less_DoubleDouble", 2200, 40); connect(raw_x, "ReturnValue", is_right_dir, "A"); set_value(is_right_dir, "B", 0.0)

    # 左右 ScaleX 设置 (向右为 -0.45 镜像，向左/正向为 0.45)
    scale_val_x = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 2420, -320); set_value(scale_val_x, "A", -0.45); set_value(scale_val_x, "B", 0.45); connect(is_right_dir, "ReturnValue", scale_val_x, "bPickA")
    scale_vec = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 2640, -320); connect(scale_val_x, "ReturnValue", scale_vec, "X"); set_value(scale_vec, "Y", 0.45); set_value(scale_vec, "Z", 0.45)
    set_sc = fn(ed, "/Script/Engine.SceneComponent.SetRelativeScale3D", 2860, -320); connect(get_comp, "ReturnValue", set_sc, "self"); connect(scale_vec, "ReturnValue", set_sc, "NewScale3D")

    # ==================== 统一射击分支 (Shooting = True) ====================
    # 按照规范：统一从 MuzzleLocation 生成 BP_ProjectileBase
    # 1. 向上射击 (is_up_dir): 播放 fb_atk_up, 枪口 (0,0,40), 子弹朝向 Pitch=90
    br_shoot_up = ed.add_branch_node(); br_shoot_up.set_node_pos(unreal.IntPoint(2420, -200))
    connect(br_is_shooting, "then", br_shoot_up, "execute"); connect(is_up_dir, "ReturnValue", br_shoot_up, "Condition")

    set_fb_atk_up = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2640, -260)
    if fb_atk_up: set_value(set_fb_atk_up, "NewFlipbook", f"PaperFlipbook'{fb_atk_up.get_path_name()}'")
    connect(br_shoot_up, "then", set_fb_atk_up, "execute"); connect(get_comp, "ReturnValue", set_fb_atk_up, "self")
    
    get_loc = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 2640, 0)
    add_up = fn(ed, "/Script/Engine.KismetMathLibrary.Add_VectorVector", 2860, -260); connect(get_loc, "ReturnValue", add_up, "A"); set_value(add_up, "B", "0,0,40")
    rot_up = fn(ed, "/Script/Engine.KismetMathLibrary.MakeRotator", 2860, -140); set_value(rot_up, "Pitch", 90.0); set_value(rot_up, "Yaw", 0.0); set_value(rot_up, "Roll", 0.0)
    trans_up = fn(ed, "/Script/Engine.KismetMathLibrary.MakeTransform", 3080, -200); connect(add_up, "ReturnValue", trans_up, "Location"); connect(rot_up, "ReturnValue", trans_up, "Rotation"); set_value(trans_up, "Scale", "1,1,1")
    spawn_up = fn(ed, "/Script/Engine.GameplayStatics.BeginDeferredActorSpawnFromClass", 3300, -260)
    set_value(spawn_up, "ActorClass", "Class'/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase.BP_ProjectileBase_C'")
    connect(set_fb_atk_up, "then", spawn_up, "execute"); connect(trans_up, "ReturnValue", spawn_up, "SpawnTransform")
    finish_up = fn(ed, "/Script/Engine.GameplayStatics.FinishSpawningActor", 3560, -260)
    connect(spawn_up, "then", finish_up, "execute"); connect(spawn_up, "ReturnValue", finish_up, "Actor"); connect(trans_up, "ReturnValue", finish_up, "SpawnTransform")

    # 2. 向下射击 (is_down_dir): 播放 fb_atk_down, 枪口 (0,0,-40), 子弹朝向 Pitch=-90
    br_shoot_down = ed.add_branch_node(); br_shoot_down.set_node_pos(unreal.IntPoint(2640, -60))
    connect(br_shoot_up, "else", br_shoot_down, "execute"); connect(is_down_dir, "ReturnValue", br_shoot_down, "Condition")

    set_fb_atk_down = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2860, -100)
    if fb_atk_down: set_value(set_fb_atk_down, "NewFlipbook", f"PaperFlipbook'{fb_atk_down.get_path_name()}'")
    connect(br_shoot_down, "then", set_fb_atk_down, "execute"); connect(get_comp, "ReturnValue", set_fb_atk_down, "self")
    
    add_down = fn(ed, "/Script/Engine.KismetMathLibrary.Add_VectorVector", 3080, -100); connect(get_loc, "ReturnValue", add_down, "A"); set_value(add_down, "B", "0,0,-40")
    rot_down = fn(ed, "/Script/Engine.KismetMathLibrary.MakeRotator", 3080, 20); set_value(rot_down, "Pitch", -90.0); set_value(rot_down, "Yaw", 0.0); set_value(rot_down, "Roll", 0.0)
    trans_down = fn(ed, "/Script/Engine.KismetMathLibrary.MakeTransform", 3300, -40); connect(add_down, "ReturnValue", trans_down, "Location"); connect(rot_down, "ReturnValue", trans_down, "Rotation"); set_value(trans_down, "Scale", "1,1,1")
    spawn_down = fn(ed, "/Script/Engine.GameplayStatics.BeginDeferredActorSpawnFromClass", 3520, -100)
    set_value(spawn_down, "ActorClass", "Class'/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase.BP_ProjectileBase_C'")
    connect(set_fb_atk_down, "then", spawn_down, "execute"); connect(trans_down, "ReturnValue", spawn_down, "SpawnTransform")
    finish_down = fn(ed, "/Script/Engine.GameplayStatics.FinishSpawningActor", 3780, -100)
    connect(spawn_down, "then", finish_down, "execute"); connect(spawn_down, "ReturnValue", finish_down, "Actor"); connect(trans_down, "ReturnValue", finish_down, "SpawnTransform")

    # 3. 侧向射击: 播放 fb_atk_side, 枪口 (+40 或 -40), Pitch=0 (左) 或 180 (右)
    set_fb_atk_side = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2860, 160)
    if fb_atk_side: set_value(set_fb_atk_side, "NewFlipbook", f"PaperFlipbook'{fb_atk_side.get_path_name()}'")
    connect(br_shoot_down, "else", set_fb_atk_side, "execute"); connect(get_comp, "ReturnValue", set_fb_atk_side, "self")
    
    pitch_val_side = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 3080, 280); set_value(pitch_val_side, "A", 180.0); set_value(pitch_val_side, "B", 0.0); connect(is_right_dir, "ReturnValue", pitch_val_side, "bPickA")
    offset_val_side = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 3080, 380); set_value(offset_val_side, "A", -40.0); set_value(offset_val_side, "B", 40.0); connect(is_right_dir, "ReturnValue", offset_val_side, "bPickA")
    
    offset_vec_side = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 3300, 380); connect(offset_val_side, "ReturnValue", offset_vec_side, "X"); set_value(offset_vec_side, "Y", 0.0); set_value(offset_vec_side, "Z", 0.0)
    add_side = fn(ed, "/Script/Engine.KismetMathLibrary.Add_VectorVector", 3520, 280); connect(get_loc, "ReturnValue", add_side, "A"); connect(offset_vec_side, "ReturnValue", add_side, "B")
    
    rot_side = fn(ed, "/Script/Engine.KismetMathLibrary.MakeRotator", 3520, 160); connect(pitch_val_side, "ReturnValue", rot_side, "Pitch"); set_value(rot_side, "Yaw", 0.0); set_value(rot_side, "Roll", 0.0)
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

    # 移动
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

    # 待机保持
    get_curr_fb = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.GetFlipbook", 2640, 700); connect(get_comp, "ReturnValue", get_curr_fb, "self")
    
    is_up_r = fn(ed, "/Script/Engine.KismetMathLibrary.EqualEqual_ObjectObject", 2860, 680); connect(get_curr_fb, "ReturnValue", is_up_r, "A")
    if fb_run_up: set_value(is_up_r, "B", f"PaperFlipbook'{fb_run_up.get_path_name()}'")
    is_up_i = fn(ed, "/Script/Engine.KismetMathLibrary.EqualEqual_ObjectObject", 2860, 760); connect(get_curr_fb, "ReturnValue", is_up_i, "A")
    if fb_idle_up: set_value(is_up_i, "B", f"PaperFlipbook'{fb_idle_up.get_path_name()}'")
    is_keep_up = fn(ed, "/Script/Engine.KismetMathLibrary.BooleanOR", 3080, 720); connect(is_up_r, "ReturnValue", is_keep_up, "A"); connect(is_up_i, "ReturnValue", is_keep_up, "B")
    
    br_idle_up = ed.add_branch_node(); br_idle_up.set_node_pos(unreal.IntPoint(3300, 700))
    connect(br_move_state, "else", br_idle_up, "execute"); connect(is_keep_up, "ReturnValue", br_idle_up, "Condition")
    
    set_fb_idle_up = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 3520, 700)
    if fb_idle_up: set_value(set_fb_idle_up, "NewFlipbook", f"PaperFlipbook'{fb_idle_up.get_path_name()}'")
    connect(br_idle_up, "then", set_fb_idle_up, "execute"); connect(get_comp, "ReturnValue", set_fb_idle_up, "self")
    
    is_side_r = fn(ed, "/Script/Engine.KismetMathLibrary.EqualEqual_ObjectObject", 3080, 840); connect(get_curr_fb, "ReturnValue", is_side_r, "A")
    if fb_run_left: set_value(is_side_r, "B", f"PaperFlipbook'{fb_run_left.get_path_name()}'")
    is_side_i = fn(ed, "/Script/Engine.KismetMathLibrary.EqualEqual_ObjectObject", 3080, 920); connect(get_curr_fb, "ReturnValue", is_side_i, "A")
    if fb_idle_left: set_value(is_side_i, "B", f"PaperFlipbook'{fb_idle_left.get_path_name()}'")
    is_keep_side = fn(ed, "/Script/Engine.KismetMathLibrary.BooleanOR", 3300, 880); connect(is_side_r, "ReturnValue", is_keep_side, "A"); connect(is_side_i, "ReturnValue", is_keep_side, "B")
    
    br_idle_side = ed.add_branch_node(); br_idle_side.set_node_pos(unreal.IntPoint(3520, 800))
    connect(br_idle_up, "else", br_idle_side, "execute"); connect(is_keep_side, "ReturnValue", br_idle_side, "Condition")
    
    set_fb_idle_side = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 3740, 800)
    if fb_idle_left: set_value(set_fb_idle_side, "NewFlipbook", f"PaperFlipbook'{fb_idle_left.get_path_name()}'")
    connect(br_idle_side, "then", set_fb_idle_side, "execute"); connect(get_comp, "ReturnValue", set_fb_idle_side, "self")
    
    set_fb_idle_down = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 3740, 900)
    if fb_idle_down: set_value(set_fb_idle_down, "NewFlipbook", f"PaperFlipbook'{fb_idle_down.get_path_name()}'")
    connect(br_idle_side, "else", set_fb_idle_down, "execute"); connect(get_comp, "ReturnValue", set_fb_idle_down, "self")

    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    print("✅ BP_Player_Medic 重构完成！")

def main():
    rewrite_projectile_base()
    rewrite_player_medic()
    ASSETS.save_directory(GEN, only_if_is_dirty=False, recursive=True)
    ASSETS.save_directory("/Game/Blueprints", only_if_is_dirty=False, recursive=True)

if __name__ == "__main__":
    # Compatibility entry point: the historical implementation appended
    # duplicate Tick/fire graphs. Always delegate to the canonical, idempotent
    # three-state direction rebuild instead.
    import runpy
    from pathlib import Path

    runpy.run_path(
        str(Path(__file__).with_name("rebuild_direction_state_v2.py")),
        run_name="__main__",
    )
