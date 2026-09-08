# -*- coding: utf-8 -*-
import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
ASSETS = unreal.EditorAssetLibrary
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary

def run():
    bp_path = "/Game/Blueprints/Characters/Enemies/BP_Enemy_MutantHound"
    bp = ASSETS.load_asset(bp_path)
    if not bp:
        raise RuntimeError("MutantHound bp not found")

    existing_vars = [str(x) for x in BPLIB.list_member_variable_names(bp)]
    if "CurrentHealth" not in existing_vars:
        BPLIB.add_member_variable(bp, "CurrentHealth", unreal.EdGraphPinType(pin_category="real", pin_sub_category="double"))
    if "MaxHealth" not in existing_vars:
        BPLIB.add_member_variable(bp, "MaxHealth", unreal.EdGraphPinType(pin_category="real", pin_sub_category="double"))

    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)

    all_nodes = ed.list_all_nodes()
    to_remove = []
    dmg_events = []
    for n in all_nodes:
        if isinstance(n, unreal.K2Node_Event):
            out_names = [str(PINLIB.get_pin_name(p)).lower() for p in BPLIB.list_output_pins(n)]
            if "damage" in out_names:
                dmg_events.append(n)
        elif n.get_node_pos().y >= 900:
            to_remove.append(n)

    for n in to_remove:
        for p in BPLIB.list_all_pins(n):
            try: PINLIB.break_pin_links(p)
            except Exception: pass
        ed.remove_nodes([n])

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

    for p in BPLIB.list_all_pins(dmg_node):
        try: PINLIB.break_pin_links(p)
        except Exception: pass
    dmg_node.set_node_pos(unreal.IntPoint(0, 1000))

    def fn(path, x, y):
        n = ed.add_call_function_node(path)
        n.set_node_pos(unreal.IntPoint(x, y))
        return n

    def pin(node, name, output=None):
        if output is True: pins = BPLIB.list_output_pins(node)
        elif output is False: pins = BPLIB.list_input_pins(node)
        else: pins = list(BPLIB.list_output_pins(node)) + list(BPLIB.list_input_pins(node))
        wanted = name.lower()
        for p in pins:
            if str(PINLIB.get_pin_name(p)).lower() == wanted: return p
        raise RuntimeError(f"Pin {name} not found")

    def connect(n1, p1, n2, p2):
        sp = pin(n1, p1, True); tp = pin(n2, p2, False)
        return PINLIB.try_create_connection(sp, tp)

    cur_hp = ed.add_get_member_variable_node("CurrentHealth")
    cur_hp.set_node_pos(unreal.IntPoint(240, 1140))

    sub_hp = fn("/Script/Engine.KismetMathLibrary.Subtract_DoubleDouble", 480, 1080)
    connect(cur_hp, "CurrentHealth", sub_hp, "A")
    connect(dmg_node, "Damage", sub_hp, "B")

    set_hp = ed.add_set_member_variable_node("CurrentHealth")
    set_hp.set_node_pos(unreal.IntPoint(720, 1000))
    connect(dmg_node, "then", set_hp, "execute")
    connect(sub_hp, "ReturnValue", set_hp, "CurrentHealth")

    is_dead = fn("/Script/Engine.KismetMathLibrary.LessEqual_DoubleDouble", 720, 1140)
    connect(sub_hp, "ReturnValue", is_dead, "A")
    PINLIB.set_pin_value(pin(is_dead, "B", False), "0.0")

    branch_dead = ed.add_branch_node()
    branch_dead.set_node_pos(unreal.IntPoint(960, 1000))
    connect(set_hp, "then", branch_dead, "execute")
    connect(is_dead, "ReturnValue", branch_dead, "Condition")

    # 0 延迟原子化销毁: 关碰撞 -> 隐藏网格 -> 销毁
    col_off = fn("/Script/Engine.Actor.SetActorEnableCollision", 1200, 1000)
    PINLIB.set_pin_value(pin(col_off, "bNewActorEnableCollision", False), "false")
    connect(branch_dead, "then", col_off, "execute")

    hide_self = fn("/Script/Engine.Actor.SetActorHiddenInGame", 1460, 1000)
    PINLIB.set_pin_value(pin(hide_self, "bNewHidden", False), "true")
    connect(col_off, "then", hide_self, "execute")

    destroy_self = fn("/Script/Engine.Actor.K2_DestroyActor", 1720, 1000)
    connect(hide_self, "then", destroy_self, "execute")

    BPLIB.compile_blueprint(bp)
    saved = ASSETS.save_loaded_asset(bp)
    print(f"[STEP2] BP_Enemy_MutantHound SAVED: {saved}")

if __name__ == "__main__":
    run()
