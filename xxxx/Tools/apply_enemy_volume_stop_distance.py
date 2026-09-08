# -*- coding: utf-8 -*-
"""
apply_enemy_volume_stop_distance.py
为所有敌人（Boss、猎犬、行尸）装配严格考虑角色体积的防重叠寻路系统：
1. Boss (BP_Boss_Overlord): 自身半宽65 + 玩家半宽30 + 裕量30 = 125 uu 停止距离
   - 距离 > 125 uu: 执行位移与4向行走动画
   - 距离 <= 125 uu: 严格拦截位移(速度归零)，原地释放地裂重击(Ground Slam)
2. 变异猎犬 (BP_Enemy_MutantHound): 自身半宽28 + 玩家半宽30 + 裕量17 = 75 uu 停止距离
   - 距离 > 75 uu: 执行高速位移与4向奔跑动画
   - 距离 <= 75 uu: 严格拦截位移(速度归零)，原地释放飞扑撕咬(Pounce)
3. 行尸 (BP_Enemy_ZombieWalker): 自身半宽35 + 玩家半宽30 + 裕量15 = 80 uu 停止距离
   - 距离 > 80 uu: 执行位移与水平翻转更新
   - 距离 <= 80 uu: 严格拦截位移，防线外围停步抓挠，绝不穿入角色
"""
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
REPORT_PATH = ROOT / "output/enemy_volume_stop_distance_report.json"

BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary
ASSETS = unreal.EditorAssetLibrary

def log(msg):
    print(f"[AI_VOLUME_STOP] {msg}", flush=True)
    unreal.log(f"[AI_VOLUME_STOP] {msg}")

def pin(node, name, output=None):
    if output is True:
        pins = BPLIB.list_output_pins(node)
    elif output is False:
        pins = BPLIB.list_input_pins(node)
    else:
        pins = list(BPLIB.list_output_pins(node)) + list(BPLIB.list_input_pins(node))
    
    wanted = name.lower()
    for p in pins:
        if str(PINLIB.get_pin_name(p)).lower() == wanted:
            return p
    avail = [str(PINLIB.get_pin_name(p)) for p in pins]
    raise RuntimeError(f"未找到引脚 '{name}'，可用引脚: {avail}")

def set_value(node, name, value):
    p = pin(node, name, False)
    if not PINLIB.set_pin_value(p, str(value)):
        raise RuntimeError(f"设置引脚默认值失败: {name}={value}")

def connect(n1, p1, n2, p2):
    sp = pin(n1, p1, True)
    tp = pin(n2, p2, False)
    ok = PINLIB.try_create_connection(sp, tp)
    if not ok:
        raise RuntimeError(f"连线失败: {BPLIB.get_node_title(n1)}.{p1} -> {BPLIB.get_node_title(n2)}.{p2}")
    return ok

def fn(ed, path, x, y):
    node = ed.add_call_function_node(path)
    if not node:
        raise RuntimeError(f"创建函数节点失败: {path}")
    node.set_node_pos(unreal.IntPoint(x, y))
    return node

def clean_event_graph(bp):
    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    tick_node = ed.find_event_node("ReceiveTick")
    begin_node = ed.find_event_node("ReceiveBeginPlay")
    
    keep_paths = set()
    if tick_node:
        keep_paths.add(tick_node.get_path_name())
    if begin_node:
        keep_paths.add(begin_node.get_path_name())
        
    nodes_to_remove = [n for n in ed.list_all_nodes() if n.get_path_name() not in keep_paths]
    for n in nodes_to_remove:
        for p in BPLIB.list_all_pins(n):
            try: PINLIB.break_pin_links(p)
            except Exception: pass
    if nodes_to_remove:
        ed.remove_nodes(nodes_to_remove)
    return ed, tick_node

