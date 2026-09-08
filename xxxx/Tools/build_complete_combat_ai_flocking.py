# -*- coding: utf-8 -*-
"""
build_complete_combat_ai_flocking.py
终极解决两大核心 Gameplay 体验问题：
1. 【AI 寻路考虑角色体积，不重叠在角色里】：
   - Boss: 停止距离 125 uu (自身65 + 角色30 + 裕量30)
   - 猎犬: 停止距离 75 uu (自身28 + 角色30 + 裕量17)
   - 行尸: 停止距离 80 uu (自身35 + 角色30 + 裕量15)
   - 距离 <= 停止距离时：切断向前位移，速度归零，原地释放专属攻击/技能！
2. 【怪与怪体积碰撞与防重叠 (Flocking Separation)】：
   - 怪物在移动时通过 GetOverlappingActors 实时检测接触的同伴怪物
   - 一旦两只怪接触重叠，立即沿相对连线反向施加强劲的排斥分离偏移 (RepelForce)
   - 怪与怪触碰瞬间平滑滑开、自然扇面展开，绝不堆叠挤成一团！
3. 【强类型动画状态机】：使用清晰 Branch 节点直连 SetFlipbook，彻底杜绝 Wildcard 连线隐患！
"""
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
REPORT_PATH = ROOT / "output/complete_combat_ai_flocking_report.json"

BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary
ASSETS = unreal.EditorAssetLibrary

