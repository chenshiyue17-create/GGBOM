# -*- coding: utf-8 -*-
import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/hound_existing_nodes.txt"

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
    cname = n.get_class().get_name()
    if "overlap" in title.lower() or "event" in cname.lower() or "tick" in title.lower():
        lines.append(f"Node: [{cname}] {title}")
        for p in BPLIB.list_output_pins(n):
            lines.append(f"  OutPin: {PINLIB.get_pin_name(p)}")

OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"Dumped to {OUT}")
