# -*- coding: utf-8 -*-
"""
build_flocking_hound.py
变异猎犬（BP_Enemy_MutantHound）扇面外翼包抄（Surround Slot = 85.0 uu）与防重叠排斥构建
"""
import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/flocking_hound_result.txt"

BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary
ASSETS = unreal.EditorAssetLibrary

def log(msg):
    unreal.log(f"[HOUND_FLOCKING] {msg}")
    print(f"[HOUND_FLOCKING] {msg}", flush=True)

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
    raise RuntimeError(f"未找到引脚 '{name}'，可用: {avail}")

def set_value(node, name, value):
    p = pin(node, name, False)
    PINLIB.set_pin_value(p, str(value))

def connect(n1, p1, n2, p2):
    sp = pin(n1, p1, True)
    tp = pin(n2, p2, False)
    PINLIB.try_create_connection(sp, tp)

def clean_event_graph_safe(bp):
    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    
    tick_node = ed.find_event_node("ReceiveTick")
    begin_node = ed.find_event_node("ReceiveBeginPlay")
    overlap_node = ed.find_event_node("ReceiveActorBeginOverlap")
    
    keep = set()
    if tick_node: keep.add(tick_node)
    if begin_node: keep.add(begin_node)
    if overlap_node: keep.add(overlap_node)
    
    to_remove = [n for n in ed.list_all_nodes() if n not in keep]
    if to_remove:
        ed.remove_nodes(to_remove)
    return ed, tick_node, overlap_node

