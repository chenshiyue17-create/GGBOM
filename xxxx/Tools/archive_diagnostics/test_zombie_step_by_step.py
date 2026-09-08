# -*- coding: utf-8 -*-
import unreal
from pathlib import Path
import traceback

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/test_zombie_step.txt"

ASSETS = unreal.EditorAssetLibrary
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary

lines = []
def log(msg):
    lines.append(str(msg))
    print(msg, flush=True)

try:
    bp_path = "/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker"
    bp = ASSETS.load_asset(bp_path)
    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    log("Loaded BP and graph")

    dmg_node = BPLIB.add_event_override(bp, "ReceiveAnyDamage", unreal.IntPoint(0, 1000))
    log(f"dmg_node: {dmg_node.get_name() if dmg_node else 'None'}")
    if dmg_node:
        out_pins = [str(PINLIB.get_pin_name(p)) for p in BPLIB.list_output_pins(dmg_node)]
        log(f"dmg out pins: {out_pins}")

    cur_hp = ed.add_get_member_variable_node("CurrentHealth")
    log(f"cur_hp: {cur_hp.get_name() if cur_hp else 'None'}")
    if cur_hp:
        out_pins = [str(PINLIB.get_pin_name(p)) for p in BPLIB.list_output_pins(cur_hp)]
        log(f"cur_hp out pins: {out_pins}")

    set_hp = ed.add_set_member_variable_node("CurrentHealth")
    log(f"set_hp: {set_hp.get_name() if set_hp else 'None'}")
    if set_hp:
        in_pins = [str(PINLIB.get_pin_name(p)) for p in BPLIB.list_input_pins(set_hp)]
        out_pins = [str(PINLIB.get_pin_name(p)) for p in BPLIB.list_output_pins(set_hp)]
        log(f"set_hp in pins: {in_pins}, out pins: {out_pins}")

    sub_hp = ed.add_call_function_node("/Script/Engine.KismetMathLibrary.Subtract_DoubleDouble")
    log(f"sub_hp: {sub_hp.get_name() if sub_hp else 'None'}")
    if sub_hp:
        in_pins = [str(PINLIB.get_pin_name(p)) for p in BPLIB.list_input_pins(sub_hp)]
        out_pins = [str(PINLIB.get_pin_name(p)) for p in BPLIB.list_output_pins(sub_hp)]
        log(f"sub_hp in pins: {in_pins}, out pins: {out_pins}")

    is_dead = ed.add_call_function_node("/Script/Engine.KismetMathLibrary.LessEqual_DoubleDouble")
    log(f"is_dead: {is_dead.get_name() if is_dead else 'None'}")
    if is_dead:
        in_pins = [str(PINLIB.get_pin_name(p)) for p in BPLIB.list_input_pins(is_dead)]
        out_pins = [str(PINLIB.get_pin_name(p)) for p in BPLIB.list_output_pins(is_dead)]
        log(f"is_dead in pins: {in_pins}, out pins: {out_pins}")

    branch = ed.add_branch_node()
    log(f"branch: {branch.get_name() if branch else 'None'}")
    if branch:
        in_pins = [str(PINLIB.get_pin_name(p)) for p in BPLIB.list_input_pins(branch)]
        out_pins = [str(PINLIB.get_pin_name(p)) for p in BPLIB.list_output_pins(branch)]
        log(f"branch in pins: {in_pins}, out pins: {out_pins}")

    destroy = ed.add_call_function_node("/Script/Engine.Actor.K2_DestroyActor")
    log(f"destroy: {destroy.get_name() if destroy else 'None'}")
    if destroy:
        in_pins = [str(PINLIB.get_pin_name(p)) for p in BPLIB.list_input_pins(destroy)]
        out_pins = [str(PINLIB.get_pin_name(p)) for p in BPLIB.list_output_pins(destroy)]
        log(f"destroy in pins: {in_pins}, out pins: {out_pins}")

    # 连线
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

    log("Connecting sub_hp...")
    connect(cur_hp, "CurrentHealth", sub_hp, "A")
    connect(dmg_node, "Damage", sub_hp, "B")

    log("Connecting set_hp...")
    connect(dmg_node, "then", set_hp, "execute")
    connect(sub_hp, "ReturnValue", set_hp, "CurrentHealth")

    log("Connecting is_dead...")
    connect(sub_hp, "ReturnValue", is_dead, "A")
    set_value(is_dead, "B", "0.0")

    log("Connecting branch...")
    connect(set_hp, "then", branch, "execute")
    connect(is_dead, "ReturnValue", branch, "Condition")

    log("Connecting destroy...")
    connect(branch, "then", destroy, "execute")

    log("Compiling...")
    BPLIB.compile_blueprint(bp)
    saved = ASSETS.save_loaded_asset(bp)
    log(f"SAVED: {saved}")

except Exception as e:
    log(f"EXCEPTION: {traceback.format_exc()}")

OUT.write_text("\n".join(lines), encoding="utf-8")
print("TEST_ZOMBIE_STEP_DONE")
