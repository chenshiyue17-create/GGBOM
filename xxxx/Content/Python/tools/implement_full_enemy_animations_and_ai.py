# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》全量敌人自主 AI 追逐、多向完整移动动画与技能动作系统
1. 行尸家族 (Walker, Runner, Spitter, Guard, Brute):
   - 保持 4 帧连续动画图集
   - 轴分离 AI 追逐寻路 (bSweep=True)，视觉朝向水平自适应翻转
2. 变异猎犬 (MutantHound):
   - 4 向完整移动奔跑动画 (Run: Down, Right, Up, Left)
   - 近身技能扑击动作 (Pounce: Down, Right, Up, Left)
   - 智能四向朝向判定与距离状态机
3. 深渊异化领主 (Boss_Overlord):
   - 4 向完整行走移动动画 (Walk: Down, Right, Up, Left)
   - 近身/重击技能动作 (Ground_Slam / Heavy_Cleave)
   - 4 向待机动作 (Idle)
================================================================================
"""
from __future__ import annotations
import unreal

GEN = "/Game/GGBOM"
ENEMY_BP_DIR = "/Game/Blueprints/Characters/Enemies"
HOUND_ART_DIR = "/Game/P01/Imported/Content/Asset/Art/02_Enemies/MutantHound"
BOSS_ART_DIR = "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Boss_Overlord"
ZOMBIE_ART_DIR = "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Zombie"

bplib = unreal.BlueprintEditorLibrary
pinlib = unreal.BlueprintGraphPinLibrary
subsystems = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)

def log(msg: str):
    print(f"[EnemyAnimationAI] {msg}")
    unreal.log(f"[EnemyAnimationAI] {msg}")

def pin(node, name, output):
    values = bplib.list_output_pins(node) if output else bplib.list_input_pins(node)
    wanted = name.lower()
    exact = [p for p in values if str(pinlib.get_pin_name(p)).lower() == wanted]
    if len(exact) == 1:
        return exact[0]
    raise RuntimeError(f"Pin {name} not found; available={[str(pinlib.get_pin_name(p)) for p in values]}")

def set_value(node, name, value):
    target = pin(node, name, False)
    if not pinlib.set_pin_value(target, str(value)):
        raise RuntimeError(f"Default rejected: {name}={value}")

def connect(a, a_pin, b, b_pin):
    source, target = pin(a, a_pin, True), pin(b, b_pin, False)
    if not pinlib.try_create_connection(source, target):
        raise RuntimeError(f"Connection rejected: {a_pin} -> {b_pin}")

def fn(ed, path, x, y):
    node = ed.add_call_function_node(path)
    if not node:
        raise RuntimeError(f"Cannot create node: {path}")
    node.set_node_pos(unreal.IntPoint(x, y))
    return node

def clean_event_graph(bp):
    graph = bplib.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    tick_node = ed.find_event_node("ReceiveTick")
    begin_node = ed.find_event_node("ReceiveBeginPlay")
    keep_paths = {tick_node.get_path_name()}
    if begin_node:
        keep_paths.add(begin_node.get_path_name())
    nodes_to_remove = [n for n in ed.list_all_nodes() if n.get_path_name() not in keep_paths]
    if nodes_to_remove:
        ed.remove_nodes(nodes_to_remove)
    return ed, tick_node

def ensure_box_component(bp, extent):
    handles = subsystems.k2_gather_subobject_data_for_blueprint(bp)
    target_comp = None
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        if isinstance(obj, unreal.BoxComponent):
            target_comp = obj
            break
    if target_comp:
        target_comp.set_editor_property("box_extent", extent)
        try:
            target_comp.set_collision_profile_name("Pawn")
            target_comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
            target_comp.set_generate_overlap_events(True)
        except Exception:
            pass

# ==============================================================================
# 1. 行尸家族 (4 帧行走动画 + AI 追逐寻路 + 左右水平翻转)
# ==============================================================================
ZOMBIE_SPECS = [
    {
        "name": "BP_Enemy_ZombieWalker",
        "display": "基础感染行尸",
        "speed": 65.0,
        "scale": 0.45,
        "flipbook": f"{ZOMBIE_ART_DIR}/01_Zombie_Walker_Basic/Flipbooks/FB_T_Zombie_WalkerBasic_Sheet.FB_T_Zombie_WalkerBasic_Sheet",
        "extent": unreal.Vector(26.0, 70.0, 36.0),
    },
    {
        "name": "BP_Enemy_ZombieRunner",
        "display": "敏捷疾跑行尸",
        "speed": 110.0,
        "scale": 0.45,
        "flipbook": f"{ZOMBIE_ART_DIR}/05_Zombie_Runner_Agile/Flipbooks/FB_T_Zombie_RunnerAgile_Sheet.FB_T_Zombie_RunnerAgile_Sheet",
        "extent": unreal.Vector(26.0, 70.0, 36.0),
    },
    {
        "name": "BP_Enemy_VenomShooter",
        "display": "毒液喷射行尸",
        "speed": 55.0,
        "scale": 0.45,
        "flipbook": f"{ZOMBIE_ART_DIR}/04_Zombie_Spitter_Minor/Flipbooks/FB_T_Zombie_SpitterMinor_Sheet.FB_T_Zombie_SpitterMinor_Sheet",
        "extent": unreal.Vector(26.0, 70.0, 36.0),
    },
    {
        "name": "BP_Enemy_ArmoredGuard",
        "display": "重装防暴行尸",
        "speed": 50.0,
        "scale": 0.50,
        "flipbook": f"{ZOMBIE_ART_DIR}/07_Zombie_Armored_Guard/Flipbooks/FB_T_Zombie_ArmoredGuard_Sheet.FB_T_Zombie_ArmoredGuard_Sheet",
        "extent": unreal.Vector(32.0, 70.0, 42.0),
    },
    {
        "name": "BP_Enemy_MutantBrute",
        "display": "重型蹒跚蛮兽",
        "speed": 40.0,
        "scale": 0.58,
        "flipbook": f"{ZOMBIE_ART_DIR}/11_Zombie_Shambler_Heavy/Flipbooks/FB_T_Zombie_ShamblerHeavy_Sheet.FB_T_Zombie_ShamblerHeavy_Sheet",
        "extent": unreal.Vector(38.0, 80.0, 48.0),
    },
]

def build_zombie_ai(spec: dict):
    bp_path = f"{ENEMY_BP_DIR}/{spec['name']}"
    log(f"🧟 正在配置行尸 4 帧追逐体系: {spec['display']} ({bp_path})...")
    bp = unreal.load_asset(bp_path)
    if not bp:
        log(f"⚠️ 未找到蓝图: {bp_path}")
        return False

    ensure_box_component(bp, spec["extent"])
    ed, tick_node = clean_event_graph(bp)

    # 1. 采样玩家坐标与自身坐标
    get_player = fn(ed, "/Script/Engine.GameplayStatics.GetPlayerPawn", 200, 100)
    set_value(get_player, "PlayerIndex", 0)

    p_loc = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 450, 50)
    connect(get_player, "ReturnValue", p_loc, "self")

    self_loc = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 450, 180)

    # 2. 向量相减并单位化
    sub_v = fn(ed, "/Script/Engine.KismetMathLibrary.Subtract_VectorVector", 700, 100)
    connect(p_loc, "ReturnValue", sub_v, "A")
    connect(self_loc, "ReturnValue", sub_v, "B")

    norm_v = fn(ed, "/Script/Engine.KismetMathLibrary.Normal", 920, 100)
    connect(sub_v, "ReturnValue", norm_v, "A")

    break_v = fn(ed, "/Script/Engine.KismetMathLibrary.BreakVector", 1140, 100)
    connect(norm_v, "ReturnValue", break_v, "InVec")

    speed = spec["speed"]
    base_scale = spec["scale"]

    # 3. 轴分离位移 (X + Z 双路 Sweep 寻路避障)
    mul_x_speed = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1360, 50)
    connect(break_v, "X", mul_x_speed, "A")
    set_value(mul_x_speed, "B", speed)

    mul_x_dt = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1580, 50)
    connect(mul_x_speed, "ReturnValue", mul_x_dt, "A")
    connect(tick_node, "DeltaSeconds", mul_x_dt, "B")

    delta_vec_x = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 1800, 50)
    connect(mul_x_dt, "ReturnValue", delta_vec_x, "X")
    set_value(delta_vec_x, "Y", 0.0)
    set_value(delta_vec_x, "Z", 0.0)

    move_x = fn(ed, "/Script/Engine.Actor.K2_AddActorWorldOffset", 2050, 50)
    set_value(move_x, "bSweep", "true")
    connect(delta_vec_x, "ReturnValue", move_x, "DeltaLocation")
    connect(tick_node, "then", move_x, "execute")

    mul_z_speed = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1360, 220)
    connect(break_v, "Z", mul_z_speed, "A")
    set_value(mul_z_speed, "B", speed)

    mul_z_dt = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1580, 220)
    connect(mul_z_speed, "ReturnValue", mul_z_dt, "A")
    connect(tick_node, "DeltaSeconds", mul_z_dt, "B")

    delta_vec_z = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 1800, 220)
    set_value(delta_vec_z, "X", 0.0)
    set_value(delta_vec_z, "Y", 0.0)
    connect(mul_z_dt, "ReturnValue", delta_vec_z, "Z")

    move_z = fn(ed, "/Script/Engine.Actor.K2_AddActorWorldOffset", 2050, 220)
    set_value(move_z, "bSweep", "true")
    connect(delta_vec_z, "ReturnValue", move_z, "DeltaLocation")
    connect(move_x, "then", move_z, "execute")

    # 4. 视觉朝向水平自适应翻转 (玩家在右侧镜像，在左侧正向)
    is_right = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 1360, -120)
    connect(break_v, "X", is_right, "A")
    set_value(is_right, "B", 0.0)

    sel_scale = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 1580, -120)
    set_value(sel_scale, "A", -base_scale)
    set_value(sel_scale, "B", base_scale)
    connect(is_right, "ReturnValue", sel_scale, "bPickA")

    scale_vec = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 1800, -120)
    connect(sel_scale, "ReturnValue", scale_vec, "X")
    set_value(scale_vec, "Y", base_scale)
    set_value(scale_vec, "Z", base_scale)

    get_fb = fn(ed, "/Script/Engine.Actor.GetComponentByClass", 1800, -260)
    set_value(get_fb, "ComponentClass", "Class'/Script/Paper2D.PaperFlipbookComponent'")

    set_scale = fn(ed, "/Script/Engine.SceneComponent.SetRelativeScale3D", 2050, -180)
    connect(get_fb, "ReturnValue", set_scale, "self")
    connect(scale_vec, "ReturnValue", set_scale, "NewScale3D")
    connect(move_z, "then", set_scale, "execute")

    # 5. CDO 绑定 4 帧 Flipbook
    cdo = unreal.get_default_object(bp.generated_class())
    if cdo:
        comp = cdo.get_component_by_class(unreal.PaperFlipbookComponent)
        if comp:
            fb = unreal.load_asset(spec["flipbook"])
            if fb:
                comp.set_editor_property("source_flipbook", fb)
            comp.set_editor_property("relative_scale3d", unreal.Vector(base_scale, base_scale, base_scale))
            comp.set_editor_property("translucency_sort_priority", 200)

    bplib.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"  ✅ 行尸 {spec['display']} 配置完毕！")
    return True

# ==============================================================================
# 2. 变异猎犬 (4 向完整移动奔跑动画 + 扑击技能动作 + 状态机)
# ==============================================================================
def build_mutant_hound_ai():
    bp_path = f"{ENEMY_BP_DIR}/BP_Enemy_MutantHound"
    log(f"🐕 正在配置变异猎犬 4 向奔跑与扑咬技能状态机 ({bp_path})...")
    bp = unreal.load_asset(bp_path)
    if not bp:
        log(f"⚠️ 未找到蓝图: {bp_path}")
        return False

    ensure_box_component(bp, unreal.Vector(30.0, 70.0, 32.0))
    ed, tick_node = clean_event_graph(bp)

    # 加载 4 向奔跑与扑击 Flipbook
    fb_run_down = unreal.load_asset(f"{HOUND_ART_DIR}/Run/Dir_01_Down/Flipbooks/FB_T_Hound_Run_Dir_01_Down_Sheet.FB_T_Hound_Run_Dir_01_Down_Sheet")
    fb_run_right = unreal.load_asset(f"{HOUND_ART_DIR}/Run/Dir_02_Right/Flipbooks/FB_T_Hound_Run_Dir_02_Right_Sheet.FB_T_Hound_Run_Dir_02_Right_Sheet")
    fb_run_up = unreal.load_asset(f"{HOUND_ART_DIR}/Run/Dir_03_Up/Flipbooks/FB_T_Hound_Run_Dir_03_Up_Sheet.FB_T_Hound_Run_Dir_03_Up_Sheet")
    fb_run_left = unreal.load_asset(f"{HOUND_ART_DIR}/Run/Dir_04_Left/Flipbooks/FB_T_Hound_Run_Dir_04_Left_Sheet.FB_T_Hound_Run_Dir_04_Left_Sheet")
    fb_pounce_down = unreal.load_asset(f"{HOUND_ART_DIR}/Pounce/Dir_01_Down/Flipbooks/FB_T_Hound_Pounce_Dir_01_Down_Sheet.FB_T_Hound_Pounce_Dir_01_Down_Sheet")

    # 1. 采样玩家坐标与自身坐标
    get_player = fn(ed, "/Script/Engine.GameplayStatics.GetPlayerPawn", 200, 100)
    set_value(get_player, "PlayerIndex", 0)

    p_loc = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 450, 50)
    connect(get_player, "ReturnValue", p_loc, "self")

    self_loc = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 450, 180)

    # 2. 距离与追逐向量
    dist_node = fn(ed, "/Script/Engine.KismetMathLibrary.Vector_Distance", 700, -80)
    connect(p_loc, "ReturnValue", dist_node, "v1")
    connect(self_loc, "ReturnValue", dist_node, "v2")

    sub_v = fn(ed, "/Script/Engine.KismetMathLibrary.Subtract_VectorVector", 700, 100)
    connect(p_loc, "ReturnValue", sub_v, "A")
    connect(self_loc, "ReturnValue", sub_v, "B")

    norm_v = fn(ed, "/Script/Engine.KismetMathLibrary.Normal", 920, 100)
    connect(sub_v, "ReturnValue", norm_v, "A")

    break_v = fn(ed, "/Script/Engine.KismetMathLibrary.BreakVector", 1140, 100)
    connect(norm_v, "ReturnValue", break_v, "InVec")

    speed = 150.0  # 猎犬高移速奔跑

    # 3. 轴分离物理位移 (X + Z 双路 Sweep)
    mul_x_speed = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1360, 50)
    connect(break_v, "X", mul_x_speed, "A"); set_value(mul_x_speed, "B", speed)

    mul_x_dt = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1580, 50)
    connect(mul_x_speed, "ReturnValue", mul_x_dt, "A")
    connect(tick_node, "DeltaSeconds", mul_x_dt, "B")

    delta_vec_x = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 1800, 50)
    connect(mul_x_dt, "ReturnValue", delta_vec_x, "X"); set_value(delta_vec_x, "Y", 0.0); set_value(delta_vec_x, "Z", 0.0)

    move_x = fn(ed, "/Script/Engine.Actor.K2_AddActorWorldOffset", 2050, 50)
    set_value(move_x, "bSweep", "true")
    connect(delta_vec_x, "ReturnValue", move_x, "DeltaLocation")
    connect(tick_node, "then", move_x, "execute")

    mul_z_speed = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1360, 220)
    connect(break_v, "Z", mul_z_speed, "A"); set_value(mul_z_speed, "B", speed)

    mul_z_dt = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1580, 220)
    connect(mul_z_speed, "ReturnValue", mul_z_dt, "A")
    connect(tick_node, "DeltaSeconds", mul_z_dt, "B")

    delta_vec_z = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 1800, 220)
    set_value(delta_vec_z, "X", 0.0); set_value(delta_vec_z, "Y", 0.0); connect(mul_z_dt, "ReturnValue", delta_vec_z, "Z")

    move_z = fn(ed, "/Script/Engine.Actor.K2_AddActorWorldOffset", 2050, 220)
    set_value(move_z, "bSweep", "true")
    connect(delta_vec_z, "ReturnValue", move_z, "DeltaLocation")
    connect(move_x, "then", move_z, "execute")

    # 4. 获取 FlipbookComponent
    get_fb = fn(ed, "/Script/Engine.Actor.GetComponentByClass", 1800, -250)
    set_value(get_fb, "ComponentClass", "Class'/Script/Paper2D.PaperFlipbookComponent'")

    # 5. 距离判定：近身扑击技能 (Dist <= 110) vs 4 向奔跑追逐 (Dist > 110)
    is_near = fn(ed, "/Script/Engine.KismetMathLibrary.LessEqual_DoubleDouble", 950, -80)
    connect(dist_node, "ReturnValue", is_near, "A"); set_value(is_near, "B", 110.0)

    br_state = ed.add_branch_node()
    br_state.set_node_pos(unreal.IntPoint(2300, 100))
    connect(move_z, "then", br_state, "execute")
    connect(is_near, "ReturnValue", br_state, "Condition")

    # --- 技能分支 (True): 播放扑击动作 ---
    set_pounce = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2550, -50)
    if fb_pounce_down: set_value(set_pounce, "NewFlipbook", f"PaperFlipbook'{fb_pounce_down.get_path_name()}'")
    connect(br_state, "then", set_pounce, "execute")
    connect(get_fb, "ReturnValue", set_pounce, "self")

    # --- 移动奔跑分支 (False): 4 向奔跑动画判别 ---
    abs_x = fn(ed, "/Script/Engine.KismetMathLibrary.Abs", 1360, -20)
    connect(break_v, "X", abs_x, "A")

    abs_z = fn(ed, "/Script/Engine.KismetMathLibrary.Abs", 1360, 40)
    connect(break_v, "Z", abs_z, "A")

    is_horizontal = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 1580, 0)
    connect(abs_x, "ReturnValue", is_horizontal, "A")
    connect(abs_z, "ReturnValue", is_horizontal, "B")

    # 水平方向判定 (Right vs Left)
    is_right = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 1800, -20)
    connect(break_v, "X", is_right, "A"); set_value(is_right, "B", 0.0)

    sel_fb_horiz = fn(ed, "/Script/Engine.KismetMathLibrary.SelectObject", 2050, -20)
    if fb_run_right: set_value(sel_fb_horiz, "A", f"PaperFlipbook'{fb_run_right.get_path_name()}'")
    if fb_run_left: set_value(sel_fb_horiz, "B", f"PaperFlipbook'{fb_run_left.get_path_name()}'")
    connect(is_right, "ReturnValue", sel_fb_horiz, "bSelectA")

    # 垂直方向判定 (Up vs Down)
    is_up = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 1800, 100)
    connect(break_v, "Z", is_up, "A"); set_value(is_up, "B", 0.0)

    sel_fb_vert = fn(ed, "/Script/Engine.KismetMathLibrary.SelectObject", 2050, 100)
    if fb_run_up: set_value(sel_fb_vert, "A", f"PaperFlipbook'{fb_run_up.get_path_name()}'")
    if fb_run_down: set_value(sel_fb_vert, "B", f"PaperFlipbook'{fb_run_down.get_path_name()}'")
    connect(is_up, "ReturnValue", sel_fb_vert, "bSelectA")

    # 最终选择奔跑 Flipbook
    final_run_fb = fn(ed, "/Script/Engine.KismetMathLibrary.SelectObject", 2300, 0)
    connect(sel_fb_horiz, "ReturnValue", final_run_fb, "A")
    connect(sel_fb_vert, "ReturnValue", final_run_fb, "B")
    connect(is_horizontal, "ReturnValue", final_run_fb, "bSelectA")

    set_run = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2550, 150)
    connect(br_state, "else", set_run, "execute")
    connect(get_fb, "ReturnValue", set_run, "self")
    connect(final_run_fb, "ReturnValue", set_run, "NewFlipbook")

    # 6. CDO 默认 4 向规模
    cdo = unreal.get_default_object(bp.generated_class())
    if cdo:
        comp = cdo.get_component_by_class(unreal.PaperFlipbookComponent)
        if comp:
            if fb_run_down: comp.set_editor_property("source_flipbook", fb_run_down)
            comp.set_editor_property("relative_scale3d", unreal.Vector(0.48, 0.48, 0.48))
            comp.set_editor_property("translucency_sort_priority", 200)

    bplib.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
    log("  ✅ 变异猎犬 4 向奔跑与扑击技能状态机装配成功！")
    return True

# ==============================================================================
# 3. 深渊异化领主 Boss (4 向完整移动走动 + 地裂重击技能 + 状态机)
# ==============================================================================
def build_boss_overlord_ai():
    bp_path = f"{ENEMY_BP_DIR}/BP_Boss_Overlord"
    log(f"👑 正在配置深渊异化领主 Boss 4 向行走与地裂技能状态机 ({bp_path})...")
    bp = unreal.load_asset(bp_path)
    if not bp:
        log(f"⚠️ 未找到蓝图: {bp_path}")
        return False

    ensure_box_component(bp, unreal.Vector(55.0, 90.0, 65.0))
    ed, tick_node = clean_event_graph(bp)

    # 加载 Boss 4 向行走、待机与技能动画
    fb_walk_down = unreal.load_asset(f"{BOSS_ART_DIR}/Actions/Walk/Dir_01_Down/Flipbooks/FB_T_Boss_Walk_Dir_01_Down_Sheet.FB_T_Boss_Walk_Dir_01_Down_Sheet")
    fb_walk_right = unreal.load_asset(f"{BOSS_ART_DIR}/Actions/Walk/Dir_02_Right/Flipbooks/FB_T_Boss_Walk_Dir_02_Right_Sheet.FB_T_Boss_Walk_Dir_02_Right_Sheet")
    fb_walk_up = unreal.load_asset(f"{BOSS_ART_DIR}/Actions/Walk/Dir_03_Up/Flipbooks/FB_T_Boss_Walk_Dir_03_Up_Sheet.FB_T_Boss_Walk_Dir_03_Up_Sheet")
    fb_walk_left = unreal.load_asset(f"{BOSS_ART_DIR}/Actions/Walk/Dir_04_Left/Flipbooks/FB_T_Boss_Walk_Dir_04_Left_Sheet.FB_T_Boss_Walk_Dir_04_Left_Sheet")
    fb_slam_down = unreal.load_asset(f"{BOSS_ART_DIR}/Actions/Ground_Slam/Dir_01_Down/Flipbooks/FB_T_Boss_Slam_Dir_01_Down_Sheet.FB_T_Boss_Slam_Dir_01_Down_Sheet")

    # 1. 采样玩家坐标与自身坐标
    get_player = fn(ed, "/Script/Engine.GameplayStatics.GetPlayerPawn", 200, 100)
    set_value(get_player, "PlayerIndex", 0)

    p_loc = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 450, 50)
    connect(get_player, "ReturnValue", p_loc, "self")

    self_loc = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 450, 180)

    # 2. 距离与追逐向量
    dist_node = fn(ed, "/Script/Engine.KismetMathLibrary.Vector_Distance", 700, -80)
    connect(p_loc, "ReturnValue", dist_node, "v1")
    connect(self_loc, "ReturnValue", dist_node, "v2")

    sub_v = fn(ed, "/Script/Engine.KismetMathLibrary.Subtract_VectorVector", 700, 100)
    connect(p_loc, "ReturnValue", sub_v, "A")
    connect(self_loc, "ReturnValue", sub_v, "B")

    norm_v = fn(ed, "/Script/Engine.KismetMathLibrary.Normal", 920, 100)
    connect(sub_v, "ReturnValue", norm_v, "A")

    break_v = fn(ed, "/Script/Engine.KismetMathLibrary.BreakVector", 1140, 100)
    connect(norm_v, "ReturnValue", break_v, "InVec")

    speed = 35.0  # Boss 压迫感沉稳步伐

    # 3. 轴分离物理位移 (X + Z 双路 Sweep)
    mul_x_speed = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1360, 50)
    connect(break_v, "X", mul_x_speed, "A"); set_value(mul_x_speed, "B", speed)

    mul_x_dt = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1580, 50)
    connect(mul_x_speed, "ReturnValue", mul_x_dt, "A")
    connect(tick_node, "DeltaSeconds", mul_x_dt, "B")

    delta_vec_x = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 1800, 50)
    connect(mul_x_dt, "ReturnValue", delta_vec_x, "X"); set_value(delta_vec_x, "Y", 0.0); set_value(delta_vec_x, "Z", 0.0)

    move_x = fn(ed, "/Script/Engine.Actor.K2_AddActorWorldOffset", 2050, 50)
    set_value(move_x, "bSweep", "true")
    connect(delta_vec_x, "ReturnValue", move_x, "DeltaLocation")
    connect(tick_node, "then", move_x, "execute")

    mul_z_speed = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1360, 220)
    connect(break_v, "Z", mul_z_speed, "A"); set_value(mul_z_speed, "B", speed)

    mul_z_dt = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1580, 220)
    connect(mul_z_speed, "ReturnValue", mul_z_dt, "A")
    connect(tick_node, "DeltaSeconds", mul_z_dt, "B")

    delta_vec_z = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 1800, 220)
    set_value(delta_vec_z, "X", 0.0); set_value(delta_vec_z, "Y", 0.0); connect(mul_z_dt, "ReturnValue", delta_vec_z, "Z")

    move_z = fn(ed, "/Script/Engine.Actor.K2_AddActorWorldOffset", 2050, 220)
    set_value(move_z, "bSweep", "true")
    connect(delta_vec_z, "ReturnValue", move_z, "DeltaLocation")
    connect(move_x, "then", move_z, "execute")

    # 4. 获取 FlipbookComponent
    get_fb = fn(ed, "/Script/Engine.Actor.GetComponentByClass", 1800, -250)
    set_value(get_fb, "ComponentClass", "Class'/Script/Paper2D.PaperFlipbookComponent'")

    # 5. 距离判定：近身地裂技能 (Dist <= 140) vs 4 向行走追逐 (Dist > 140)
    is_near = fn(ed, "/Script/Engine.KismetMathLibrary.LessEqual_DoubleDouble", 950, -80)
    connect(dist_node, "ReturnValue", is_near, "A"); set_value(is_near, "B", 140.0)

    br_state = ed.add_branch_node()
    br_state.set_node_pos(unreal.IntPoint(2300, 100))
    connect(move_z, "then", br_state, "execute")
    connect(is_near, "ReturnValue", br_state, "Condition")

    # --- 技能分支 (True): 播放地裂重砸技能 ---
    set_slam = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2550, -50)
    if fb_slam_down: set_value(set_slam, "NewFlipbook", f"PaperFlipbook'{fb_slam_down.get_path_name()}'")
    connect(br_state, "then", set_slam, "execute")
    connect(get_fb, "ReturnValue", set_slam, "self")

    # --- 移动行走分支 (False): 4 向行走动画判别 ---
    abs_x = fn(ed, "/Script/Engine.KismetMathLibrary.Abs", 1360, -20)
    connect(break_v, "X", abs_x, "A")

    abs_z = fn(ed, "/Script/Engine.KismetMathLibrary.Abs", 1360, 40)
    connect(break_v, "Z", abs_z, "A")

    is_horizontal = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 1580, 0)
    connect(abs_x, "ReturnValue", is_horizontal, "A")
    connect(abs_z, "ReturnValue", is_horizontal, "B")

    # 水平方向判定 (Right vs Left)
    is_right = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 1800, -20)
    connect(break_v, "X", is_right, "A"); set_value(is_right, "B", 0.0)

    sel_fb_horiz = fn(ed, "/Script/Engine.KismetMathLibrary.SelectObject", 2050, -20)
    if fb_walk_right: set_value(sel_fb_horiz, "A", f"PaperFlipbook'{fb_walk_right.get_path_name()}'")
    if fb_walk_left: set_value(sel_fb_horiz, "B", f"PaperFlipbook'{fb_walk_left.get_path_name()}'")
    connect(is_right, "ReturnValue", sel_fb_horiz, "bSelectA")

    # 垂直方向判定 (Up vs Down)
    is_up = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 1800, 100)
    connect(break_v, "Z", is_up, "A"); set_value(is_up, "B", 0.0)

    sel_fb_vert = fn(ed, "/Script/Engine.KismetMathLibrary.SelectObject", 2050, 100)
    if fb_walk_up: set_value(sel_fb_vert, "A", f"PaperFlipbook'{fb_walk_up.get_path_name()}'")
    if fb_walk_down: set_value(sel_fb_vert, "B", f"PaperFlipbook'{fb_walk_down.get_path_name()}'")
    connect(is_up, "ReturnValue", sel_fb_vert, "bSelectA")

    # 最终选择行走 Flipbook
    final_walk_fb = fn(ed, "/Script/Engine.KismetMathLibrary.SelectObject", 2300, 0)
    connect(sel_fb_horiz, "ReturnValue", final_walk_fb, "A")
    connect(sel_fb_vert, "ReturnValue", final_walk_fb, "B")
    connect(is_horizontal, "ReturnValue", final_walk_fb, "bSelectA")

    set_walk = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2550, 150)
    connect(br_state, "else", set_walk, "execute")
    connect(get_fb, "ReturnValue", set_walk, "self")
    connect(final_walk_fb, "ReturnValue", set_walk, "NewFlipbook")

    # 6. CDO 默认 4 向规模
    cdo = unreal.get_default_object(bp.generated_class())
    if cdo:
        comp = cdo.get_component_by_class(unreal.PaperFlipbookComponent)
        if comp:
            if fb_walk_down: comp.set_editor_property("source_flipbook", fb_walk_down)
            comp.set_editor_property("relative_scale3d", unreal.Vector(0.68, 0.68, 0.68))
            comp.set_editor_property("translucency_sort_priority", 200)

    bplib.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
    log("  ✅ 深渊异化领主 Boss 4 向行走与地裂技能状态机装配成功！")
    return True

# ==============================================================================
# 主执行入口
# ==============================================================================
def main():
    log("🚀 [1/3] 重构行尸家族 5 类 4 帧追逐体系...")
    for spec in ZOMBIE_SPECS:
        build_zombie_ai(spec)

    log("🚀 [2/3] 重构变异猎犬 4 向奔跑与扑击技能状态机...")
    build_mutant_hound_ai()

    log("🚀 [3/3] 重构深渊领主 Boss 4 向行走与地裂技能状态机...")
    build_boss_overlord_ai()

    unreal.EditorAssetLibrary.save_directory(ENEMY_BP_DIR, only_if_is_dirty=False, recursive=True)
    log("🎉 ALL_ENEMY_ANIMATIONS_AND_AI_CHASE_COMPLETED_SUCCESSFULLY")

if __name__ == "__main__":
    main()