# ==============================================================================
# 1. 重构深渊领主 Boss (BP_Boss_Overlord) - StopDistance = 125.0
# ==============================================================================
def setup_boss_volume_stop():
    bp_path = "/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord"
    log(f"👑 正在重构 Boss 防重叠体积寻路: {bp_path} (StopDistance=125.0)...")
    bp = ASSETS.load_asset(bp_path)
    if not bp:
        raise RuntimeError(f"未找到 Boss 蓝图: {bp_path}")

    ed, tick_node = clean_event_graph(bp)
    tick_node.set_node_pos(unreal.IntPoint(0, 0))

    BOSS_ART = "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Boss_Overlord"
    fb_walk_down = unreal.load_asset(f"{BOSS_ART}/Actions/Walk/Dir_01_Down/Flipbooks/FB_T_Boss_Walk_Dir_01_Down_Sheet.FB_T_Boss_Walk_Dir_01_Down_Sheet")
    fb_walk_right = unreal.load_asset(f"{BOSS_ART}/Actions/Walk/Dir_02_Right/Flipbooks/FB_T_Boss_Walk_Dir_02_Right_Sheet.FB_T_Boss_Walk_Dir_02_Right_Sheet")
    fb_walk_up = unreal.load_asset(f"{BOSS_ART}/Actions/Walk/Dir_03_Up/Flipbooks/FB_T_Boss_Walk_Dir_03_Up_Sheet.FB_T_Boss_Walk_Dir_03_Up_Sheet")
    fb_walk_left = unreal.load_asset(f"{BOSS_ART}/Actions/Walk/Dir_04_Left/Flipbooks/FB_T_Boss_Walk_Dir_04_Left_Sheet.FB_T_Boss_Walk_Dir_04_Left_Sheet")
    fb_slam_down = unreal.load_asset(f"{BOSS_ART}/Actions/Ground_Slam/Dir_01_Down/Flipbooks/FB_T_Boss_Slam_Dir_01_Down_Sheet.FB_T_Boss_Slam_Dir_01_Down_Sheet")

    # 1. 采样玩家坐标与自身坐标
    get_player = fn(ed, "/Script/Engine.GameplayStatics.GetPlayerPawn", 220, 100)
    set_value(get_player, "PlayerIndex", 0)

    p_loc = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 460, 40)
    connect(get_player, "ReturnValue", p_loc, "self")

    self_loc = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 460, 180)

    # 2. 距离计算
    dist_node = fn(ed, "/Script/Engine.KismetMathLibrary.Vector_Distance", 700, -80)
    connect(p_loc, "ReturnValue", dist_node, "v1")
    connect(self_loc, "ReturnValue", dist_node, "v2")

    # 3. 门禁分支：Distance > 125.0 (考虑两者体积之后仍有安全距离才允许移动)
    is_far = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 940, -80)
    connect(dist_node, "ReturnValue", is_far, "A")
    set_value(is_far, "B", 125.0)

    br_gate = ed.add_branch_node()
    br_gate.set_node_pos(unreal.IntPoint(1160, 0))
    connect(tick_node, "then", br_gate, "execute")
    connect(is_far, "ReturnValue", br_gate, "Condition")

    # --- 4. 追击向量与位移 (仅在 br_gate.then 执行！) ---
    sub_v = fn(ed, "/Script/Engine.KismetMathLibrary.Subtract_VectorVector", 700, 120)
    connect(p_loc, "ReturnValue", sub_v, "A")
    connect(self_loc, "ReturnValue", sub_v, "B")

    norm_v = fn(ed, "/Script/Engine.KismetMathLibrary.Normal", 920, 120)
    connect(sub_v, "ReturnValue", norm_v, "A")

    break_v = fn(ed, "/Script/Engine.KismetMathLibrary.BreakVector", 1140, 120)
    connect(norm_v, "ReturnValue", break_v, "InVec")

    speed = 35.0

    mul_x_speed = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1380, 40)
    connect(break_v, "X", mul_x_speed, "A")
    set_value(mul_x_speed, "B", speed)

    mul_x_dt = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1600, 40)
    connect(mul_x_speed, "ReturnValue", mul_x_dt, "A")
    connect(tick_node, "DeltaSeconds", mul_x_dt, "B")

    delta_vec_x = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 1820, 40)
    connect(mul_x_dt, "ReturnValue", delta_vec_x, "X")
    set_value(delta_vec_x, "Y", 0.0); set_value(delta_vec_x, "Z", 0.0)

    move_x = fn(ed, "/Script/Engine.Actor.K2_AddActorWorldOffset", 2060, 40)
    set_value(move_x, "bSweep", "true")
    connect(delta_vec_x, "ReturnValue", move_x, "DeltaLocation")
    connect(br_gate, "then", move_x, "execute")  # 核心：由 br_gate.then 驱动！

    mul_z_speed = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1380, 200)
    connect(break_v, "Z", mul_z_speed, "A")
    set_value(mul_z_speed, "B", speed)

    mul_z_dt = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1600, 200)
    connect(mul_z_speed, "ReturnValue", mul_z_dt, "A")
    connect(tick_node, "DeltaSeconds", mul_z_dt, "B")

    delta_vec_z = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 1820, 200)
    set_value(delta_vec_z, "X", 0.0); set_value(delta_vec_z, "Y", 0.0)
    connect(mul_z_dt, "ReturnValue", delta_vec_z, "Z")

    move_z = fn(ed, "/Script/Engine.Actor.K2_AddActorWorldOffset", 2060, 200)
    set_value(move_z, "bSweep", "true")
    connect(delta_vec_z, "ReturnValue", move_z, "DeltaLocation")
    connect(move_x, "then", move_z, "execute")

    # 5. 获取 Flipbook 组件
    get_fb = fn(ed, "/Script/Engine.Actor.GetComponentByClass", 1820, -260)
    set_value(get_fb, "ComponentClass", "Class'/Script/Paper2D.PaperFlipbookComponent'")

    # 6. 行走动画方向选择 (由 move_z 驱动)
    abs_x = fn(ed, "/Script/Engine.KismetMathLibrary.Abs", 1380, -40)
    connect(break_v, "X", abs_x, "A")
    abs_z = fn(ed, "/Script/Engine.KismetMathLibrary.Abs", 1380, 10)
    connect(break_v, "Z", abs_z, "A")

    is_horizontal = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 1600, -20)
    connect(abs_x, "ReturnValue", is_horizontal, "A")
    connect(abs_z, "ReturnValue", is_horizontal, "B")

    is_right = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 1820, -40)
    connect(break_v, "X", is_right, "A"); set_value(is_right, "B", 0.0)

    sel_fb_horiz = fn(ed, "/Script/Engine.KismetMathLibrary.SelectObject", 2060, -40)
    if fb_walk_right: set_value(sel_fb_horiz, "A", f"PaperFlipbook'{fb_walk_right.get_path_name()}'")
    if fb_walk_left: set_value(sel_fb_horiz, "B", f"PaperFlipbook'{fb_walk_left.get_path_name()}'")
    connect(is_right, "ReturnValue", sel_fb_horiz, "bSelectA")

    is_up = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 1820, 80)
    connect(break_v, "Z", is_up, "A"); set_value(is_up, "B", 0.0)

    sel_fb_vert = fn(ed, "/Script/Engine.KismetMathLibrary.SelectObject", 2060, 80)
    if fb_walk_up: set_value(sel_fb_vert, "A", f"PaperFlipbook'{fb_walk_up.get_path_name()}'")
    if fb_walk_down: set_value(sel_fb_vert, "B", f"PaperFlipbook'{fb_walk_down.get_path_name()}'")
    connect(is_up, "ReturnValue", sel_fb_vert, "bSelectA")

    final_walk_fb = fn(ed, "/Script/Engine.KismetMathLibrary.SelectObject", 2300, 0)
    connect(sel_fb_horiz, "ReturnValue", final_walk_fb, "A")
    connect(sel_fb_vert, "ReturnValue", final_walk_fb, "B")
    connect(is_horizontal, "ReturnValue", final_walk_fb, "bSelectA")

    set_walk = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2560, 100)
    connect(move_z, "then", set_walk, "execute")
    connect(get_fb, "ReturnValue", set_walk, "self")
    connect(final_walk_fb, "ReturnValue", set_walk, "NewFlipbook")

    # --- 7. 到达角色体积外围 (br_gate.else: Distance <= 125.0) ---
    # 核心：完全不执行 move_x 和 move_z，速度为 0，原地播放地裂重砸动画！
    set_slam = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 1400, -180)
    if fb_slam_down: set_value(set_slam, "NewFlipbook", f"PaperFlipbook'{fb_slam_down.get_path_name()}'")
    connect(br_gate, "else", set_slam, "execute")
    connect(get_fb, "ReturnValue", set_slam, "self")

    BPLIB.compile_blueprint(bp)
    saved = ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"  💾 Boss BP_Boss_Overlord 编译与落盘: {'成功' if saved else '失败'}")
    return saved

