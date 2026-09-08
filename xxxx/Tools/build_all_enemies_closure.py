# -*- coding: utf-8 -*-
"""
build_all_enemies_closure.py
三大敌人 AI 体积停止与怪与怪防重叠闭环重构：
1. BP_Boss_Overlord: 停止距离 125.0, 原地地裂重砸 Ground_Slam, 接触推开 40 uu
2. BP_Enemy_MutantHound: 停止距离 75.0, 原地凶猛扑咬 Pounce, 4 向奔跑, 接触推开 40 uu
3. BP_Enemy_ZombieWalker: 停止距离 80.0, 纯 Branch 水平翻转, 接触推开 40 uu
"""
import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary
ASSETS = unreal.EditorAssetLibrary

def log(msg):
    unreal.log(f"[ALL_ENEMIES] {msg}")
    print(f"[ALL_ENEMIES] {msg}", flush=True)

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

def inject_monster_repel_overlap(bp, ed, base_x=0, base_y=450):
    log("  🛡️ 注入【怪与怪接触弹开防重叠闭环】...")
    overlap_evt = BPLIB.add_event_override(bp, "ReceiveActorBeginOverlap", unreal.IntPoint(base_x, base_y))
    
    get_player = ed.add_call_function_node("/Script/Engine.GameplayStatics.GetPlayerPawn")
    get_player.set_node_pos(unreal.IntPoint(base_x + 220, base_y + 120))
    set_value(get_player, "PlayerIndex", 0)
    
    not_player = ed.add_call_function_node("/Script/Engine.KismetMathLibrary.NotEqual_ObjectObject")
    not_player.set_node_pos(unreal.IntPoint(base_x + 460, base_y + 60))
    connect(overlap_evt, "OtherActor", not_player, "A")
    connect(get_player, "ReturnValue", not_player, "B")
    
    br_not_player = ed.add_branch_node()
    br_not_player.set_node_pos(unreal.IntPoint(base_x + 680, base_y))
    connect(overlap_evt, "then", br_not_player, "execute")
    connect(not_player, "ReturnValue", br_not_player, "Condition")
    
    self_loc = ed.add_call_function_node("/Script/Engine.Actor.K2_GetActorLocation")
    self_loc.set_node_pos(unreal.IntPoint(base_x + 680, base_y + 140))
    
    other_loc = ed.add_call_function_node("/Script/Engine.Actor.K2_GetActorLocation")
    other_loc.set_node_pos(unreal.IntPoint(base_x + 680, base_y + 260))
    connect(overlap_evt, "OtherActor", other_loc, "self")
    
    sub_v = ed.add_call_function_node("/Script/Engine.KismetMathLibrary.Subtract_VectorVector")
    sub_v.set_node_pos(unreal.IntPoint(base_x + 920, base_y + 180))
    connect(self_loc, "ReturnValue", sub_v, "A")
    connect(other_loc, "ReturnValue", sub_v, "B")
    
    norm_v = ed.add_call_function_node("/Script/Engine.KismetMathLibrary.Normal")
    norm_v.set_node_pos(unreal.IntPoint(base_x + 1140, base_y + 180))
    connect(sub_v, "ReturnValue", norm_v, "A")
    
    push_vec = ed.add_call_function_node("/Script/Engine.KismetMathLibrary.Multiply_VectorVector")
    push_vec.set_node_pos(unreal.IntPoint(base_x + 1360, base_y + 180))
    connect(norm_v, "ReturnValue", push_vec, "A")
    set_value(push_vec, "B", "40.0, 0.0, 40.0")
    
    push_offset = ed.add_call_function_node("/Script/Engine.Actor.K2_AddActorWorldOffset")
    push_offset.set_node_pos(unreal.IntPoint(base_x + 1600, base_y))
    set_value(push_offset, "bSweep", "false")
    connect(br_not_player, "then", push_offset, "execute")
    connect(push_vec, "ReturnValue", push_offset, "DeltaLocation")
    log("    ✅ 怪与怪接触反弹排斥逻辑创建就绪！")

