# -*- coding: utf-8 -*-
"""
UE5.8 2D 竖屏游戏: 胶囊体体积适配、发射朝向锁存与子弹物理终极根治
===================================================================
彻底解决“向右射击 子弹向左”与“胶囊体体积碰撞反弹”的终极方案:

1. 玩家胶囊体体积安全发射线 (R=26, H=36):
   - 向右射击: Muzzle = (Loc.X - 58.0, -15.0, Loc.Z + 6.0), Yaw = 180.0 (世界 -X = 屏幕右)
   - 向左射击: Muzzle = (Loc.X + 58.0, -15.0, Loc.Z + 6.0), Yaw = 0.0   (世界 +X = 屏幕左)
   - 向上射击: Muzzle = (Loc.X,        -15.0, Loc.Z + 58.0), Pitch = 90.0(世界 +Z = 屏幕上)
   - 向下射击: Muzzle = (Loc.X,        -15.0, Loc.Z - 58.0), Pitch = -90.0(世界 -Z = 屏幕下)

2. 朝向状态记忆 (K2_SetActorRotation / K2_GetActorRotation):
   - 移动时: D键 -> SetActorRotation(Yaw=180); A键 -> SetActorRotation(Yaw=0); W键 -> SetActorRotation(Yaw=90); S键 -> SetActorRotation(Yaw=-90)
   - 停止移动时: 不修改 ActorRotation, 永远保留最后朝向
   - 站立射击时: 自动根据 GetActorRotation() 判定朝向, 绝不再发生“停下后向右射击却变成向左”的错乱

3. 子弹 BP_ProjectileBase 物理通道纯净化:
   - 关闭所有 Sprite/Flipbook 碰撞 (NoCollision)
   - 唯一碰撞球 CollisionSphere 设为 OverlapAllDynamic (QueryOnly), 绝不阻挡玩家 Pawn
   - should_bounce = False (禁止反弹)
   - InitialSpeed = 1000.0, MaxSpeed = 1000.0
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

# ==============================================================================
# 1. 清理与配置子弹 BP_ProjectileBase
# ==============================================================================
def clean_and_configure_bullet():
    print("🔫 [1/2] 清理并精准配置 BP_ProjectileBase 物理通道...")
    bp = unreal.load_asset(PROJ_BP_PATH)
    if not bp:
        print("❌ 未找到子弹蓝图！")
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
            obj.set_editor_property("sphere_radius", 12.0)
            obj.set_editor_property("relative_location", unreal.Vector(0.0, 0.0, 0.0))
            obj.set_editor_property("relative_rotation", unreal.Rotator(0.0, 0.0, 0.0))
            try:
                bi = obj.get_editor_property("body_instance")
                bi.set_editor_property("collision_profile_name", "OverlapAllDynamic")
                bi.set_editor_property("collision_enabled", unreal.CollisionEnabled.QUERY_ONLY)
            except Exception as e:
                print(f"  Sphere body_instance: {e}")

        elif isinstance(obj, (unreal.PaperFlipbookComponent, unreal.PaperSpriteComponent)):
            try:
                bi = obj.get_editor_property("body_instance")
                bi.set_editor_property("collision_profile_name", "NoCollision")
                bi.set_editor_property("collision_enabled", unreal.CollisionEnabled.NO_COLLISION)
            except:
                pass
            obj.set_editor_property("relative_location", unreal.Vector(0.0, 0.0, 0.0))
            obj.set_editor_property("relative_rotation", unreal.Rotator(0.0, 0.0, 0.0))
            obj.set_editor_property("relative_scale3d", unreal.Vector(0.4, 0.4, 0.4))
            obj.set_editor_property("translucency_sort_priority", 500)
            if isinstance(obj, unreal.PaperFlipbookComponent) and bullet_fb:
                obj.set_editor_property("source_flipbook", bullet_fb)
                obj.set_editor_property("visible", True)
                obj.set_editor_property("hidden_in_game", False)
            elif isinstance(obj, unreal.PaperSpriteComponent):
                obj.set_editor_property("visible", False)
                obj.set_editor_property("hidden_in_game", True)

        elif isinstance(obj, unreal.ProjectileMovementComponent):
            obj.set_editor_property("initial_speed", 1000.0)
            obj.set_editor_property("max_speed", 1000.0)
            obj.set_editor_property("velocity", unreal.Vector(1000.0, 0.0, 0.0))
            obj.set_editor_property("initial_velocity_in_local_space", True)
            obj.set_editor_property("rotation_follows_velocity", True)
            obj.set_editor_property("should_bounce", False)
            obj.set_editor_property("projectile_gravity_scale", 0.0)

    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    print("✅ BP_ProjectileBase 清洗与物理配置完成！")

# ==============================================================================
# 2. 重构主角 BP_Player_Medic 发射与朝向状态机
# ==============================================================================
def rebuild_player_medic_standard():
    print("🎮 [2/2] 正在重构主角 BP_Player_Medic 发射与朝向状态机...")
    bp = unreal.load_asset(PLAYER_BP_PATH)
    if not bp:
        print("❌ 未找到主角蓝图！")
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
            if fb_idle_down:
                obj.set_editor_property("source_flipbook", fb_idle_down)

    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    tick = ed.find_event_node("ReceiveTick")
    if not tick:
        tick = ed.add_event_node("ReceiveTick")
    tick.set_node_pos(unreal.IntPoint(-200, 0))

    pc = fn(ed, "/Script/Engine.GameplayStatics.GetPlayerController", 0, -200)
    set_value(pc, "PlayerIndex", 0)

    # 1. 采样输入按键 (A, D, W, S, J)
    key_a = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, -250); set_value(key_a, "Key", "A"); connect(pc, "ReturnValue", key_a, "self")
    key_d = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, -150); set_value(key_d, "Key", "D"); connect(pc, "ReturnValue", key_d, "self")
    key_w = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, -50);  set_value(key_w, "Key", "W"); connect(pc, "ReturnValue", key_w, "self")
    key_s = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, 50);   set_value(key_s, "Key", "S"); connect(pc, "ReturnValue", key_s, "self")
    key_j = fn(ed, "/Script/Engine.PlayerController.IsInputKeyDown", 220, 150);  set_value(key_j, "Key", "J"); connect(pc, "ReturnValue", key_j, "self")

    # 坐标系 (Camera Yaw=90): D键向右(-X, -1.0), A键向左(+X, +1.0), W键向上(+Z, +1.0), S键向下(-Z, -1.0)
    sel_a = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, -250); set_value(sel_a, "A", 1.0);  set_value(sel_a, "B", 0.0); connect(key_a, "ReturnValue", sel_a, "bPickA")
    sel_d = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 440, -150); set_value(sel_d, "A", -1.0); set_value(sel_d, "B", 0.0); connect(key_d, "ReturnValue", sel_d, "bPickA")
    axis_x = fn(ed, "/Script/Engine.KismetMathLibrary.Add_DoubleDouble", 660, -200); connect(sel_a, "ReturnValue", axis_x, "A"); connect(sel_d, "ReturnValue", axis_x, "B")

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

    # 3. 移动特征
    cmp_x = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_DoubleDouble", 880, -320); connect(axis_x, "ReturnValue", cmp_x, "A"); set_value(cmp_x, "B", 0.0)
    cmp_z = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_DoubleDouble", 880, 100);  connect(axis_z, "ReturnValue", cmp_z, "A"); set_value(cmp_z, "B", 0.0)
    is_moving = fn(ed, "/Script/Engine.KismetMathLibrary.BooleanOR", 1100, -20); connect(cmp_x, "ReturnValue", is_moving, "A"); connect(cmp_z, "ReturnValue", is_moving, "B")

    get_comp = fn(ed, "/Script/Engine.Actor.GetComponentByClass", 1540, -260)
    set_value(get_comp, "ComponentClass", "Class'/Script/Paper2D.PaperFlipbookComponent'")

    # 4. 朝向记忆更新:
    # 只有当按 D 键时更新 ActorRotation(Yaw=180); 按 A 键时更新 ActorRotation(Yaw=0)
    # 向上 W 键 -> ActorRotation(Yaw=90); 向下 S 键 -> ActorRotation(Yaw=-90)
    is_up_in    = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 1320, 100); connect(axis_z, "ReturnValue", is_up_in, "A"); set_value(is_up_in, "B", 0.0)
    is_down_in  = fn(ed, "/Script/Engine.KismetMathLibrary.Less_DoubleDouble", 1320, 180);    connect(axis_z, "ReturnValue", is_down_in, "A"); set_value(is_down_in, "B", 0.0)
    is_right_in = fn(ed, "/Script/Engine.KismetMathLibrary.Less_DoubleDouble", 1320, 260);    connect(axis_x, "ReturnValue", is_right_in, "A"); set_value(is_right_in, "B", 0.0)
    is_left_in  = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 1320, 340); connect(axis_x, "ReturnValue", is_left_in, "A"); set_value(is_left_in, "B", 0.0)

    # 状态机节点:
    # 当 is_moving = True 时，更新 Actor Rotation
    br_update_rot = ed.add_branch_node(); br_update_rot.set_node_pos(unreal.IntPoint(1760, -100))
    connect(move_act, "then", br_update_rot, "execute")
    connect(is_moving, "ReturnValue", br_update_rot, "Condition")

    # 计算目标 Yaw:
    # 优先级: W -> 90.0, S -> -90.0, D -> 180.0, A -> 0.0
    yaw_sel_a = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 1540, 440)
    set_value(yaw_sel_a, "A", 0.0); set_value(yaw_sel_a, "B", 180.0); connect(is_left_in, "ReturnValue", yaw_sel_a, "bPickA")

    yaw_sel_d = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 1760, 440)
    set_value(yaw_sel_d, "A", 180.0); connect(yaw_sel_a, "ReturnValue", yaw_sel_d, "B"); connect(is_right_in, "ReturnValue", yaw_sel_d, "bPickA")

    yaw_sel_s = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 1980, 440)
    set_value(yaw_sel_s, "A", -90.0); connect(yaw_sel_d, "ReturnValue", yaw_sel_s, "B"); connect(is_down_in, "ReturnValue", yaw_sel_s, "bPickA")

    yaw_target = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 2200, 440)
    set_value(yaw_target, "A", 90.0); connect(yaw_sel_s, "ReturnValue", yaw_target, "B"); connect(is_up_in, "ReturnValue", yaw_target, "bPickA")

    rot_target = fn(ed, "/Script/Engine.KismetMathLibrary.MakeRotator", 2420, 440)
    set_value(rot_target, "Pitch", 0.0); connect(yaw_target, "ReturnValue", rot_target, "Yaw"); set_value(rot_target, "Roll", 0.0)

    set_actor_rot = fn(ed, "/Script/Engine.Actor.K2_SetActorRotation", 2640, -100)
    connect(br_update_rot, "then", set_actor_rot, "execute")
    connect(rot_target, "ReturnValue", set_actor_rot, "NewRotation")

    # 贴图翻转: 只有明确按 D (向右) 设为 -0.5, 明确按 A (向左) 设为 0.5
    scale_target_x = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 2420, 560)
    set_value(scale_target_x, "A", -0.5); set_value(scale_target_x, "B", 0.5); connect(is_right_in, "ReturnValue", scale_target_x, "bPickA")
    scale_vec = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 2640, 560)
    connect(scale_target_x, "ReturnValue", scale_vec, "X"); set_value(scale_vec, "Y", 0.5); set_value(scale_vec, "Z", 0.5)

    br_update_scale = ed.add_branch_node(); br_update_scale.set_node_pos(unreal.IntPoint(2860, -100))
    connect(set_actor_rot, "then", br_update_scale, "execute")
    connect(cmp_x, "ReturnValue", br_update_scale, "Condition")

    set_sc = fn(ed, "/Script/Engine.SceneComponent.SetRelativeScale3D", 3080, -100)
    connect(br_update_scale, "then", set_sc, "execute")
    connect(get_comp, "ReturnValue", set_sc, "self")
    connect(scale_vec, "ReturnValue", set_sc, "NewScale3D")

    # 5. 射击主分支 (J 键触发)
    br_shoot = ed.add_branch_node(); br_shoot.set_node_pos(unreal.IntPoint(3300, 0))
    # 无论是否移动/更新过朝向，最终都汇入射击判断
    connect(br_update_rot, "else", br_shoot, "execute")
    connect(br_update_scale, "else", br_shoot, "execute")
    connect(set_sc, "then", br_shoot, "execute")
    connect(key_j, "ReturnValue", br_shoot, "Condition")

    # 角色世界坐标与当前记录的 ActorRotation
    get_loc = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 3300, -200)
    get_rot = fn(ed, "/Script/Engine.Actor.K2_GetActorRotation", 3300, -320)
    brk_rot = fn(ed, "/Script/Engine.KismetMathLibrary.BreakRotator", 3520, -320)
    connect(get_rot, "ReturnValue", brk_rot, "InRot")

    # 判定当前朝向:
    # 是否为朝上: is_up_in OR (Yaw > 45 AND Yaw < 135)
    yaw_gt_45 = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 3740, -420); connect(brk_rot, "Yaw", yaw_gt_45, "A"); set_value(yaw_gt_45, "B", 45.0)
    yaw_lt_135 = fn(ed, "/Script/Engine.KismetMathLibrary.Less_DoubleDouble", 3740, -340);   connect(brk_rot, "Yaw", yaw_lt_135, "A"); set_value(yaw_lt_135, "B", 135.0)
    yaw_is_up = fn(ed, "/Script/Engine.KismetMathLibrary.BooleanAND", 3960, -380); connect(yaw_gt_45, "ReturnValue", yaw_is_up, "A"); connect(yaw_lt_135, "ReturnValue", yaw_is_up, "B")
    final_is_up = fn(ed, "/Script/Engine.KismetMathLibrary.BooleanOR", 4180, -380); connect(is_up_in, "ReturnValue", final_is_up, "A"); connect(yaw_is_up, "ReturnValue", final_is_up, "B")

    # 是否为朝下: is_down_in OR (Yaw > -135 AND Yaw < -45)
    yaw_gt_m135 = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 3740, -260); connect(brk_rot, "Yaw", yaw_gt_m135, "A"); set_value(yaw_gt_m135, "B", -135.0)
    yaw_lt_m45 = fn(ed, "/Script/Engine.KismetMathLibrary.Less_DoubleDouble", 3740, -180);     connect(brk_rot, "Yaw", yaw_lt_m45, "A"); set_value(yaw_lt_m45, "B", -45.0)
    yaw_is_down = fn(ed, "/Script/Engine.KismetMathLibrary.BooleanAND", 3960, -220); connect(yaw_gt_m135, "ReturnValue", yaw_is_down, "A"); connect(yaw_lt_m45, "ReturnValue", yaw_is_down, "B")
    final_is_down = fn(ed, "/Script/Engine.KismetMathLibrary.BooleanOR", 4180, -220); connect(is_down_in, "ReturnValue", final_is_down, "A"); connect(yaw_is_down, "ReturnValue", final_is_down, "B")

    # 是否为朝右: is_right_in OR (Yaw > 135 OR Yaw < -135)
    yaw_gt_135 = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 3740, -100); connect(brk_rot, "Yaw", yaw_gt_135, "A"); set_value(yaw_gt_135, "B", 135.0)
    yaw_lt_neg135 = fn(ed, "/Script/Engine.KismetMathLibrary.Less_DoubleDouble", 3740, -20);   connect(brk_rot, "Yaw", yaw_lt_neg135, "A"); set_value(yaw_lt_neg135, "B", -135.0)
    yaw_is_right = fn(ed, "/Script/Engine.KismetMathLibrary.BooleanOR", 3960, -60); connect(yaw_gt_135, "ReturnValue", yaw_is_right, "A"); connect(yaw_lt_neg135, "ReturnValue", yaw_is_right, "B")
    final_is_right = fn(ed, "/Script/Engine.KismetMathLibrary.BooleanOR", 4180, -60); connect(is_right_in, "ReturnValue", final_is_right, "A"); connect(yaw_is_right, "ReturnValue", final_is_right, "B")

    # ==================== 射击分支 (Shooting = True) ====================
    # [分支 1: 向上射击]
    br_shoot_up = ed.add_branch_node(); br_shoot_up.set_node_pos(unreal.IntPoint(4400, -200))
    connect(br_shoot, "then", br_shoot_up, "execute"); connect(final_is_up, "ReturnValue", br_shoot_up, "Condition")

    set_fb_atk_up = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 4620, -260)
    if fb_atk_up: set_value(set_fb_atk_up, "NewFlipbook", f"PaperFlipbook'{fb_atk_up.get_path_name()}'")
    connect(br_shoot_up, "then", set_fb_atk_up, "execute"); connect(get_comp, "ReturnValue", set_fb_atk_up, "self")

    # 枪口: 头顶外侧远离胶囊体安全距离 (0, -15, +58)
    muzzle_up_rel = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 4620, -140)
    set_value(muzzle_up_rel, "X", 0.0); set_value(muzzle_up_rel, "Y", -15.0); set_value(muzzle_up_rel, "Z", 58.0)
    muzzle_up_w = fn(ed, "/Script/Engine.KismetMathLibrary.Add_VectorVector", 4840, -200)
    connect(get_loc, "ReturnValue", muzzle_up_w, "A"); connect(muzzle_up_rel, "ReturnValue", muzzle_up_w, "B")
    rot_up = fn(ed, "/Script/Engine.KismetMathLibrary.MakeRotator", 4840, -80)
    set_value(rot_up, "Pitch", 90.0); set_value(rot_up, "Yaw", 0.0); set_value(rot_up, "Roll", 0.0)
    trans_up = fn(ed, "/Script/Engine.KismetMathLibrary.MakeTransform", 5060, -140)
    connect(muzzle_up_w, "ReturnValue", trans_up, "Location"); connect(rot_up, "ReturnValue", trans_up, "Rotation"); set_value(trans_up, "Scale", "1,1,1")

    spawn_up = fn(ed, "/Script/Engine.GameplayStatics.BeginDeferredActorSpawnFromClass", 5280, -260)
    set_value(spawn_up, "ActorClass", "Class'/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase.BP_ProjectileBase_C'")
    connect(set_fb_atk_up, "then", spawn_up, "execute"); connect(trans_up, "ReturnValue", spawn_up, "SpawnTransform")
    finish_up = fn(ed, "/Script/Engine.GameplayStatics.FinishSpawningActor", 5540, -260)
    connect(spawn_up, "then", finish_up, "execute"); connect(spawn_up, "ReturnValue", finish_up, "Actor"); connect(trans_up, "ReturnValue", finish_up, "SpawnTransform")

    # [分支 2: 向下射击]
    br_shoot_down = ed.add_branch_node(); br_shoot_down.set_node_pos(unreal.IntPoint(4620, -20))
    connect(br_shoot_up, "else", br_shoot_down, "execute"); connect(final_is_down, "ReturnValue", br_shoot_down, "Condition")

    set_fb_atk_down = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 4840, -20)
    if fb_atk_down: set_value(set_fb_atk_down, "NewFlipbook", f"PaperFlipbook'{fb_atk_down.get_path_name()}'")
    connect(br_shoot_down, "then", set_fb_atk_down, "execute"); connect(get_comp, "ReturnValue", set_fb_atk_down, "self")

    # 枪口: 脚底下侧远离胶囊体安全距离 (0, -15, -58)
    muzzle_down_rel = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 4840, 100)
    set_value(muzzle_down_rel, "X", 0.0); set_value(muzzle_down_rel, "Y", -15.0); set_value(muzzle_down_rel, "Z", -58.0)
    muzzle_down_w = fn(ed, "/Script/Engine.KismetMathLibrary.Add_VectorVector", 5060, 40)
    connect(get_loc, "ReturnValue", muzzle_down_w, "A"); connect(muzzle_down_rel, "ReturnValue", muzzle_down_w, "B")
    rot_down = fn(ed, "/Script/Engine.KismetMathLibrary.MakeRotator", 5060, 160)
    set_value(rot_down, "Pitch", -90.0); set_value(rot_down, "Yaw", 0.0); set_value(rot_down, "Roll", 0.0)
    trans_down = fn(ed, "/Script/Engine.KismetMathLibrary.MakeTransform", 5280, 100)
    connect(muzzle_down_w, "ReturnValue", trans_down, "Location"); connect(rot_down, "ReturnValue", trans_down, "Rotation"); set_value(trans_down, "Scale", "1,1,1")

    spawn_down = fn(ed, "/Script/Engine.GameplayStatics.BeginDeferredActorSpawnFromClass", 5500, -20)
    set_value(spawn_down, "ActorClass", "Class'/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase.BP_ProjectileBase_C'")
    connect(set_fb_atk_down, "then", spawn_down, "execute"); connect(trans_down, "ReturnValue", spawn_down, "SpawnTransform")
    finish_down = fn(ed, "/Script/Engine.GameplayStatics.FinishSpawningActor", 5760, -20)
    connect(spawn_down, "then", finish_down, "execute"); connect(spawn_down, "ReturnValue", finish_down, "Actor"); connect(trans_down, "ReturnValue", finish_down, "SpawnTransform")

    # [分支 3: 侧向射击 (向右 / 向左)]
    set_fb_atk_side = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 4840, 280)
    if fb_atk_side: set_value(set_fb_atk_side, "NewFlipbook", f"PaperFlipbook'{fb_atk_side.get_path_name()}'")
    connect(br_shoot_down, "else", set_fb_atk_side, "execute"); connect(get_comp, "ReturnValue", set_fb_atk_side, "self")

    # 当 final_is_right = True (向右):
    #   枪口 X 偏移 = -58.0 (世界 -X = 屏幕右侧, 远离胶囊体 26 边界 32 单位)
    #   子弹 Yaw = 180.0 (沿世界 -X 飞向屏幕右侧)
    # 当 final_is_right = False (向左):
    #   枪口 X 偏移 = +58.0 (世界 +X = 屏幕左侧)
    #   子弹 Yaw = 0.0 (沿世界 +X 飞向屏幕左侧)
    muzzle_x_side = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 5060, 360)
    set_value(muzzle_x_side, "A", -58.0); set_value(muzzle_x_side, "B", 58.0); connect(final_is_right, "ReturnValue", muzzle_x_side, "bPickA")

    yaw_side = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 5060, 460)
    set_value(yaw_side, "A", 180.0); set_value(yaw_side, "B", 0.0); connect(final_is_right, "ReturnValue", yaw_side, "bPickA")

    muzzle_side_rel = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 5280, 360)
    connect(muzzle_x_side, "ReturnValue", muzzle_side_rel, "X"); set_value(muzzle_side_rel, "Y", -15.0); set_value(muzzle_side_rel, "Z", 6.0)

    muzzle_side_w = fn(ed, "/Script/Engine.KismetMathLibrary.Add_VectorVector", 5500, 300)
    connect(get_loc, "ReturnValue", muzzle_side_w, "A"); connect(muzzle_side_rel, "ReturnValue", muzzle_side_w, "B")

    rot_side = fn(ed, "/Script/Engine.KismetMathLibrary.MakeRotator", 5500, 420)
    set_value(rot_side, "Pitch", 0.0); connect(yaw_side, "ReturnValue", rot_side, "Yaw"); set_value(rot_side, "Roll", 0.0)

    trans_side = fn(ed, "/Script/Engine.KismetMathLibrary.MakeTransform", 5720, 360)
    connect(muzzle_side_w, "ReturnValue", trans_side, "Location"); connect(rot_side, "ReturnValue", trans_side, "Rotation"); set_value(trans_side, "Scale", "1,1,1")

    spawn_side = fn(ed, "/Script/Engine.GameplayStatics.BeginDeferredActorSpawnFromClass", 5940, 280)
    set_value(spawn_side, "ActorClass", "Class'/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase.BP_ProjectileBase_C'")
    connect(set_fb_atk_side, "then", spawn_side, "execute"); connect(trans_side, "ReturnValue", spawn_side, "SpawnTransform")
    finish_side = fn(ed, "/Script/Engine.GameplayStatics.FinishSpawningActor", 6200, 280)
    connect(spawn_side, "then", finish_side, "execute"); connect(spawn_side, "ReturnValue", finish_side, "Actor"); connect(trans_side, "ReturnValue", finish_side, "SpawnTransform")

    # 6. 非射击状态 (Shooting = False): 移动 / 待机动画切换
    br_moving = ed.add_branch_node(); br_moving.set_node_pos(unreal.IntPoint(3520, 600))
    connect(br_shoot, "else", br_moving, "execute"); connect(is_moving, "ReturnValue", br_moving, "Condition")

    # 移动中 (Moving = True)
    br_run_up = ed.add_branch_node(); br_run_up.set_node_pos(unreal.IntPoint(3740, 520))
    connect(br_moving, "then", br_run_up, "execute"); connect(is_up_in, "ReturnValue", br_run_up, "Condition")
    set_fb_run_up = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 3960, 480)
    if fb_run_up: set_value(set_fb_run_up, "NewFlipbook", f"PaperFlipbook'{fb_run_up.get_path_name()}'")
    connect(br_run_up, "then", set_fb_run_up, "execute"); connect(get_comp, "ReturnValue", set_fb_run_up, "self")

    br_run_down = ed.add_branch_node(); br_run_down.set_node_pos(unreal.IntPoint(3960, 600))
    connect(br_run_up, "else", br_run_down, "execute"); connect(is_down_in, "ReturnValue", br_run_down, "Condition")
    set_fb_run_down = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 4180, 560)
    if fb_run_down: set_value(set_fb_run_down, "NewFlipbook", f"PaperFlipbook'{fb_run_down.get_path_name()}'")
    connect(br_run_down, "then", set_fb_run_down, "execute"); connect(get_comp, "ReturnValue", set_fb_run_down, "self")

    set_fb_run_side = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 4180, 660)
    if fb_run_left: set_value(set_fb_run_side, "NewFlipbook", f"PaperFlipbook'{fb_run_left.get_path_name()}'")
    connect(br_run_down, "else", set_fb_run_side, "execute"); connect(get_comp, "ReturnValue", set_fb_run_side, "self")

    # 待机中 (Moving = False): 根据当前动画或 Yaw 平滑切入待机
    get_curr_fb = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.GetFlipbook", 3740, 800)
    connect(get_comp, "ReturnValue", get_curr_fb, "self")

    is_up_r = fn(ed, "/Script/Engine.KismetMathLibrary.EqualEqual_ObjectObject", 3960, 760); connect(get_curr_fb, "ReturnValue", is_up_r, "A")
    if fb_run_up: set_value(is_up_r, "B", f"PaperFlipbook'{fb_run_up.get_path_name()}'")
    is_up_i = fn(ed, "/Script/Engine.KismetMathLibrary.EqualEqual_ObjectObject", 3960, 820); connect(get_curr_fb, "ReturnValue", is_up_i, "A")
    if fb_idle_up: set_value(is_up_i, "B", f"PaperFlipbook'{fb_idle_up.get_path_name()}'")
    is_keep_up = fn(ed, "/Script/Engine.KismetMathLibrary.BooleanOR", 4180, 790); connect(is_up_r, "ReturnValue", is_keep_up, "A"); connect(is_up_i, "ReturnValue", is_keep_up, "B")

    br_idle_up = ed.add_branch_node(); br_idle_up.set_node_pos(unreal.IntPoint(4400, 760))
    connect(br_moving, "else", br_idle_up, "execute"); connect(is_keep_up, "ReturnValue", br_idle_up, "Condition")
    set_fb_idle_up = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 4620, 760)
    if fb_idle_up: set_value(set_fb_idle_up, "NewFlipbook", f"PaperFlipbook'{fb_idle_up.get_path_name()}'")
    connect(br_idle_up, "then", set_fb_idle_up, "execute"); connect(get_comp, "ReturnValue", set_fb_idle_up, "self")

    is_down_r = fn(ed, "/Script/Engine.KismetMathLibrary.EqualEqual_ObjectObject", 3960, 920); connect(get_curr_fb, "ReturnValue", is_down_r, "A")
    if fb_run_down: set_value(is_down_r, "B", f"PaperFlipbook'{fb_run_down.get_path_name()}'")
    is_down_i = fn(ed, "/Script/Engine.KismetMathLibrary.EqualEqual_ObjectObject", 3960, 980); connect(get_curr_fb, "ReturnValue", is_down_i, "A")
    if fb_idle_down: set_value(is_down_i, "B", f"PaperFlipbook'{fb_idle_down.get_path_name()}'")
    is_keep_down = fn(ed, "/Script/Engine.KismetMathLibrary.BooleanOR", 4180, 950); connect(is_down_r, "ReturnValue", is_keep_down, "A"); connect(is_down_i, "ReturnValue", is_keep_down, "B")

    br_idle_down = ed.add_branch_node(); br_idle_down.set_node_pos(unreal.IntPoint(4400, 920))
    connect(br_idle_up, "else", br_idle_down, "execute"); connect(is_keep_down, "ReturnValue", br_idle_down, "Condition")
    set_fb_idle_down = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 4620, 920)
    if fb_idle_down: set_value(set_fb_idle_down, "NewFlipbook", f"PaperFlipbook'{fb_idle_down.get_path_name()}'")
    connect(br_idle_down, "then", set_fb_idle_down, "execute"); connect(get_comp, "ReturnValue", set_fb_idle_down, "self")

    set_fb_idle_side = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 4620, 1040)
    if fb_idle_left: set_value(set_fb_idle_side, "NewFlipbook", f"PaperFlipbook'{fb_idle_left.get_path_name()}'")
    connect(br_idle_down, "else", set_fb_idle_side, "execute"); connect(get_comp, "ReturnValue", set_fb_idle_side, "self")

    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    print("✅ BP_Player_Medic 胶囊体适配与发射系统重构完成！")

def main():
    clean_and_configure_bullet()
    rebuild_player_medic_standard()
    ASSETS.save_directory(GEN, only_if_is_dirty=False, recursive=True)
    ASSETS.save_directory("/Game/Blueprints", only_if_is_dirty=False, recursive=True)
    print("\n🎯 ALL_CAPSULE_AND_BULLET_DIRECTION_FIXES_COMPLETE")

if __name__ == "__main__":
    main()
