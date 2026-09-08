# -*- coding: utf-8 -*-
import unreal
from pathlib import Path
import traceback

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/setup_zombie_result.txt"
OUT.parent.mkdir(parents=True, exist_ok=True)

ASSETS = unreal.EditorAssetLibrary
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary

def log(msg):
    print(f"[ZOMBIE_DAMAGE] {msg}", flush=True)

def pin(node, name, output=None):
    if output is True: pins = BPLIB.list_output_pins(node)
    elif output is False: pins = BPLIB.list_input_pins(node)
    else: pins = list(BPLIB.list_output_pins(node)) + list(BPLIB.list_input_pins(node))
    wanted = name.lower()
    for p in pins:
        if str(PINLIB.get_pin_name(p)).lower() == wanted: return p
    avail = [str(PINLIB.get_pin_name(p)) for p in pins]
    raise RuntimeError(f"Pin '{name}' not found, avail: {avail}")

def set_value(node, name, value):
    p = pin(node, name, False)
    PINLIB.set_pin_value(p, str(value))

def connect(n1, p1, n2, p2):
    sp = pin(n1, p1, True); tp = pin(n2, p2, False)
    ok = PINLIB.try_create_connection(sp, tp)
    log(f"Connect {p1} -> {p2}: {ok}")

def run():
    bp_path = "/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker"
    bp = ASSETS.load_asset(bp_path)
    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    log(f"Opened {bp_path}")

    # 1. 扫描所有事件节点，找出所有 AnyDamage 节点
    all_nodes = ed.list_all_nodes()
    dmg_events = []
    to_remove = []
    for n in all_nodes:
        if isinstance(n, unreal.K2Node_Event):
            out_names = [str(PINLIB.get_pin_name(p)).lower() for p in BPLIB.list_output_pins(n)]
            if "damage" in out_names:
                dmg_events.append(n)
        # 清理之前残留的游离节点（大于 Y=900 的临时节点）
        elif n.get_node_pos().y >= 900:
            to_remove.append(n)

    log(f"Found {len(dmg_events)} damage event nodes, {len(to_remove)} stray nodes to clean")

    # 移除游离节点
    if to_remove:
        for n in to_remove:
            for p in BPLIB.list_all_pins(n):
                try: PINLIB.break_pin_links(p)
                except Exception: pass
        ed.remove_nodes(to_remove)

    # 确保只留一个 damage event
    if len(dmg_events) > 1:
        for extra in dmg_events[1:]:
            for p in BPLIB.list_all_pins(extra):
                try: PINLIB.break_pin_links(p)
                except Exception: pass
            ed.remove_nodes([extra])
        dmg_node = dmg_events[0]
    elif len(dmg_events) == 1:
        dmg_node = dmg_events[0]
    else:
        dmg_node = BPLIB.add_event_override(bp, "ReceiveAnyDamage", unreal.IntPoint(0, 1000))

    # 断开 dmg_node 现存的所有连接，重新连线
    for p in BPLIB.list_all_pins(dmg_node):
        try: PINLIB.break_pin_links(p)
        except Exception: pass
    dmg_node.set_node_pos(unreal.IntPoint(0, 1000))

    def fn(path, x, y):
        n = ed.add_call_function_node(path)
        n.set_node_pos(unreal.IntPoint(x, y))
        return n

    # 2. 扣血逻辑
    cur_hp = ed.add_get_member_variable_node("CurrentHealth")
    cur_hp.set_node_pos(unreal.IntPoint(240, 1140))

    sub_hp = fn("/Script/Engine.KismetMathLibrary.Subtract_DoubleDouble", 460, 1080)
    connect(cur_hp, "CurrentHealth", sub_hp, "A")
    connect(dmg_node, "Damage", sub_hp, "B")

    set_hp = ed.add_set_member_variable_node("CurrentHealth")
    set_hp.set_node_pos(unreal.IntPoint(720, 1000))
    connect(dmg_node, "then", set_hp, "execute")
    connect(sub_hp, "ReturnValue", set_hp, "CurrentHealth")

    # 3. 死亡判定
    is_dead = fn("/Script/Engine.KismetMathLibrary.LessEqual_DoubleDouble", 720, 1140)
    connect(sub_hp, "ReturnValue", is_dead, "A")
    set_value(is_dead, "B", "0.0")

    branch = ed.add_branch_node()
    branch.set_node_pos(unreal.IntPoint(960, 1000))
    connect(set_hp, "then", branch, "execute")
    connect(is_dead, "ReturnValue", branch, "Condition")

    # 4. 死亡自毁
    destroy = fn("/Script/Engine.Actor.K2_DestroyActor", 1200, 980)
    connect(branch, "then", destroy, "execute")

    # 5. 编译与保存
    log("Compiling Blueprint...")
    BPLIB.compile_blueprint(bp)
    saved = ASSETS.save_loaded_asset(bp)
    log(f"SAVED: {saved}")
    OUT.write_text(f"SAVED: {saved}\n", encoding="utf-8")

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        err = traceback.format_exc()
        log(f"ERROR: {err}")
        OUT.write_text(f"ERROR: {err}\n", encoding="utf-8")
        raise