# ==============================================================================
# 1. 变异猎犬
# ==============================================================================
def setup_hound():
    bp_path = "/Game/Blueprints/Characters/Enemies/BP_Enemy_MutantHound"
    log(f"🐕 重构变异猎犬: 停止距离(75.0) + 凶猛扑咬 + 怪怪排斥...")
    bp = ASSETS.load_asset(bp_path)
    ed, tick_node = clean_event_graph(bp)
    tick_node.set_node_pos(unreal.IntPoint(0, 0))

    HOUND_ART = "/Game/P01/Imported/Content/Asset/Art/02_Enemies/MutantHound"
    fb_run_down = unreal.load_asset(f"{HOUND_ART}/Run/Dir_01_Down/Flipbooks/FB_T_Hound_Run_Dir_01_Down_Sheet.FB_T_Hound_Run_Dir_01_Down_Sheet")
    fb_run_right = unreal.load_asset(f"{HOUND_ART}/Run/Dir_02_Right/Flipbooks/FB_T_Hound_Run_Dir_02_Right_Sheet.FB_T_Hound_Run_Dir_02_Right_Sheet")
    fb_run_up = unreal.load_asset(f"{HOUND_ART}/Run/Dir_03_Up/Flipbooks/FB_T_Hound_Run_Dir_03_Up_Sheet.FB_T_Hound_Run_Dir_03_Up_Sheet")
    fb_run_left = unreal.load_asset(f"{HOUND_ART}/Run/Dir_04_Left/Flipbooks/FB_T_Hound_Run_Dir_04_Left_Sheet.FB_T_Hound_Run_Dir_04_Left_Sheet")
    fb_pounce_down = unreal.load_asset(f"{HOUND_ART}/Pounce/Dir_01_Down/Flipbooks/FB_T_Hound_Pounce_Dir_01_Down_Sheet.FB_T_Hound_Pounce_Dir_01_Down_Sheet")

    # 1. 采样玩家与自身坐标
    get_player = ed.add_call_function_node("/Script/Engine.GameplayStatics.GetPlayerPawn")
    get_player.set_node_pos(unreal.IntPoint(220, 100))
    set_value(get_player, "PlayerIndex", 0)

    p_loc = ed.add_call_function_node("/Script/Engine.Actor.K2_GetActorLocation")
    p_loc.set_node_pos(unreal.IntPoint(460, 40))
    connect(get_player, "ReturnValue", p_loc, "self")

    self_loc = ed.add_call_function_node("/Script/Engine.Actor.K2_GetActorLocation")
    self_loc.set_node_pos(unreal.IntPoint(460, 180))

    # 2. 距离判断 (Distance > 75.0)
    dist_node = ed.add_call_function_node("/Script/Engine.KismetMathLibrary.Vector_Distance")
    dist_node.set_node_pos(unreal.IntPoint(700, -80))
    connect(p_loc, "ReturnValue", dist_node, "v1")
    connect(self_loc, "ReturnValue", dist_node, "v2")

    is_far = ed.add_call_function_node("/Script/Engine.KismetMathLibrary.Greater_DoubleDouble")
    is_far.set_node_pos(unreal.IntPoint(940, -80))
    connect(dist_node, "ReturnValue", is_far, "A")
    set_value(is_far, "B", 75.0)

    br_gate = ed.add_branch_node()
    br_gate.set_node_pos(unreal.IntPoint(1160, 0))
    connect(tick_node, "then", br_gate, "execute")
    connect(is_far, "ReturnValue", br_gate, "Condition")

    # 3. 追击向移动 (br_gate.then: 距离 > 75.0)
    sub_v = ed.add_call_function_node("/Script/Engine.KismetMathLibrary.Subtract_VectorVector")
    sub_v.set_node_pos(unreal.IntPoint(700, 120))
    connect(p_loc, "ReturnValue", sub_v, "A")
    connect(self_loc, "ReturnValue", sub_v, "B")

    norm_v = ed.add_call_function_node("/Script/Engine.KismetMathLibrary.Normal")
    norm_v.set_node_pos(unreal.IntPoint(920, 120))
    connect(sub_v, "ReturnValue", norm_v, "A")

    break_v = ed.add_call_function_node("/Script/Engine.KismetMathLibrary.BreakVector")
    break_v.set_node_pos(unreal.IntPoint(1140, 120))
    connect(norm_v, "ReturnValue", break_v, "InVec")

    speed = 150.0

    mul_x_speed = ed.add_call_function_node("/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble")
    mul_x_speed.set_node_pos(unreal.IntPoint(1380, 40))
    connect(break_v, "X", mul_x_speed, "A"); set_value(mul_x_speed, "B", speed)

    mul_x_dt = ed.add_call_function_node("/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble")
    mul_x_dt.set_node_pos(unreal.IntPoint(1600, 40))
    connect(mul_x_speed, "ReturnValue", mul_x_dt, "A")
    connect(tick_node, "DeltaSeconds", mul_x_dt, "B")

    delta_vec_x = ed.add_call_function_node("/Script/Engine.KismetMathLibrary.MakeVector")
    delta_vec_x.set_node_pos(unreal.IntPoint(1820, 40))
    connect(mul_x_dt, "ReturnValue", delta_vec_x, "X"); set_value(delta_vec_x, "Y", 0.0); set_value(delta_vec_x, "Z", 0.0)

    move_x = ed.add_call_function_node("/Script/Engine.Actor.K2_AddActorWorldOffset")
    move_x.set_node_pos(unreal.IntPoint(2060, 40))
    set_value(move_x, "bSweep", "true")
    connect(delta_vec_x, "ReturnValue", move_x, "DeltaLocation")
    connect(br_gate, "then", move_x, "execute")

    mul_z_speed = ed.add_call_function_node("/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble")
    mul_z_speed.set_node_pos(unreal.IntPoint(1380, 200))
    connect(break_v, "Z", mul_z_speed, "A"); set_value(mul_z_speed, "B", speed)

    mul_z_dt = ed.add_call_function_node("/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble")
    mul_z_dt.set_node_pos(unreal.IntPoint(1600, 200))
    connect(mul_z_speed, "ReturnValue", mul_z_dt, "A")
    connect(tick_node, "DeltaSeconds", mul_z_dt, "B")

    delta_vec_z = ed.add_call_function_node("/Script/Engine.KismetMathLibrary.MakeVector")
    delta_vec_z.set_node_pos(unreal.IntPoint(1820, 200))
    set_value(delta_vec_z, "X", 0.0); set_value(delta_vec_z, "Y", 0.0)
    connect(mul_z_dt, "ReturnValue", delta_vec_z, "Z")

    move_z = ed.add_call_function_node("/Script/Engine.Actor.K2_AddActorWorldOffset")
    move_z.set_node_pos(unreal.IntPoint(2060, 200))
    set_value(move_z, "bSweep", "true")
    connect(delta_vec_z, "ReturnValue", move_z, "DeltaLocation")
    connect(move_x, "then", move_z, "execute")

    # 4. 强类型 4 向奔跑状态机
    get_fb = ed.add_call_function_node("/Script/Engine.Actor.GetComponentByClass")
    get_fb.set_node_pos(unreal.IntPoint(1820, -260))
    set_value(get_fb, "ComponentClass", "Class'/Script/Paper2D.PaperFlipbookComponent'")

    abs_x = ed.add_call_function_node("/Script/Engine.KismetMathLibrary.Abs")
    abs_x.set_node_pos(unreal.IntPoint(1380, -40))
    connect(break_v, "X", abs_x, "A")
    abs_z = ed.add_call_function_node("/Script/Engine.KismetMathLibrary.Abs")
    abs_z.set_node_pos(unreal.IntPoint(1380, 10))
    connect(break_v, "Z", abs_z, "A")

    is_horizontal = ed.add_call_function_node("/Script/Engine.KismetMathLibrary.Greater_DoubleDouble")
    is_horizontal.set_node_pos(unreal.IntPoint(1600, -20))
    connect(abs_x, "ReturnValue", is_horizontal, "A")
    connect(abs_z, "ReturnValue", is_horizontal, "B")

    br_axis = ed.add_branch_node(); br_axis.set_node_pos(unreal.IntPoint(2320, 40))
    connect(move_z, "then", br_axis, "execute")
    connect(is_horizontal, "ReturnValue", br_axis, "Condition")

    # 水平奔跑
    is_right = ed.add_call_function_node("/Script/Engine.KismetMathLibrary.Greater_DoubleDouble")
    is_right.set_node_pos(unreal.IntPoint(1820, -40))
    connect(break_v, "X", is_right, "A"); set_value(is_right, "B", 0.0)
    br_horiz = ed.add_branch_node(); br_horiz.set_node_pos(unreal.IntPoint(2560, -40))
    connect(br_axis, "then", br_horiz, "execute")
    connect(is_right, "ReturnValue", br_horiz, "Condition")

    set_right = ed.add_call_function_node("/Script/Paper2D.PaperFlipbookComponent.SetFlipbook")
    set_right.set_node_pos(unreal.IntPoint(2800, -100))
    if fb_run_right: set_value(set_right, "NewFlipbook", f"PaperFlipbook'{fb_run_right.get_path_name()}'")
    connect(br_horiz, "then", set_right, "execute")
    connect(get_fb, "ReturnValue", set_right, "self")

    set_left = ed.add_call_function_node("/Script/Paper2D.PaperFlipbookComponent.SetFlipbook")
    set_left.set_node_pos(unreal.IntPoint(2800, 20))
    if fb_run_left: set_value(set_left, "NewFlipbook", f"PaperFlipbook'{fb_run_left.get_path_name()}'")
    connect(br_horiz, "else", set_left, "execute")
    connect(get_fb, "ReturnValue", set_left, "self")

    # 垂直奔跑
    is_up = ed.add_call_function_node("/Script/Engine.KismetMathLibrary.Greater_DoubleDouble")
    is_up.set_node_pos(unreal.IntPoint(1820, 80))
    connect(break_v, "Z", is_up, "A"); set_value(is_up, "B", 0.0)
    br_vert = ed.add_branch_node(); br_vert.set_node_pos(unreal.IntPoint(2560, 160))
    connect(br_axis, "else", br_vert, "execute")
    connect(is_up, "ReturnValue", br_vert, "Condition")

    set_up = ed.add_call_function_node("/Script/Paper2D.PaperFlipbookComponent.SetFlipbook")
    set_up.set_node_pos(unreal.IntPoint(2800, 120))
    if fb_run_up: set_value(set_up, "NewFlipbook", f"PaperFlipbook'{fb_run_up.get_path_name()}'")
    connect(br_vert, "then", set_up, "execute")
    connect(get_fb, "ReturnValue", set_up, "self")

    set_down = ed.add_call_function_node("/Script/Paper2D.PaperFlipbookComponent.SetFlipbook")
    set_down.set_node_pos(unreal.IntPoint(2800, 240))
    if fb_run_down: set_value(set_down, "NewFlipbook", f"PaperFlipbook'{fb_run_down.get_path_name()}'")
    connect(br_vert, "else", set_down, "execute")
    connect(get_fb, "ReturnValue", set_down, "self")

    # 5. 到达角色体积外围 (br_gate.else: 距离 <= 75.0) -> 原地扑咬
    set_pounce = ed.add_call_function_node("/Script/Paper2D.PaperFlipbookComponent.SetFlipbook")
    set_pounce.set_node_pos(unreal.IntPoint(1400, -200))
    if fb_pounce_down: set_value(set_pounce, "NewFlipbook", f"PaperFlipbook'{fb_pounce_down.get_path_name()}'")
    connect(br_gate, "else", set_pounce, "execute")
    connect(get_fb, "ReturnValue", set_pounce, "self")

    # 6. 注入怪与怪反弹排斥
    inject_monster_repel_overlap(bp, ed, 0, 450)

    BPLIB.compile_blueprint(bp)
    saved = ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"  💾 变异猎犬 BP_Enemy_MutantHound 构建与落盘: {'成功' if saved else '失败'}")
    return saved