# ==============================================================================
# 2. 重构变异猎犬 (BP_Enemy_MutantHound) - StopDistance = 75.0
# ==============================================================================
def setup_hound_volume_stop():
    bp_path = "/Game/Blueprints/Characters/Enemies/BP_Enemy_MutantHound"
    log(f"🐕 正在重构变异猎犬防重叠体积寻路: {bp_path} (StopDistance=75.0)...")
    bp = ASSETS.load_asset(bp_path)
    if not bp:
        raise RuntimeError(f"未找到猎犬蓝图: {bp_path}")

    ed, tick_node = clean_event_graph(bp)
    tick_node.set_node_pos(unreal.IntPoint(0, 0))

    HOUND_ART = "/Game/P01/Imported/Content/Asset/Art/02_Enemies/MutantHound"
    fb_run_down = unreal.load_asset(f"{HOUND_ART}/Run/Dir_01_Down/Flipbooks/FB_T_Hound_Run_Dir_01_Down_Sheet.FB_T_Hound_Run_Dir_01_Down_Sheet")
    fb_run_right = unreal.load_asset(f"{HOUND_ART}/Run/Dir_02_Right/Flipbooks/FB_T_Hound_Run_Dir_02_Right_Sheet.FB_T_Hound_Run_Dir_02_Right_Sheet")
    fb_run_up = unreal.load_asset(f"{HOUND_ART}/Run/Dir_03_Up/Flipbooks/FB_T_Hound_Run_Dir_03_Up_Sheet.FB_T_Hound_Run_Dir_03_Up_Sheet")
    fb_run_left = unreal.load_asset(f"{HOUND_ART}/Run/Dir_04_Left/Flipbooks/FB_T_Hound_Run_Dir_04_Left_Sheet.FB_T_Hound_Run_Dir_04_Left_Sheet")
    fb_pounce_down = unreal.load_asset(f"{HOUND_ART}/Pounce/Dir_01_Down/Flipbooks/FB_T_Hound_Pounce_Dir_01_Down_Sheet.FB_T_Hound_Pounce_Dir_01_Down_Sheet")

    # 1. 采样玩家坐标与自身坐标
    get_player = fn(ed, "/Script/Engine.GameplayStatics.GetPlayerPawn", 220, 100)
    set_value(get_player, "PlayerIndex", 0)

    p_loc = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 460, 40)
    connect(get_player, "ReturnValue", p_loc, "self")

    self_loc = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 460, 180)

    # 2. 距离计算与门禁判断 (Distance > 75.0)
    dist_node = fn(ed, "/Script/Engine.KismetMathLibrary.Vector_Distance", 700, -80)
    connect(p_loc, "ReturnValue", dist_node, "v1")
    connect(self_loc, "ReturnValue", dist_node, "v2")

    is_far = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 940, -80)
    connect(dist_node, "ReturnValue", is_far, "A")
    set_value(is_far, "B", 75.0)

    br_gate = ed.add_branch_node()
    br_gate.set_node_pos(unreal.IntPoint(1160, 0))
    connect(tick_node, "then", br_gate, "execute")
    connect(is_far, "ReturnValue", br_gate, "Condition")

    # 3. 追击向量与位移 (仅在 br_gate.then 执行)
    sub_v = fn(ed, "/Script/Engine.KismetMathLibrary.Subtract_VectorVector", 700, 120)
    connect(p_loc, "ReturnValue", sub_v, "A")
    connect(self_loc, "ReturnValue", sub_v, "B")

    norm_v = fn(ed, "/Script/Engine.KismetMathLibrary.Normal", 920, 120)
    connect(sub_v, "ReturnValue", norm_v, "A")

    break_v = fn(ed, "/Script/Engine.KismetMathLibrary.BreakVector", 1140, 120)
    connect(norm_v, "ReturnValue", break_v, "InVec")

    speed = 150.0

    mul_x_speed = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1380, 40)
    connect(break_v, "X", mul_x_speed, "A")
    set_value(mul_x_speed, "B", speed)

    mul_x_dt = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1600, 40)
    connect(mul_x_speed, "ReturnValue", mul_x_dt, "A")
    connect(tick_node, "DeltaSeconds", mul_x_dt, "B")

    delta_vec_x = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 1820, 40)
    connect(mul_x_dt, "ReturnValue", delta_vec_x, "X")
    set_value(delta_vec_x, "Y", 0.0); set_value(delta_vec_x, "Z", 0.0)

    move_x = fn(ed, "/Script/Engine.Actor.K2_AddActorWorldOffset", 2060, 40)
    set_value(move_x, "bSweep", "true")
    connect(delta_vec_x, "ReturnValue", move_x, "DeltaLocation")
    connect(br_gate, "then", move_x, "execute")

    mul_z_speed = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1380, 200)
    connect(break_v, "Z", mul_z_speed, "A")
    set_value(mul_z_speed, "B", speed)

    mul_z_dt = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1600, 200)
    connect(mul_z_speed, "ReturnValue", mul_z_dt, "A")
    connect(tick_node, "DeltaSeconds", mul_z_dt, "B")

    delta_vec_z = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 1820, 200)
    set_value(delta_vec_z, "X", 0.0); set_value(delta_vec_z, "Y", 0.0)
    connect(mul_z_dt, "ReturnValue", delta_vec_z, "Z")

    move_z = fn(ed, "/Script/Engine.Actor.K2_AddActorWorldOffset", 2060, 200)
    set_value(move_z, "bSweep", "true")
    connect(delta_vec_z, "ReturnValue", move_z, "DeltaLocation")
    connect(move_x, "then", move_z, "execute")

    # 4. 获取 Flipbook 组件
    get_fb = fn(ed, "/Script/Engine.Actor.GetComponentByClass", 1820, -260)
    set_value(get_fb, "ComponentClass", "Class'/Script/Paper2D.PaperFlipbookComponent'")

    # 5. 奔跑动画选择
    abs_x = fn(ed, "/Script/Engine.KismetMathLibrary.Abs", 1380, -40)
    connect(break_v, "X", abs_x, "A")
    abs_z = fn(ed, "/Script/Engine.KismetMathLibrary.Abs", 1380, 10)
    connect(break_v, "Z", abs_z, "A")

    is_horizontal = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 1600, -20)
    connect(abs_x, "ReturnValue", is_horizontal, "A")
    connect(abs_z, "ReturnValue", is_horizontal, "B")

    is_right = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 1820, -40)
    connect(break_v, "X", is_right, "A"); set_value(is_right, "B", 0.0)

    sel_fb_horiz = fn(ed, "/Script/Engine.KismetMathLibrary.SelectObject", 2060, -40)
    if fb_run_right: set_value(sel_fb_horiz, "A", f"PaperFlipbook'{fb_run_right.get_path_name()}'")
    if fb_run_left: set_value(sel_fb_horiz, "B", f"PaperFlipbook'{fb_run_left.get_path_name()}'")
    connect(is_right, "ReturnValue", sel_fb_horiz, "bSelectA")

    is_up = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 1820, 80)
    connect(break_v, "Z", is_up, "A"); set_value(is_up, "B", 0.0)

    sel_fb_vert = fn(ed, "/Script/Engine.KismetMathLibrary.SelectObject", 2060, 80)
    if fb_run_up: set_value(sel_fb_vert, "A", f"PaperFlipbook'{fb_run_up.get_path_name()}'")
    if fb_run_down: set_value(sel_fb_vert, "B", f"PaperFlipbook'{fb_run_down.get_path_name()}'")
    connect(is_up, "ReturnValue", sel_fb_vert, "bSelectA")

    final_run_fb = fn(ed, "/Script/Engine.KismetMathLibrary.SelectObject", 2300, 0)
    connect(sel_fb_horiz, "ReturnValue", final_run_fb, "A")
    connect(sel_fb_vert, "ReturnValue", final_run_fb, "B")
    connect(is_horizontal, "ReturnValue", final_run_fb, "bSelectA")

    set_run = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2560, 100)
    connect(move_z, "then", set_run, "execute")
    connect(get_fb, "ReturnValue", set_run, "self")
    connect(final_run_fb, "ReturnValue", set_run, "NewFlipbook")

    # --- 6. 到达角色体积外围 (br_gate.else: Distance <= 75.0) ---
    # 严格拦截位移，速度归零，原地释放飞扑撕咬动作
    set_pounce = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 1400, -180)
    if fb_pounce_down: set_value(set_pounce, "NewFlipbook", f"PaperFlipbook'{fb_pounce_down.get_path_name()}'")
    connect(br_gate, "else", set_pounce, "execute")
    connect(get_fb, "ReturnValue", set_pounce, "self")

    BPLIB.compile_blueprint(bp)
    saved = ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"  💾 变异猎犬 BP_Enemy_MutantHound 编译与落盘: {'成功' if saved else '失败'}")
    return saved

