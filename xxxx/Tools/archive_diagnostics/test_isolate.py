# -*- coding: utf-8 -*-
import unreal
from pathlib import Path

BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary
ASSETS = unreal.EditorAssetLibrary

def log(msg):
    unreal.log(f"[TEST_ISOLATE] {msg}")
    print(f"[TEST_ISOLATE] {msg}", flush=True)

bp_path = "/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord"
bp = ASSETS.load_asset(bp_path)
graph = BPLIB.find_event_graph(bp)
ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)

log("1. Testing add_event_override ReceiveActorBeginOverlap...")
try:
    overlap_evt = BPLIB.add_event_override(bp, "ReceiveActorBeginOverlap", unreal.IntPoint(0, 450))
    log(f"   Success: {overlap_evt}")
    ed.remove_nodes([overlap_evt])
except Exception as e:
    log(f"   Failed: {e}")

log("Test isolate finished successfully.")
