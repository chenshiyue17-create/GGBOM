# -*- coding: utf-8 -*-
import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/hound_trace_log.txt"
lines = []

def log(msg):
    lines.append(msg)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(msg, flush=True)

BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary
ASSETS = unreal.EditorAssetLibrary

log("1. Loading Hound BP...")
bp_path = "/Game/Blueprints/Characters/Enemies/BP_Enemy_MutantHound"
bp = ASSETS.load_asset(bp_path)
graph = BPLIB.find_event_graph(bp)
ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
tick_node = ed.find_event_node("ReceiveTick")
log(f"   BP loaded, tick_node={tick_node}")

HOUND_ART = "/Game/P01/Imported/Content/Asset/Art/02_Enemies/MutantHound"
log("2. Loading Flipbooks...")
fb_run_down = unreal.load_asset(f"{HOUND_ART}/Run/Dir_01_Down/Flipbooks/FB_T_Hound_Run_Dir_01_Down_Sheet.FB_T_Hound_Run_Dir_01_Down_Sheet")
fb_run_right = unreal.load_asset(f"{HOUND_ART}/Run/Dir_02_Right/Flipbooks/FB_T_Hound_Run_Dir_02_Right_Sheet.FB_T_Hound_Run_Dir_02_Right_Sheet")
fb_run_up = unreal.load_asset(f"{HOUND_ART}/Run/Dir_03_Up/Flipbooks/FB_T_Hound_Run_Dir_03_Up_Sheet.FB_T_Hound_Run_Dir_03_Up_Sheet")
fb_run_left = unreal.load_asset(f"{HOUND_ART}/Run/Dir_04_Left/Flipbooks/FB_T_Hound_Run_Dir_04_Left_Sheet.FB_T_Hound_Run_Dir_04_Left_Sheet")
fb_pounce_down = unreal.load_asset(f"{HOUND_ART}/Pounce/Dir_01_Down/Flipbooks/FB_T_Hound_Pounce_Dir_01_Down_Sheet.FB_T_Hound_Pounce_Dir_01_Down_Sheet")
log("   Flipbooks loaded.")

def pin(node, name, output=None):
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

def fn(path, x, y):
    log(f"   add node: {path}")
    node = ed.add_call_function_node(path)
    node.set_node_pos(unreal.IntPoint(x, y))
    return node

log("3. Creating sampling nodes...")
get_player = fn("/Script/Engine.GameplayStatics.GetPlayerPawn", 220, 100)
set_value(get_player, "PlayerIndex", 0)

p_loc = fn("/Script/Engine.Actor.K2_GetActorLocation", 460, 40)
connect(get_player, "ReturnValue", p_loc, "self")

self_loc = fn("/Script/Engine.Actor.K2_GetActorLocation", 460, 180)

dist_node = fn("/Script/Engine.KismetMathLibrary.Vector_Distance", 700, -80)
connect(p_loc, "ReturnValue", dist_node, "v1")
connect(self_loc, "ReturnValue", dist_node, "v2")

is_far = fn("/Script/Engine.KismetMathLibrary.Greater_DoubleDouble", 940, -80)
connect(dist_node, "ReturnValue", is_far, "A")
set_value(is_far, "B", 75.0)

log("4. Creating branch gate...")
br_gate = ed.add_branch_node()
connect(tick_node, "then", br_gate, "execute")
connect(is_far, "ReturnValue", br_gate, "Condition")

log("5. Finished Hound test!")
