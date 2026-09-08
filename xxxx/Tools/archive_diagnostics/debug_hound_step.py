# -*- coding: utf-8 -*-
import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/debug_hound_step.txt"

BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary
ASSETS = unreal.EditorAssetLibrary

lines = []
def log(msg):
    lines.append(str(msg))
    print(msg, flush=True)

try:
    bp_path = "/Game/Blueprints/Characters/Enemies/BP_Enemy_MutantHound"
    bp = ASSETS.load_asset(bp_path)
    log(f"1. Loaded BP: {bp}")
    graph = BPLIB.find_event_graph(bp)
    log(f"2. Found graph: {graph}")
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    log(f"3. Got ed: {ed}")
    nodes = ed.list_all_nodes()
    log(f"4. Node count: {len(nodes)}")
    for n in nodes:
        log(f"   Node: {n.get_name()} ({n.get_class().get_name()})")
except Exception as e:
    log(f"Exception: {e}")

OUT.write_text("\n".join(lines), encoding="utf-8")