def run():
    bp_path = "/Game/Blueprints/Characters/Enemies/BP_Enemy_MutantHound"
    log(f"🐕 构建战术侧翼包抄变异猎犬: {bp_path}")
    bp = ASSETS.load_asset(bp_path)
    ed, tick_node, overlap_node = clean_event_graph_safe(bp)
    tick_node.set_node_pos(unreal.IntPoint(0, 0))

    HOUND_ART = "/Game/P01/Imported/Content/Asset/Art/02_Enemies/MutantHound"
    fb_run_down = unreal.load_asset(f"{HOUND_ART}/Run/Dir_01_Down/Flipbooks/FB_T_Hound_Run_Dir_01_Down_Sheet.FB_T_Hound_Run_Dir_01_Down_Sheet")
    fb_run_right = unreal.load_asset(f"{HOUND_ART}/Run/Dir_02_Right/Flipbooks/FB_T_Hound_Run_Dir_02_Right_Sheet.FB_T_Hound_Run_Dir_02_Right_Sheet")
    fb_run_up = unreal.load_asset(f"{HOUND_ART}/Run/Dir_03_Up/Flipbooks/FB_T_Hound_Run_Dir_03_Up_Sheet.FB_T_Hound_Run_Dir_03_Up_Sheet")
    fb_run_left = unreal.load_asset(f"{HOUND_ART}/Run/Dir_04_Left/Flipbooks/FB_T_Hound_Run_Dir_04_Left_Sheet.FB_T_Hound_Run_Dir_04_Left_Sheet")
    fb_pounce_down = unreal.load_asset(f"{HOUND_ART}/Pounce/Dir_01_Down/Flipbooks/FB_T_Hound_Pounce_Dir_01_Down_Sheet.FB_T_Hound_Pounce_Dir_01_Down_Sheet")

    def fn(path, x, y):
        n = ed.add_call_function_node(path)
        n.set_node_pos(unreal.IntPoint(x, y))
        return n

    # 1. 采样玩家与自身位置
    get_player = fn("/Script/Engine.GameplayStatics.GetPlayerPawn", 220, 100)
    set_value(get_player, "PlayerIndex", 0)

    p_loc = fn("/Script/Engine.Actor.K2_GetActorLocation", 460, 40)
    connect(get_player, "ReturnValue", p_loc, "self")

    self_loc = fn("/Script/Engine.Actor.K2_GetActorLocation", 460, 180)

    # 2. 战术包围槽位（Surround Slot 计算）：左怪走左翼(-85)，右怪走右翼(+85)
    # 计算 (self_loc - p_loc) 的 X 相对偏移
    sub_rel = fn("/Script/Engine.KismetMathLibrary.Subtract_VectorVector", 700, 240)
    connect(self_loc, "ReturnValue", sub_rel, "A")
    connect(p_loc, "ReturnValue", sub_rel, "B")

    break_rel = fn("/Script/Engine.KismetMathLibrary.BreakVector", 920, 240)
    connect(sub_rel, "ReturnValue", break_rel, "InVec")

    make_rel_x = fn("/Script/Engine.KismetMathLibrary.MakeVector", 1140, 240)
    connect(break_rel, "X", make_rel_x, "X")
    set_value(make_rel_x, "Y", 0.0); set_value(make_rel_x, "Z", 0.0)

    norm_rel_x = fn("/Script/Engine.KismetMathLibrary.Normal", 1360, 240)
    connect(make_rel_x, "ReturnValue", norm_rel_x, "A")

    # 猎犬外翼展开半宽: 85.0 uu
    mul_slot_off = fn("/Script/Engine.KismetMathLibrary.Multiply_VectorVector", 1580, 240)
    connect(norm_rel_x, "ReturnValue", mul_slot_off, "A")
    set_value(mul_slot_off, "B", "85.0, 0.0, 20.0")

    # 猎犬专属目标点 = p_loc + mul_slot_off
    slot_target_loc = fn("/Script/Engine.KismetMathLibrary.Add_VectorVector", 1800, 180)
    connect(p_loc, "ReturnValue", slot_target_loc, "A")
    connect(mul_slot_off, "ReturnValue", slot_target_loc, "B")

    # 3. 距离判断 (StopDistance = 75.0 对准专属包围槽目标点)
    dist_node = fn("/Script/Engine.KismetMathLibrary.Vector_Distance", 2020, -60)
    connect(slot_target_loc, "ReturnValue", dist_node, "v1")
    connect(self_loc, "ReturnValue", dist_node, "v2")

    is_far = fn("/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 2240, -60)
    connect(dist_node, "ReturnValue", is_far, "A")
    set_value(is_far, "B", 75.0)

    br_gate = ed.add_branch_node()
    br_gate.set_node_pos(unreal.IntPoint(2460, 0))
    connect(tick_node, "then", br_gate, "execute")
    connect(is_far, "ReturnValue", br_gate, "Condition")

    # 4. 追击向移动 (br_gate.then: 距离 > 75.0)
    sub_v = fn("/Script/Engine.KismetMathLibrary.Subtract_VectorVector", 2020, 140)
    connect(slot_target_loc, "ReturnValue", sub_v, "A")
    connect(self_loc, "ReturnValue", sub_v, "B")

    norm_v = fn("/Script/Engine.KismetMathLibrary.Normal", 2240, 140)
    connect(sub_v, "ReturnValue", norm_v, "A")

    break_v = fn("/Script/Engine.KismetMathLibrary.BreakVector", 2460, 140)
    connect(norm_v, "ReturnValue", break_v, "InVec")

    speed = 150.0

    mul_x_speed = fn("/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 2680, 40)
    connect(break_v, "X", mul_x_speed, "A"); set_value(mul_x_speed, "B", speed)

    mul_x_dt = fn("/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 2900, 40)
    connect(mul_x_speed, "ReturnValue", mul_x_dt, "A")
    connect(tick_node, "DeltaSeconds", mul_x_dt, "B")

    delta_vec_x = fn("/Script/Engine.KismetMathLibrary.MakeVector", 3120, 40)
    connect(mul_x_dt, "ReturnValue", delta_vec_x, "X"); set_value(delta_vec_x, "Y", 0.0); set_value(delta_vec_x, "Z", 0.0)

    move_x = fn("/Script/Engine.Actor.K2_AddActorWorldOffset", 3360, 40)
    set_value(move_x, "bSweep", "true")
    connect(delta_vec_x, "ReturnValue", move_x, "DeltaLocation")
    connect(br_gate, "then", move_x, "execute")

    mul_z_speed = fn("/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 2680, 200)
    connect(break_v, "Z", mul_z_speed, "A"); set_value(mul_z_speed, "B", speed)

    mul_z_dt = fn("/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 2900, 200)
    connect(mul_z_speed, "ReturnValue", mul_z_dt, "A")
    connect(tick_node, "DeltaSeconds", mul_z_dt, "B")

    delta_vec_z = fn("/Script/Engine.KismetMathLibrary.MakeVector", 3120, 200)
    set_value(delta_vec_z, "X", 0.0); set_value(delta_vec_z, "Y", 0.0)
    connect(mul_z_dt, "ReturnValue", delta_vec_z, "Z")

    move_z = fn("/Script/Engine.Actor.K2_AddActorWorldOffset", 3360, 200)
    set_value(move_z, "bSweep", "true")
    connect(delta_vec_z, "ReturnValue", move_z, "DeltaLocation")
    connect(move_x, "then", move_z, "execute")

    # 5. 强类型 4 向奔跑状态机 (与 move_z 串联)
    get_fb = fn("/Script/Engine.Actor.GetComponentByClass", 3120, -260)
    set_value(get_fb, "ComponentClass", "Class'/Script/Paper2D.PaperFlipbookComponent'")

    abs_x = fn("/Script/Engine.KismetMathLibrary.Abs", 2680, -40)
    connect(break_v, "X", abs_x, "A")
    abs_z = fn("/Script/Engine.KismetMathLibrary.Abs", 2680, 10)
    connect(break_v, "Z", abs_z, "A")

    is_horizontal = fn("/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 2900, -20)
    connect(abs_x, "ReturnValue", is_horizontal, "A")
    connect(abs_z, "ReturnValue", is_horizontal, "B")

    br_axis = ed.add_branch_node(); br_axis.set_node_pos(unreal.IntPoint(3600, 40))
    connect(move_z, "then", br_axis, "execute")
    connect(is_horizontal, "ReturnValue", br_axis, "Condition")

    # 水平奔跑
    is_right = fn("/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 3120, -40)
    connect(break_v, "X", is_right, "A"); set_value(is_right, "B", 0.0)

    br_horiz = ed.add_branch_node(); br_horiz.set_node_pos(unreal.IntPoint(3820, -40))
    connect(br_axis, "then", br_horiz, "execute")
    connect(is_right, "ReturnValue", br_horiz, "Condition")

    set_fb_right = fn("/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 4060, -80)
    set_value(set_fb_right, "NewFlipbook", fb_run_right.get_path_name())
    connect(br_horiz, "then", set_fb_right, "execute")
    connect(get_fb, "ReturnValue", set_fb_right, "self")

    set_fb_left = fn("/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 4060, 0)
    set_value(set_fb_left, "NewFlipbook", fb_run_left.get_path_name())
    connect(br_horiz, "else", set_fb_left, "execute")
    connect(get_fb, "ReturnValue", set_fb_left, "self")

    # 垂直奔跑
    is_up = fn("/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 3120, 120)
    connect(break_v, "Z", is_up, "A"); set_value(is_up, "B", 0.0)

    br_vert = ed.add_branch_node(); br_vert.set_node_pos(unreal.IntPoint(3820, 120))
    connect(br_axis, "else", br_vert, "execute")
    connect(is_up, "ReturnValue", br_vert, "Condition")

    set_fb_up = fn("/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 4060, 80)
    set_value(set_fb_up, "NewFlipbook", fb_run_up.get_path_name())
    connect(br_vert, "then", set_fb_up, "execute")
    connect(get_fb, "ReturnValue", set_fb_up, "self")

    set_fb_down = fn("/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 4060, 160)
    set_value(set_fb_down, "NewFlipbook", fb_run_down.get_path_name())
    connect(br_vert, "else", set_fb_down, "execute")
    connect(get_fb, "ReturnValue", set_fb_down, "self")

    # 6. 原地攻击态 (br_gate.else: 距离 <= 75.0 时播放扑咬动作)
    set_fb_atk = fn("/Script/Paper2D.PaperFlipbookComponent.SetFlipbook", 2680, -140)
    set_value(set_fb_atk, "NewFlipbook", fb_pounce_down.get_path_name())
    connect(br_gate, "else", set_fb_atk, "execute")
    connect(get_fb, "ReturnValue", set_fb_atk, "self")

    # 7. 怪与怪反弹排斥 (复用或创建 overlap_node)
    base_x, base_y = 0, 480
    if not overlap_node:
        overlap_node = BPLIB.add_event_override(bp, "ReceiveActorBeginOverlap", unreal.IntPoint(base_x, base_y))
    else:
        overlap_node.set_node_pos(unreal.IntPoint(base_x, base_y))
    
    get_p = fn("/Script/Engine.GameplayStatics.GetPlayerPawn", base_x + 220, base_y + 120)
    set_value(get_p, "PlayerIndex", 0)
    
    not_p = fn("/Script/Engine.KismetMathLibrary.NotEqual_ObjectObject", base_x + 460, base_y + 60)
    connect(overlap_node, "OtherActor", not_p, "A")
    connect(get_p, "ReturnValue", not_p, "B")
    
    br_np = ed.add_branch_node()
    br_np.set_node_pos(unreal.IntPoint(base_x + 680, base_y))
    connect(overlap_node, "then", br_np, "execute")
    connect(not_p, "ReturnValue", br_np, "Condition")
    
    s_loc = fn("/Script/Engine.Actor.K2_GetActorLocation", base_x + 680, base_y + 140)
    o_loc = fn("/Script/Engine.Actor.K2_GetActorLocation", base_x + 680, base_y + 260)
    connect(overlap_node, "OtherActor", o_loc, "self")
    
    rep_sub = fn("/Script/Engine.KismetMathLibrary.Subtract_VectorVector", base_x + 920, base_y + 180)
    connect(s_loc, "ReturnValue", rep_sub, "A")
    connect(o_loc, "ReturnValue", rep_sub, "B")
    
    rep_norm = fn("/Script/Engine.KismetMathLibrary.Normal", base_x + 1140, base_y + 180)
    connect(rep_sub, "ReturnValue", rep_norm, "A")
    
    rep_vec = fn("/Script/Engine.KismetMathLibrary.Multiply_VectorVector", base_x + 1360, base_y + 180)
    connect(rep_norm, "ReturnValue", rep_vec, "A")
    set_value(rep_vec, "B", "40.0, 0.0, 40.0")
    
    rep_off = fn("/Script/Engine.Actor.K2_AddActorWorldOffset", base_x + 1600, base_y)
    set_value(rep_off, "bSweep", "false")
    connect(br_np, "then", rep_off, "execute")
    connect(rep_vec, "ReturnValue", rep_off, "DeltaLocation")

    BPLIB.compile_blueprint(bp)
    saved = ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"  💾 变异猎犬构建与落盘: {'成功' if saved else '失败'}")
    OUT.write_text(f"SAVED: {saved}", encoding="utf-8")
    return saved

if __name__ == "__main__":
    run()
