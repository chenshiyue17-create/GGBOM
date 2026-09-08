# -*- coding: utf-8 -*-
import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
ASSETS = unreal.EditorAssetLibrary
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary

def run():
    bp_path = "/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord"
    bp = ASSETS.load_asset(bp_path)
    if not bp:
        raise RuntimeError("Boss bp not found")

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
        elif n.get_node_pos().y >= 850:
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

    # 1. 扣减生命值
    cur_hp = ed.add_get_member_variable_node("CurrentHealth")
    cur_hp.set_node_pos(unreal.IntPoint(240, 1140))

    sub_hp = fn("/Script/Engine.KismetMathLibrary.Subtract_DoubleDouble", 480, 1080)
    connect(cur_hp, "CurrentHealth", sub_hp, "A")
    connect(dmg_node, "Damage", sub_hp, "B")

    max_zero = fn("/Script/Engine.KismetMathLibrary.FMax", 700, 1080)
    connect(sub_hp, "ReturnValue", max_zero, "A")
    PINLIB.set_pin_value(pin(max_zero, "B", False), "0.0")

    set_hp = ed.add_set_member_variable_node("CurrentHealth")
    set_hp.set_node_pos(unreal.IntPoint(920, 1000))
    connect(dmg_node, "then", set_hp, "execute")
    connect(max_zero, "ReturnValue", set_hp, "CurrentHealth")

    # 2. 死亡判定
    is_dead = fn("/Script/Engine.KismetMathLibrary.LessEqual_DoubleDouble", 1160, 1140)
    connect(max_zero, "ReturnValue", is_dead, "A")
    PINLIB.set_pin_value(pin(is_dead, "B", False), "0.0")

    branch = ed.add_branch_node()
    branch.set_node_pos(unreal.IntPoint(1400, 1000))
    connect(set_hp, "then", branch, "execute")
    connect(is_dead, "ReturnValue", branch, "Condition")

    # ---------------- 死亡分支 (branch.then): 0 延迟瞬消 + 级联销毁血条与自身 ----------------
    col_off = fn("/Script/Engine.Actor.SetActorEnableCollision", 1640, 900)
    PINLIB.set_pin_value(pin(col_off, "bNewActorEnableCollision", False), "false")
    connect(branch, "then", col_off, "execute")

    hide_boss = fn("/Script/Engine.Actor.SetActorHiddenInGame", 1900, 900)
    PINLIB.set_pin_value(pin(hide_boss, "bNewHidden", False), "true")
    connect(col_off, "then", hide_boss, "execute")

    get_bars = fn("/Script/Engine.GameplayStatics.GetAllActorsWithTag", 2160, 900)
    PINLIB.set_pin_value(pin(get_bars, "Tag", False), "BossBarGroup")
    connect(hide_boss, "then", get_bars, "execute")

    last_exec = get_bars
    for i in range(4):
        item_node = fn("/Script/Engine.KismetArrayLibrary.Array_Get", 2400 + i * 400, 900)
        connect(get_bars, "OutActors", item_node, "TargetArray")
        PINLIB.set_pin_value(pin(item_node, "Index", False), str(i))

        hide_bar = fn("/Script/Engine.Actor.SetActorHiddenInGame", 2580 + i * 400, 900)
        PINLIB.set_pin_value(pin(hide_bar, "bNewHidden", False), "true")
        connect(last_exec, "then", hide_bar, "execute")
        connect(item_node, "Item", hide_bar, "self")

        dest_bar = fn("/Script/Engine.Actor.K2_DestroyActor", 2800 + i * 400, 900)
        connect(hide_bar, "then", dest_bar, "execute")
        connect(item_node, "Item", dest_bar, "self")
        last_exec = dest_bar

    destroy_boss = fn("/Script/Engine.Actor.K2_DestroyActor", 4200, 900)
    connect(last_exec, "then", destroy_boss, "execute")

    # ---------------- 存活受击分支 (branch.else): 动态自适应头顶血条收缩 ----------------
    div_ratio = fn("/Script/Engine.KismetMathLibrary.Divide_DoubleDouble", 1640, 1200)
    connect(max_zero, "ReturnValue", div_ratio, "A")
    PINLIB.set_pin_value(pin(div_ratio, "B", False), "1200.0")

    clamp_ratio = fn("/Script/Engine.KismetMathLibrary.FClamp", 1860, 1200)
    connect(div_ratio, "ReturnValue", clamp_ratio, "Value")
    PINLIB.set_pin_value(pin(clamp_ratio, "Min", False), "0.0")
    PINLIB.set_pin_value(pin(clamp_ratio, "Max", False), "1.0")

    mul_scale = fn("/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 2080, 1200)
    connect(clamp_ratio, "ReturnValue", mul_scale, "A")
    PINLIB.set_pin_value(pin(mul_scale, "B", False), "0.20")

    make_scale = fn("/Script/Engine.KismetMathLibrary.MakeVector", 2300, 1200)
    connect(mul_scale, "ReturnValue", make_scale, "X")
    PINLIB.set_pin_value(pin(make_scale, "Y", False), "1.0")
    PINLIB.set_pin_value(pin(make_scale, "Z", False), "0.16")

    get_fill_tag = fn("/Script/Engine.GameplayStatics.GetAllActorsWithTag", 1640, 1380)
    PINLIB.set_pin_value(pin(get_fill_tag, "Tag", False), "BossBarFill")
    connect(branch, "else", get_fill_tag, "execute")

    fill_item = fn("/Script/Engine.KismetArrayLibrary.Array_Get", 1880, 1380)
    connect(get_fill_tag, "OutActors", fill_item, "TargetArray")
    PINLIB.set_pin_value(pin(fill_item, "Index", False), "0")

    set_fill_scale = fn("/Script/Engine.Actor.SetActorScale3D", 2520, 1200)
    connect(get_fill_tag, "then", set_fill_scale, "execute")
    connect(fill_item, "Item", set_fill_scale, "self")
    connect(make_scale, "ReturnValue", set_fill_scale, "NewScale3D")

    BPLIB.compile_blueprint(bp)
    saved = ASSETS.save_loaded_asset(bp)
    print(f"[STEP3] BP_Boss_Overlord SAVED: {saved}")

if __name__ == "__main__":
    run()
