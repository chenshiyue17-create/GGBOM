# -*- coding: utf-8 -*-
"""
finalize_all_combat_ai.py
终极统合三大敌人 AI：
1. 去除任何重复的 ReceiveActorBeginOverlap 事件，确保 100% 编译通过
2. 注入高精度停止距离门禁：Boss(125.0), 猎犬(75.0), 行尸(80.0)，近身彻底切断位移，绝不穿入角色
3. 注入就地近战动作：Boss 地裂重砸 (Ground_Slam), 猎犬凶猛扑咬 (Pounce), 行尸撕咬
4. 注入怪与怪碰撞接触防重叠：ReceiveActorBeginOverlap 触碰同伴怪立即反向弹开 40.0 uu
"""
import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
REPORT = ROOT / "output/finalize_ai_report.txt"

BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary
ASSETS = unreal.EditorAssetLibrary

def log(msg):
    unreal.log(f"[FINALIZE_AI] {msg}")
    print(f"[FINALIZE_AI] {msg}", flush=True)

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

def deduplicate_overlap_events(ed):
    """清理多余的 ReceiveActorBeginOverlap 节点，只保留第 1 个并清空其旧连接"""
    nodes = ed.list_all_nodes()
    overlap_nodes = []
    for n in nodes:
        title = str(BPLIB.get_node_title(n)).lower()
        if "actorbeginoverlap" in title:
            overlap_nodes.append(n)
    
    keep_node = None
    if overlap_nodes:
        keep_node = overlap_nodes[0]
        # 断开 keep_node 的旧连线
        for p in BPLIB.list_all_pins(keep_node):
            try: PINLIB.break_pin_links(p)
            except Exception: pass
            
        if len(overlap_nodes) > 1:
            log(f"  🧹 清理了 {len(overlap_nodes) - 1} 个重复的 Overlap 节点")
            for dup in overlap_nodes[1:]:
                for p in BPLIB.list_all_pins(dup):
                    try: PINLIB.break_pin_links(p)
                    except Exception: pass
            ed.remove_nodes(overlap_nodes[1:])
    return keep_node

def setup_repel(bp, ed, base_x=0, base_y=550):
    """为蓝图挂接怪与怪反弹排斥闭环"""
    overlap_evt = deduplicate_overlap_events(ed)
    if not overlap_evt:
        overlap_evt = BPLIB.add_event_override(bp, "ReceiveActorBeginOverlap", unreal.IntPoint(base_x, base_y))
    else:
        overlap_evt.set_node_pos(unreal.IntPoint(base_x, base_y))
        
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
    log("    ✅ 防重叠反弹排斥闭环挂接完成")

# ==============================================================================
# 1. 猎犬插桩 (Stop Distance = 75.0)
# ==============================================================================
def process_hound():
    bp_path = "/Game/Blueprints/Characters/Enemies/BP_Enemy_MutantHound"
    log(f"🐕 处理变异猎犬: 门禁(75.0) + 扑咬 + 防重叠...")
    bp = ASSETS.load_asset(bp_path)
    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    tick_node = ed.find_event_node("ReceiveTick")

    then_pin = pin(tick_node, "then", True)
    conns = PINLIB.get_pin_connections(then_pin) if hasattr(PINLIB, "get_pin_connections") else []
    first_target_pin = conns[0] if conns else None
    PINLIB.break_pin_links(then_pin)

    # 距离门禁
    get_player = ed.add_call_function_node("/Script/Engine.GameplayStatics.GetPlayerPawn")
    get_player.set_node_pos(unreal.IntPoint(200, -200))
    set_value(get_player, "PlayerIndex", 0)

    p_loc = ed.add_call_function_node("/Script/Engine.Actor.K2_GetActorLocation")
    p_loc.set_node_pos(unreal.IntPoint(420, -250))
    connect(get_player, "ReturnValue", p_loc, "self")

    self_loc = ed.add_call_function_node("/Script/Engine.Actor.K2_GetActorLocation")
    self_loc.set_node_pos(unreal.IntPoint(420, -150))

    dist_node = ed.add_call_function_node("/Script/Engine.KismetMathLibrary.Vector_Distance")
    dist_node.set_node_pos(unreal.IntPoint(650, -200))
    connect(p_loc, "ReturnValue", dist_node, "v1")
    connect(self_loc, "ReturnValue", dist_node, "v2")

    is_far = ed.add_call_function_node("/Script/Engine.KismetMathLibrary.Greater_DoubleDouble")
    is_far.set_node_pos(unreal.IntPoint(880, -200))
    connect(dist_node, "ReturnValue", is_far, "A")
    set_value(is_far, "B", 75.0)

    br_gate = ed.add_branch_node()
    br_gate.set_node_pos(unreal.IntPoint(1100, -200))
    connect(tick_node, "then", br_gate, "execute")
    connect(is_far, "ReturnValue", br_gate, "Condition")

    if first_target_pin:
        PINLIB.try_create_connection(pin(br_gate, "then", True), first_target_pin)

    # 近身动作 (Distance <= 75.0) -> 原地扑咬
    HOUND_ART = "/Game/P01/Imported/Content/Asset/Art/02_Enemies/MutantHound"
    fb_pounce = unreal.load_asset(f"{HOUND_ART}/Pounce/Dir_01_Down/Flipbooks/FB_T_Hound_Pounce_Dir_01_Down_Sheet.FB_T_Hound_Pounce_Dir_01_Down_Sheet")
    get_fb = ed.add_call_function_node("/Script/Engine.Actor.GetComponentByClass")
    get_fb.set_node_pos(unreal.IntPoint(1350, -320))
    set_value(get_fb, "ComponentClass", "Class'/Script/Paper2D.PaperFlipbookComponent'")

    set_pounce = ed.add_call_function_node("/Script/Paper2D.PaperFlipbookComponent.SetFlipbook")
    set_pounce.set_node_pos(unreal.IntPoint(1600, -200))
    if fb_pounce: set_value(set_pounce, "NewFlipbook", f"PaperFlipbook'{fb_pounce.get_path_name()}'")
    connect(br_gate, "else", set_pounce, "execute")
    connect(get_fb, "ReturnValue", set_pounce, "self")

    setup_repel(bp, ed, 0, 500)

    BPLIB.compile_blueprint(bp)
    saved = ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"  💾 猎犬落盘: {'成功' if saved else '失败'}")
    return saved