# ==============================================================================
# 2. 普通行尸
# ==============================================================================
def setup_zombie():
    bp_path = "/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker"
    log(f"🧟 重构普通行尸: 停止距离(80.0) + 水平翻转 + 怪怪排斥...")
    bp = ASSETS.load_asset(bp_path)
    ed, tick_node = clean_event_graph(bp)
    tick_node.set_node_pos(unreal.IntPoint(0, 0))

    base_scale = 0.45
    speed = 65.0

    # 1. 采样坐标
    get_player = ed.add_call_function_node("/Script/Engine.GameplayStatics.GetPlayerPawn")
    get_player.set_node_pos(unreal.IntPoint(220, 100))
    set_value(get_player, "PlayerIndex", 0)

    p_loc = ed.add_call_function_node("/Script/Engine.Actor.K2_GetActorLocation")
    p_loc.set_node_pos(unreal.IntPoint(460, 40))
    connect(get_player, "ReturnValue", p_loc, "self")

    self_loc = ed.add_call_function_node("/Script/Engine.Actor.K2_GetActorLocation")
    self_loc.set_node_pos(unreal.IntPoint(460, 180))

    # 2. 距离判断 (Distance > 80.0)
    dist_node = ed.add_call_function_node("/Script/Engine.KismetMathLibrary.Vector_Distance")
    dist_node.set_node_pos(unreal.IntPoint(700, -80))
    connect(p_loc, "ReturnValue", dist_node, "v1")
    connect(self_loc, "ReturnValue", dist_node, "v2")

    is_far = ed.add_call_function_node("/Script/Engine.KismetMathLibrary.Greater_DoubleDouble")
    is_far.set_node_pos(unreal.IntPoint(940, -80))
    connect(dist_node, "ReturnValue", is_far, "A")
    set_value(is_far, "B", 80.0)

    br_gate = ed.add_branch_node()
    br_gate.set_node_pos(unreal.IntPoint(1160, 0))
    connect(tick_node, "then", br_gate, "execute")
    connect(is_far, "ReturnValue", br_gate, "Condition")

    # 3. 追击向移动 (br_gate.then)
    sub_v = ed.add_call_function_node("/Script/Engine.KismetMathLibrary.Subtract_VectorVector")
    sub_v.set_node_pos(unreal.IntPoint(700, 120))
    connect(p_loc, "ReturnValue", sub_v, "A")
    connect(self_loc, "ReturnValue", sub_v, "B")

    norm_v = ed.add_call_function_node("/Script/Engine.KismetMathLibrary.Normal")
    norm_v.set_node_pos(unreal.IntPoint(920, 120))
    connect(sub_v, "ReturnValue", norm_v, "A")

    break_v = ed.add_call_function_node("/Script/Engine.KismetMathLibrary.BreakVector")
    break_v.set_node_pos(unreal.IntPoint(1140, 120))
    connect(norm_v, "ReturnValue", break_v, "InVec")

    mul_x_speed = ed.add_call_function_node("/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble")
    mul_x_speed.set_node_pos(unreal.IntPoint(1380, 40))
    connect(break_v, "X", mul_x_speed, "A"); set_value(mul_x_speed, "B", speed)

    mul_x_dt = ed.add_call_function_node("/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble")
    mul_x_dt.set_node_pos(unreal.IntPoint(1600, 40))
    connect(mul_x_speed, "ReturnValue", mul_x_dt, "A")
    connect(tick_node, "DeltaSeconds", mul_x_dt, "B")

    delta_vec_x = ed.add_call_function_node("/Script/Engine.KismetMathLibrary.MakeVector")
    delta_vec_x.set_node_pos(unreal.IntPoint(1820, 40))
    connect(mul_x_dt, "ReturnValue", delta_vec_x, "X"); set_value(delta_vec_x, "Y", 0.0); set_value(delta_vec_x, "Z", 0.0)

    move_x = ed.add_call_function_node("/Script/Engine.Actor.K2_AddActorWorldOffset")
    move_x.set_node_pos(unreal.IntPoint(2060, 40))
    set_value(move_x, "bSweep", "true")
    connect(delta_vec_x, "ReturnValue", move_x, "DeltaLocation")
    connect(br_gate, "then", move_x, "execute")

    mul_z_speed = ed.add_call_function_node("/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble")
    mul_z_speed.set_node_pos(unreal.IntPoint(1380, 200))
    connect(break_v, "Z", mul_z_speed, "A"); set_value(mul_z_speed, "B", speed)

    mul_z_dt = ed.add_call_function_node("/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble")
    mul_z_dt.set_node_pos(unreal.IntPoint(1600, 200))
    connect(mul_z_speed, "ReturnValue", mul_z_dt, "A")
    connect(tick_node, "DeltaSeconds", mul_z_dt, "B")

    delta_vec_z = ed.add_call_function_node("/Script/Engine.KismetMathLibrary.MakeVector")
    delta_vec_z.set_node_pos(unreal.IntPoint(1820, 200))
    set_value(delta_vec_z, "X", 0.0); set_value(delta_vec_z, "Y", 0.0)
    connect(mul_z_dt, "ReturnValue", delta_vec_z, "Z")

    move_z = ed.add_call_function_node("/Script/Engine.Actor.K2_AddActorWorldOffset")
    move_z.set_node_pos(unreal.IntPoint(2060, 200))
    set_value(move_z, "bSweep", "true")
    connect(delta_vec_z, "ReturnValue", move_z, "DeltaLocation")
    connect(move_x, "then", move_z, "execute")

    # 4. 水平翻转更新 (纯 Branch 架构，绝对安全强类型)
    get_fb = ed.add_call_function_node("/Script/Engine.Actor.GetComponentByClass")
    get_fb.set_node_pos(unreal.IntPoint(1820, -260))
    set_value(get_fb, "ComponentClass", "Class'/Script/Paper2D.PaperFlipbookComponent'")

    is_right = ed.add_call_function_node("/Script/Engine.KismetMathLibrary.Greater_DoubleDouble")
    is_right.set_node_pos(unreal.IntPoint(1380, -120))
    connect(break_v, "X", is_right, "A"); set_value(is_right, "B", 0.0)

    br_flip = ed.add_branch_node()
    br_flip.set_node_pos(unreal.IntPoint(1600, -120))
    connect(move_z, "then", br_flip, "execute")
    connect(is_right, "ReturnValue", br_flip, "Condition")

    # 右侧: ScaleX = -base_scale
    set_scale_r = ed.add_call_function_node("/Script/Engine.SceneComponent.SetRelativeScale3D")
    set_scale_r.set_node_pos(unreal.IntPoint(1860, -180))
    set_value(set_scale_r, "NewScale3D", f"{-base_scale}, {base_scale}, {base_scale}")
    connect(br_flip, "then", set_scale_r, "execute")
    connect(get_fb, "ReturnValue", set_scale_r, "self")

    # 左侧: ScaleX = base_scale
    set_scale_l = ed.add_call_function_node("/Script/Engine.SceneComponent.SetRelativeScale3D")
    set_scale_l.set_node_pos(unreal.IntPoint(1860, -60))
    set_value(set_scale_l, "NewScale3D", f"{base_scale}, {base_scale}, {base_scale}")
    connect(br_flip, "else", set_scale_l, "execute")
    connect(get_fb, "ReturnValue", set_scale_l, "self")

    # 5. 注入怪与怪反弹排斥
    inject_monster_repel_overlap(bp, ed, 0, 450)

    BPLIB.compile_blueprint(bp)
    saved = ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"  💾 行尸 BP_Enemy_ZombieWalker 构建与落盘: {'成功' if saved else '失败'}")
    return saved

def run():
    log("==================================================")
    log("🚀 启动变异猎犬与行尸 AI 体积停止与怪怪排斥全量构建...")
    r_hound = setup_hound()
    r_zombie = setup_zombie()
    log(f"🎉 猎犬构建={r_hound}, 行尸构建={r_zombie}")
    log("==================================================")

if __name__ == "__main__":
    run()