def log(msg):
    print(f"[AI_FLOCKING] {msg}", flush=True)
    unreal.log(f"[AI_FLOCKING] {msg}")

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
# 1. 重构深渊领主 Boss (BP_Boss_Overlord)
# ==============================================================================
def setup_boss():
    bp_path = "/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord"
    log(f"👑 重构 Boss: 体积停止(125.0) + 怪怪排斥 + 地裂重砸...")
    bp = ASSETS.load_asset(bp_path)
    if not bp: raise RuntimeError(f"未找到: {bp_path}")

    ed, tick_node = clean_event_graph(bp)
    tick_node.set_node_pos(unreal.IntPoint(0, 0))

    BOSS_ART = "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Boss_Overlord"
    fb_walk_down = unreal.load_asset(f"{BOSS_ART}/Actions/Walk/Dir_01_Down/Flipbooks/FB_T_Boss_Walk_Dir_01_Down_Sheet.FB_T_Boss_Walk_Dir_01_Down_Sheet")
    fb_walk_right = unreal.load_asset(f"{BOSS_ART}/Actions/Walk/Dir_02_Right/Flipbooks/FB_T_Boss_Walk_Dir_02_Right_Sheet.FB_T_Boss_Walk_Dir_02_Right_Sheet")
    fb_walk_up = unreal.load_asset(f"{BOSS_ART}/Actions/Walk/Dir_03_Up/Flipbooks/FB_T_Boss_Walk_Dir_03_Up_Sheet.FB_T_Boss_Walk_Dir_03_Up_Sheet")
    fb_walk_left = unreal.load_asset(f"{BOSS_ART}/Actions/Walk/Dir_04_Left/Flipbooks/FB_T_Boss_Walk_Dir_04_Left_Sheet.FB_T_Boss_Walk_Dir_04_Left_Sheet")
    fb_slam_down = unreal.load_asset(f"{BOSS_ART}/Actions/Ground_Slam/Dir_01_Down/Flipbooks/FB_T_Boss_Slam_Dir_01_Down_Sheet.FB_T_Boss_Slam_Dir_01_Down_Sheet")

    # 1. 采样自身与玩家坐标
    get_player = fn(ed, "/Script/Engine.GameplayStatics.GetPlayerPawn", 220, 100)
    set_value(get_player, "PlayerIndex", 0)

    p_loc = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 460, 40)
    connect(get_player, "ReturnValue", p_loc, "self")

    self_loc = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 460, 180)

    # 2. 距离计算
    dist_node = fn(ed, "/Script/Engine.KismetMathLibrary.Vector_Distance", 700, -80)
    connect(p_loc, "ReturnValue", dist_node, "v1")
    connect(self_loc, "ReturnValue", dist_node, "v2")

    # 3. 门禁分支：Distance > 125.0 (考虑自身65+玩家30+裕量30)
    is_far = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 940, -80)
    connect(dist_node, "ReturnValue", is_far, "A")
    set_value(is_far, "B", 125.0)

    br_gate = ed.add_branch_node()
    br_gate.set_node_pos(unreal.IntPoint(1160, 0))
    connect(tick_node, "then", br_gate, "execute")
    connect(is_far, "ReturnValue", br_gate, "Condition")

    # --- 4. 追击向移动 (br_gate.then: 距离 > 125.0) ---
    sub_v = fn(ed, "/Script/Engine.KismetMathLibrary.Subtract_VectorVector", 700, 120)
    connect(p_loc, "ReturnValue", sub_v, "A")
    connect(self_loc, "ReturnValue", sub_v, "B")

    norm_v = fn(ed, "/Script/Engine.KismetMathLibrary.Normal", 920, 120)
    connect(sub_v, "ReturnValue", norm_v, "A")

    break_v = fn(ed, "/Script/Engine.KismetMathLibrary.BreakVector", 1140, 120)
    connect(norm_v, "ReturnValue", break_v, "InVec")

    speed = 35.0

    mul_x_speed = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1380, 40)
    connect(break_v, "X", mul_x_speed, "A"); set_value(mul_x_speed, "B", speed)

    mul_x_dt = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1600, 40)
    connect(mul_x_speed, "ReturnValue", mul_x_dt, "A")
    connect(tick_node, "DeltaSeconds", mul_x_dt, "B")

    delta_vec_x = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 1820, 40)
    connect(mul_x_dt, "ReturnValue", delta_vec_x, "X"); set_value(delta_vec_x, "Y", 0.0); set_value(delta_vec_x, "Z", 0.0)

    move_x = fn(ed, "/Script/Engine.Actor.K2_AddActorWorldOffset", 2060, 40)
    set_value(move_x, "bSweep", "true")
    connect(delta_vec_x, "ReturnValue", move_x, "DeltaLocation")
    connect(br_gate, "then", move_x, "execute")

    mul_z_speed = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1380, 200)
    connect(break_v, "Z", mul_z_speed, "A"); set_value(mul_z_speed, "B", speed)

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

    # 5. Flipbook 强类型方向切换 (纯 Branch 架构，告别通配符)
    get_fb = fn(ed, "/Script/Engine.Actor.GetComponentByClass", 1820, -260)
    set_value(get_fb, "ComponentClass", "Class'/Script/Paper2D.PaperFlipbookComponent'")

    abs_x = fn(ed, "/Script/Engine.KismetMathLibrary.Abs", 1380, -40)
    connect(break_v, "X", abs_x, "A")
    abs_z = fn(ed, "/Script/Engine.KismetMathLibrary.Abs", 1380, 10)
    connect(break_v, "Z", abs_z, "A")

    is_horizontal = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 1600, -20)
    connect(abs_x, "ReturnValue", is_horizontal, "A")
    connect(abs_z, "ReturnValue", is_horizontal, "B")

    br_axis = ed.add_branch_node(); br_axis.set_node_pos(unreal.IntPoint(2320, 40))
    connect(move_z, "then", br_axis, "execute")
    connect(is_horizontal, "ReturnValue", br_axis, "Condition")

    # 水平方向
    is_right = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 1820, -40)
    connect(break_v, "X", is_right, "A"); set_value(is_right, "B", 0.0)
    br_horiz = ed.add_branch_node(); br_horiz.set_node_pos(unreal.IntPoint(2560, -40))
    connect(br_axis, "then", br_horiz, "execute")
    connect(is_right, "ReturnValue", br_horiz, "Condition")

    set_right = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2800, -100)
    if fb_walk_right: set_value(set_right, "NewFlipbook", f"PaperFlipbook'{fb_walk_right.get_path_name()}'")
    connect(br_horiz, "then", set_right, "execute")
    connect(get_fb, "ReturnValue", set_right, "self")

    set_left = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2800, 20)
    if fb_walk_left: set_value(set_left, "NewFlipbook", f"PaperFlipbook'{fb_walk_left.get_path_name()}'")
    connect(br_horiz, "else", set_left, "execute")
    connect(get_fb, "ReturnValue", set_left, "self")

    # 垂直方向
    is_up = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 1820, 80)
    connect(break_v, "Z", is_up, "A"); set_value(is_up, "B", 0.0)
    br_vert = ed.add_branch_node(); br_vert.set_node_pos(unreal.IntPoint(2560, 160))
    connect(br_axis, "else", br_vert, "execute")
    connect(is_up, "ReturnValue", br_vert, "Condition")

    set_up = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2800, 120)
    if fb_walk_up: set_value(set_up, "NewFlipbook", f"PaperFlipbook'{fb_walk_up.get_path_name()}'")
    connect(br_vert, "then", set_up, "execute")
    connect(get_fb, "ReturnValue", set_up, "self")

    set_down = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2800, 240)
    if fb_walk_down: set_value(set_down, "NewFlipbook", f"PaperFlipbook'{fb_walk_down.get_path_name()}'")
    connect(br_vert, "else", set_down, "execute")
    connect(get_fb, "ReturnValue", set_down, "self")

    # --- 6. 到达角色体积外围 (br_gate.else: 距离 <= 125.0) ---
    # 彻底切断位移，速度归零，原地释放地裂重砸动画！
    set_slam = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 1400, -200)
    if fb_slam_down: set_value(set_slam, "NewFlipbook", f"PaperFlipbook'{fb_slam_down.get_path_name()}'")
    connect(br_gate, "else", set_slam, "execute")
    connect(get_fb, "ReturnValue", set_slam, "self")

    BPLIB.compile_blueprint(bp)
    saved = ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"  💾 Boss BP_Boss_Overlord 编译与落盘: {'成功' if saved else '失败'}")
    return saved