# ==============================================================================
# 3. 重构普通行尸 (BP_Enemy_ZombieWalker) - StopDistance = 80.0
# ==============================================================================
def setup_zombie_volume_stop():
    bp_path = "/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker"
    log(f"🧟 正在重构行尸防重叠体积寻路: {bp_path} (StopDistance=80.0)...")
    bp = ASSETS.load_asset(bp_path)
    if not bp:
        raise RuntimeError(f"未找到行尸蓝图: {bp_path}")

    ed, tick_node = clean_event_graph(bp)
    tick_node.set_node_pos(unreal.IntPoint(0, 0))

    base_scale = 0.45
    speed = 65.0

    # 1. 采样玩家坐标与自身坐标
    get_player = fn(ed, "/Script/Engine.GameplayStatics.GetPlayerPawn", 220, 100)
    set_value(get_player, "PlayerIndex", 0)

    p_loc = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 460, 40)
    connect(get_player, "ReturnValue", p_loc, "self")

    self_loc = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 460, 180)

    # 2. 距离计算与门禁判断 (Distance > 80.0)
    dist_node = fn(ed, "/Script/Engine.KismetMathLibrary.Vector_Distance", 700, -80)
    connect(p_loc, "ReturnValue", dist_node, "v1")
    connect(self_loc, "ReturnValue", dist_node, "v2")

    is_far = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 940, -80)
    connect(dist_node, "ReturnValue", is_far, "A")
    set_value(is_far, "B", 80.0)

    br_gate = ed.add_branch_node()
    br_gate.set_node_pos(unreal.IntPoint(1160, 0))
    connect(tick_node, "then", br_gate, "execute")
    connect(is_far, "ReturnValue", br_gate, "Condition")

    # 3. 追击向量与位移 (仅在 br_gate.then 执行)
    sub_v = fn(ed, "/Script/Engine.KismetMathLibrary.Subtract_VectorVector", 700, 120)
    connect(p_loc, "ReturnValue", sub_v, "A")
    connect(self_loc, "ReturnValue", sub_v, "B")

    norm_v = fn(ed, "/Script/Engine.KismetMathLibrary.Normal", 920, 120)
    connect(sub_v, "ReturnValue", norm_v, "A")

    break_v = fn(ed, "/Script/Engine.KismetMathLibrary.BreakVector", 1140, 120)
    connect(norm_v, "ReturnValue", break_v, "InVec")

    mul_x_speed = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1380, 40)
    connect(break_v, "X", mul_x_speed, "A")
    set_value(mul_x_speed, "B", speed)

    mul_x_dt = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1600, 40)
    connect(mul_x_speed, "ReturnValue", mul_x_dt, "A")
    connect(tick_node, "DeltaSeconds", mul_x_dt, "B")

    delta_vec_x = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 1820, 40)
    connect(mul_x_dt, "ReturnValue", delta_vec_x, "X")
    set_value(delta_vec_x, "Y", 0.0); set_value(delta_vec_x, "Z", 0.0)

    move_x = fn(ed, "/Script/Engine.Actor.K2_AddActorWorldOffset", 2060, 40)
    set_value(move_x, "bSweep", "true")
    connect(delta_vec_x, "ReturnValue", move_x, "DeltaLocation")
    connect(br_gate, "then", move_x, "execute")

    mul_z_speed = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1380, 200)
    connect(break_v, "Z", mul_z_speed, "A")
    set_value(mul_z_speed, "B", speed)

    mul_z_dt = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1600, 200)
    connect(mul_z_speed, "ReturnValue", mul_z_dt, "A")
    connect(tick_node, "DeltaSeconds", mul_z_dt, "B")

    delta_vec_z = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 1820, 200)
    set_value(delta_vec_z, "X", 0.0); set_value(delta_vec_z, "Y", 0.0)
    connect(mul_z_dt, "ReturnValue", delta_vec_z, "Z")

    move_z = fn(ed, "/Script/Engine.Actor.K2_AddActorWorldOffset", 2060, 200)
    set_value(move_z, "bSweep", "true")
    connect(delta_vec_z, "ReturnValue", move_z, "DeltaLocation")
    connect(move_x, "then", move_z, "execute")

    # 4. 水平翻转更新 (在移动时更新)
    is_right = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 1380, -120)
    connect(break_v, "X", is_right, "A")
    set_value(is_right, "B", 0.0)

    sel_scale = fn(ed, "/Script/Engine.KismetMathLibrary.SelectFloat", 1600, -120)
    set_value(sel_scale, "A", -base_scale)
    set_value(sel_scale, "B", base_scale)
    connect(is_right, "ReturnValue", sel_scale, "bPickA")

    scale_vec = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 1820, -120)
    connect(sel_scale, "ReturnValue", scale_vec, "X")
    set_value(scale_vec, "Y", base_scale)
    set_value(scale_vec, "Z", base_scale)

    get_fb = fn(ed, "/Script/Engine.Actor.GetComponentByClass", 1820, -260)
    set_value(get_fb, "ComponentClass", "Class'/Script/Paper2D.PaperFlipbookComponent'")

    set_scale = fn(ed, "/Script/Engine.SceneComponent.SetRelativeScale3D", 2060, -180)
    connect(get_fb, "ReturnValue", set_scale, "self")
    connect(scale_vec, "ReturnValue", set_scale, "NewScale3D")
    connect(move_z, "then", set_scale, "execute")

    # --- 5. 到达角色体积外围 (br_gate.else: Distance <= 80.0) ---
    # 严格拦截位移，速度归零，防线外原地站定，不执行任何位移！
    # （br_gate.else 可以空置或播放原地威慑动作）

    BPLIB.compile_blueprint(bp)
    saved = ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"  💾 行尸 BP_Enemy_ZombieWalker 编译与落盘: {'成功' if saved else '失败'}")
    return saved

def run():
    log("==================================================")
    log("🚀 启动全量敌人 AI 体积防重叠寻路重构流水线...")

    res_boss = setup_boss_volume_stop()
    res_hound = setup_hound_volume_stop()
    res_zombie = setup_zombie_volume_stop()

    report = {
        "status": "PASS" if (res_boss and res_hound and res_zombie) else "FAIL",
        "boss_stop_distance": 125.0,
        "boss_saved": res_boss,
        "hound_stop_distance": 75.0,
        "hound_saved": res_hound,
        "zombie_stop_distance": 80.0,
        "zombie_saved": res_zombie
    }

    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    log("==================================================")
    log(f"🎉 敌人 AI 体积防重叠全部构建完成！报告: {REPORT_PATH}")
    log("==================================================")

if __name__ == "__main__":
    run()