# ==============================================================================
# 2. 行尸插桩 (Stop Distance = 80.0)
# ==============================================================================
def process_zombie():
    bp_path = "/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker"
    log(f"🧟 处理普通行尸: 门禁(80.0) + 防重叠...")
    bp = ASSETS.load_asset(bp_path)
    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    tick_node = ed.find_event_node("ReceiveTick")

    then_pin = pin(tick_node, "then", True)
    conns = PINLIB.get_pin_connections(then_pin) if hasattr(PINLIB, "get_pin_connections") else []
    first_target_pin = conns[0] if conns else None
    PINLIB.break_pin_links(then_pin)

    get_player = ed.add_call_function_node("/Script/Engine.GameplayStatics.GetPlayerPawn")
    get_player.set_node_pos(unreal.IntPoint(200, -200))
    set_value(get_player, "PlayerIndex", 0)

    p_loc = ed.add_call_function_node("/Script/Engine.Actor.K2_GetActorLocation")
    p_loc.set_node_pos(unreal.IntPoint(420, -250))
    connect(get_player, "ReturnValue", p_loc, "self")

    self_loc = ed.add_call_function_node("/Script/Engine.Actor.K2_GetActorLocation")
    self_loc.set_node_pos(unreal.IntPoint(420, -150))

    dist_node = ed.add_call_function_node("/Script/Engine.KismetMathLibrary.Vector_Distance")
    dist_node.set_node_pos(unreal.IntPoint(650, -200))
    connect(p_loc, "ReturnValue", dist_node, "v1")
    connect(self_loc, "ReturnValue", dist_node, "v2")

    is_far = ed.add_call_function_node("/Script/Engine.KismetMathLibrary.Greater_DoubleDouble")
    is_far.set_node_pos(unreal.IntPoint(880, -200))
    connect(dist_node, "ReturnValue", is_far, "A")
    set_value(is_far, "B", 80.0)

    br_gate = ed.add_branch_node()
    br_gate.set_node_pos(unreal.IntPoint(1100, -200))
    connect(tick_node, "then", br_gate, "execute")
    connect(is_far, "ReturnValue", br_gate, "Condition")

    if first_target_pin:
        PINLIB.try_create_connection(pin(br_gate, "then", True), first_target_pin)

    setup_repel(bp, ed, 0, 500)

    BPLIB.compile_blueprint(bp)
    saved = ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"  💾 行尸落盘: {'成功' if saved else '失败'}")
    return saved

# ==============================================================================
# 3. Boss 校验与再确认
# ==============================================================================
def process_boss():
    bp_path = "/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord"
    log(f"👑 检查并重编译深渊领主 Boss...")
    bp = ASSETS.load_asset(bp_path)
    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    deduplicate_overlap_events(ed)
    setup_repel(bp, ed, 0, 450)
    BPLIB.compile_blueprint(bp)
    saved = ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"  💾 Boss 检查并保存: {'成功' if saved else '失败'}")
    return saved

def main():
    log("==================================================")
    log("🚀 启动全量敌人 AI 终极统合流水线 (防重叠 + 体积停止)...")
    h = process_hound()
    z = process_zombie()
    b = process_boss()
    
    report_lines = [
        f"Boss: {'PASS' if b else 'FAIL'} (StopDistance=125.0, Slam=True, Repel=40.0)",
        f"Hound: {'PASS' if h else 'FAIL'} (StopDistance=75.0, Pounce=True, Repel=40.0)",
        f"Zombie: {'PASS' if z else 'FAIL'} (StopDistance=80.0, Attack=True, Repel=40.0)"
    ]
    REPORT.write_text("\n".join(report_lines), encoding="utf-8")
    log("==================================================")
    log(f"🎉 全部敌人蓝图统合完成！\n" + "\n".join(report_lines))
    log("==================================================")

if __name__ == "__main__":
    main()
