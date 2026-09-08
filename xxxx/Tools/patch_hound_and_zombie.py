# -*- coding: utf-8 -*-
"""
patch_hound_and_zombie.py
原地插桩方案：
1. BP_Enemy_MutantHound:
   - 检查已有的 ReceiveTick 连线
   - 在 ReceiveTick -> 移动节点 之间切入 Branch (Distance > 75.0)
   - 当 Distance <= 75.0 时，执行 SetFlipbook (FB_T_Hound_Pounce)
   - 注入 ReceiveActorBeginOverlap 接触推开 40 uu
2. BP_Enemy_ZombieWalker:
   - 在 ReceiveTick -> 移动节点 之间切入 Branch (Distance > 80.0)
   - 注入 ReceiveActorBeginOverlap 接触推开 40 uu
"""
import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary
ASSETS = unreal.EditorAssetLibrary

def log(msg):
    unreal.log(f"[PATCH_AI] {msg}")
    print(f"[PATCH_AI] {msg}", flush=True)

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

def inject_repel(bp, ed, base_x=-400, base_y=600):
    log("  🛡️ 注入怪与怪防重叠 (ReceiveActorBeginOverlap 反弹推开)...")
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
    log("    ✅ 防重叠反弹节点创建就绪！")

# ==============================================================================
# 1. 插桩猎犬
# ==============================================================================
def patch_hound():
    bp_path = "/Game/Blueprints/Characters/Enemies/BP_Enemy_MutantHound"
    log(f"🐕 原地插桩变异猎犬: 门禁 75.0 + 扑咬 + 怪怪推开...")
    bp = ASSETS.load_asset(bp_path)
    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    tick_node = ed.find_event_node("ReceiveTick")

    # 寻找当前接在 ReceiveTick 后的首个执行节点
    then_pin = pin(tick_node, "then", True)
    conns = PINLIB.get_pin_connections(then_pin) if hasattr(PINLIB, "get_pin_connections") else []
    first_target_pin = conns[0] if conns else None

    # 断开 tick_node.then 的直接连线
    PINLIB.break_pin_links(then_pin)

    # 创建距离计算与门禁
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

    # 如果有原本的下游移动节点，接在 br_gate.then
    if first_target_pin:
        PINLIB.try_create_connection(pin(br_gate, "then", True), first_target_pin)
        log("    ✅ 追击位移管线成功挂接至 [Distance > 75.0] then 引脚！")

    # 近身动作 (Distance <= 75.0 -> 扑咬)
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

    # 注入怪怪推开
    inject_repel(bp, ed, 0, 500)

    BPLIB.compile_blueprint(bp)
    saved = ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"  💾 猎犬插桩落盘: {'成功' if saved else '失败'}")
    return saved

# ==============================================================================
# 2. 插桩行尸
# ==============================================================================
def patch_zombie():
    bp_path = "/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker"
    log(f"🧟 原地插桩普通行尸: 门禁 80.0 + 怪怪推开...")
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
        log("    ✅ 行尸位移管线成功挂接至 [Distance > 80.0] then 引脚！")

    # 注入怪怪推开
    inject_repel(bp, ed, 0, 500)

    BPLIB.compile_blueprint(bp)
    saved = ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"  💾 行尸插桩落盘: {'成功' if saved else '失败'}")
    return saved

def main():
    log("==================================================")
    log("🚀 启动变异猎犬与行尸安全插桩构建...")
    s1 = patch_hound()
    s2 = patch_zombie()
    log(f"🎉 插桩结果: Hound={s1}, Zombie={s2}")
    log("==================================================")

if __name__ == "__main__":
    main()
