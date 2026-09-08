# -*- coding: utf-8 -*-
import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/hound_all_nodes.txt"

ASSETS = unreal.EditorAssetLibrary
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary

bp = ASSETS.load_asset("/Game/Blueprints/Characters/Enemies/BP_Enemy_MutantHound")
graph = BPLIB.find_event_graph(bp)
ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
nodes = ed.list_all_nodes()

lines = []
for n in nodes:
    title = BPLIB.get_node_title(n)
    lines.append(f"\nNode: [{n.get_class().get_name()}] {title}")
    for p in BPLIB.list_input_pins(n):
        lines.append(f"  In: {PINLIB.get_pin_name(p)}")
    for p in BPLIB.list_output_pins(n):
        lines.append(f"  Out: {PINLIB.get_pin_name(p)}")

OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"Total nodes: {len(nodes)}, dumped to {OUT}")