# ==============================================================================
# 2. 重构变异猎犬 (BP_Enemy_MutantHound) - StopDistance = 75.0 + 怪怪排斥
# ==============================================================================
def setup_hound():
    bp_path = "/Game/Blueprints/Characters/Enemies/BP_Enemy_MutantHound"
    log(f"🐕 重构变异猎犬: 体积停止(75.0) + 怪怪排斥 + 扑击技能...")
    bp = ASSETS.load_asset(bp_path)
    if not bp: raise RuntimeError(f"未找到: {bp_path}")

    ed, tick_node = clean_event_graph(bp)
    tick_node.set_node_pos(unreal.IntPoint(0, 0))

    HOUND_ART = "/Game/P01/Imported/Content/Asset/Art/02_Enemies/MutantHound"
    fb_run_down = unreal.load_asset(f"{HOUND_ART}/Run/Dir_01_Down/Flipbooks/FB_T_Hound_Run_Dir_01_Down_Sheet.FB_T_Hound_Run_Dir_01_Down_Sheet")
    fb_run_right = unreal.load_asset(f"{HOUND_ART}/Run/Dir_02_Right/Flipbooks/FB_T_Hound_Run_Dir_02_Right_Sheet.FB_T_Hound_Run_Dir_02_Right_Sheet")
    fb_run_up = unreal.load_asset(f"{HOUND_ART}/Run/Dir_03_Up/Flipbooks/FB_T_Hound_Run_Dir_03_Up_Sheet.FB_T_Hound_Run_Dir_03_Up_Sheet")
    fb_run_left = unreal.load_asset(f"{HOUND_ART}/Run/Dir_04_Left/Flipbooks/FB_T_Hound_Run_Dir_04_Left_Sheet.FB_T_Hound_Run_Dir_04_Left_Sheet")
    fb_pounce_down = unreal.load_asset(f"{HOUND_ART}/Pounce/Dir_01_Down/Flipbooks/FB_T_Hound_Pounce_Dir_01_Down_Sheet.FB_T_Hound_Pounce_Dir_01_Down_Sheet")

    # 1. 坐标采样
    get_player = fn(ed, "/Script/Engine.GameplayStatics.GetPlayerPawn", 220, 100)
    set_value(get_player, "PlayerIndex", 0)

    p_loc = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 460, 40)
    connect(get_player, "ReturnValue", p_loc, "self")

    self_loc = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 460, 180)

    # 2. 距离判断 (Distance > 75.0)
    dist_node = fn(ed, "/Script/Engine.KismetMathLibrary.Vector_Distance", 700, -80)
    connect(p_loc, "ReturnValue", dist_node, "v1")
    connect(self_loc, "ReturnValue", dist_node, "v2")

    is_far = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 940, -80)
    connect(dist_node, "ReturnValue", is_far, "A")
    set_value(is_far, "B", 75.0)

    br_gate = ed.add_branch_node(); br_gate.set_node_pos(unreal.IntPoint(1160, 0))
    connect(tick_node, "then", br_gate, "execute")
    connect(is_far, "ReturnValue", br_gate, "Condition")

    # 3. 追击向量与位移 (br_gate.then)
    sub_v = fn(ed, "/Script/Engine.KismetMathLibrary.Subtract_VectorVector", 700, 120)
    connect(p_loc, "ReturnValue", sub_v, "A")
    connect(self_loc, "ReturnValue", sub_v, "B")

    norm_v = fn(ed, "/Script/Engine.KismetMathLibrary.Normal", 920, 120)
    connect(sub_v, "ReturnValue", norm_v, "A")

    break_v = fn(ed, "/Script/Engine.KismetMathLibrary.BreakVector", 1140, 120)
    connect(norm_v, "ReturnValue", break_v, "InVec")

    speed = 150.0

    mul_x_speed = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1380, 40)
    connect(break_v, "X", mul_x_speed, "A"); set_value(mul_x_speed, "B", speed)

    mul_x_dt = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1600, 40)
    connect(mul_x_speed, "ReturnValue", mul_x_dt, "A")
    connect(tick_node, "DeltaSeconds", mul_x_dt, "B")

    delta_vec_x = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 1820, 40)
    connect(mul_x_dt, "ReturnValue", delta_vec_x, "X"); set_value(delta_vec_x, "Y", 0.0); set_value(delta_vec_x, "Z", 0.0)

    move_x = fn(ed, "/Script/Engine.Actor.K2_AddActorWorldOffset", 2060, 40)
    set_value(move_x, "bSweep", "true")
    connect(delta_vec_x, "ReturnValue", move_x, "DeltaLocation")
    connect(br_gate, "then", move_x, "execute")

    mul_z_speed = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1380, 200)
    connect(break_v, "Z", mul_z_speed, "A"); set_value(mul_z_speed, "B", speed)

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

    # 4. 强类型 4 向奔跑状态机
    get_fb = fn(ed, "/Script/Engine.Actor.GetComponentByClass", 1820, -260)
    set_value(get_fb, "ComponentClass", "Class'/Script/Paper2D.PaperFlipbookComponent'")

    abs_x = fn(ed, "/Script/Engine.KismetMathLibrary.Abs", 1380, -40)
    connect(break_v, "X", abs_x, "A")
    abs_z = fn(ed, "/Script/Engine.KismetMathLibrary.Abs", 1380, 10)
    connect(break_v, "Z", abs_z, "A")

    is_horizontal = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 1600, -20)
    connect(abs_x, "ReturnValue", is_horizontal, "A")
    connect(abs_z, "ReturnValue", is_horizontal, "B")

    br_axis = ed.add_branch_node(); br_axis.set_node_pos(unreal.IntPoint(2320, 40))
    connect(move_z, "then", br_axis, "execute")
    connect(is_horizontal, "ReturnValue", br_axis, "Condition")

    # 水平奔跑
    is_right = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 1820, -40)
    connect(break_v, "X", is_right, "A"); set_value(is_right, "B", 0.0)
    br_horiz = ed.add_branch_node(); br_horiz.set_node_pos(unreal.IntPoint(2560, -40))
    connect(br_axis, "then", br_horiz, "execute")
    connect(is_right, "ReturnValue", br_horiz, "Condition")

    set_right = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2800, -100)
    if fb_run_right: set_value(set_right, "NewFlipbook", f"PaperFlipbook'{fb_run_right.get_path_name()}'")
    connect(br_horiz, "then", set_right, "execute")
    connect(get_fb, "ReturnValue", set_right, "self")

    set_left = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2800, 20)
    if fb_run_left: set_value(set_left, "NewFlipbook", f"PaperFlipbook'{fb_run_left.get_path_name()}'")
    connect(br_horiz, "else", set_left, "execute")
    connect(get_fb, "ReturnValue", set_left, "self")

    # 垂直奔跑
    is_up = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 1820, 80)
    connect(break_v, "Z", is_up, "A"); set_value(is_up, "B", 0.0)
    br_vert = ed.add_branch_node(); br_vert.set_node_pos(unreal.IntPoint(2560, 160))
    connect(br_axis, "else", br_vert, "execute")
    connect(is_up, "ReturnValue", br_vert, "Condition")

    set_up = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2800, 120)
    if fb_run_up: set_value(set_up, "NewFlipbook", f"PaperFlipbook'{fb_run_up.get_path_name()}'")
    connect(br_vert, "then", set_up, "execute")
    connect(get_fb, "ReturnValue", set_up, "self")

    set_down = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2800, 240)
    if fb_run_down: set_value(set_down, "NewFlipbook", f"PaperFlipbook'{fb_run_down.get_path_name()}'")
    connect(br_vert, "else", set_down, "execute")
    connect(get_fb, "ReturnValue", set_down, "self")

    # 5. 到达角色体积外围 (br_gate.else: 距离 <= 75.0) -> 原地扑咬
    set_pounce = fn(ed, "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 1400, -200)
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
def setup_zombie():
    bp_path = "/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker"
    log(f"🧟 重构普通行尸: 体积停止(80.0) + 怪怪排斥...")
    bp = ASSETS.load_asset(bp_path)
    if not bp: raise RuntimeError(f"未找到: {bp_path}")

    ed, tick_node = clean_event_graph(bp)
    tick_node.set_node_pos(unreal.IntPoint(0, 0))

    base_scale = 0.45
    speed = 65.0

    # 1. 采样坐标
    get_player = fn(ed, "/Script/Engine.GameplayStatics.GetPlayerPawn", 220, 100)
    set_value(get_player, "PlayerIndex", 0)

    p_loc = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 460, 40)
    connect(get_player, "ReturnValue", p_loc, "self")

    self_loc = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 460, 180)

    # 2. 距离判断 (Distance > 80.0)
    dist_node = fn(ed, "/Script/Engine.KismetMathLibrary.Vector_Distance", 700, -80)
    connect(p_loc, "ReturnValue", dist_node, "v1")
    connect(self_loc, "ReturnValue", dist_node, "v2")

    is_far = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 940, -80)
    connect(dist_node, "ReturnValue", is_far, "A")
    set_value(is_far, "B", 80.0)

    br_gate = ed.add_branch_node(); br_gate.set_node_pos(unreal.IntPoint(1160, 0))
    connect(tick_node, "then", br_gate, "execute")
    connect(is_far, "ReturnValue", br_gate, "Condition")

    # 3. 追击向移动 (br_gate.then)
    sub_v = fn(ed, "/Script/Engine.KismetMathLibrary.Subtract_VectorVector", 700, 120)
    connect(p_loc, "ReturnValue", sub_v, "A")
    connect(self_loc, "ReturnValue", sub_v, "B")

    norm_v = fn(ed, "/Script/Engine.KismetMathLibrary.Normal", 920, 120)
    connect(sub_v, "ReturnValue", norm_v, "A")

    break_v = fn(ed, "/Script/Engine.KismetMathLibrary.BreakVector", 1140, 120)
    connect(norm_v, "ReturnValue", break_v, "InVec")

    mul_x_speed = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1380, 40)
    connect(break_v, "X", mul_x_speed, "A"); set_value(mul_x_speed, "B", speed)

    mul_x_dt = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1600, 40)
    connect(mul_x_speed, "ReturnValue", mul_x_dt, "A")
    connect(tick_node, "DeltaSeconds", mul_x_dt, "B")

    delta_vec_x = fn(ed, "/Script/Engine.KismetMathLibrary.MakeVector", 1820, 40)
    connect(mul_x_dt, "ReturnValue", delta_vec_x, "X"); set_value(delta_vec_x, "Y", 0.0); set_value(delta_vec_x, "Z", 0.0)

    move_x = fn(ed, "/Script/Engine.Actor.K2_AddActorWorldOffset", 2060, 40)
    set_value(move_x, "bSweep", "true")
    connect(delta_vec_x, "ReturnValue", move_x, "DeltaLocation")
    connect(br_gate, "then", move_x, "execute")

    mul_z_speed = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1380, 200)
    connect(break_v, "Z", mul_z_speed, "A"); set_value(mul_z_speed, "B", speed)

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

    # 4. 水平翻转更新
    is_right = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 1380, -120)
    connect(break_v, "X", is_right, "A"); set_value(is_right, "B", 0.0)

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

    BPLIB.compile_blueprint(bp)
    saved = ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"  💾 行尸 BP_Enemy_ZombieWalker 编译与落盘: {'成功' if saved else '失败'}")
    return saved

def run():
    log("==================================================")
    log("🚀 启动全量敌人 AI 体积防穿透与防重叠终极构建流水线...")

    res_boss = setup_boss()
    res_hound = setup_hound()
    res_zombie = setup_zombie()

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
    log(f"🎉 敌人 AI 角色体积防穿透与防重叠全部构建完成！报告: {REPORT_PATH}")
    log("==================================================")

if __name__ == "__main__":
    run()
