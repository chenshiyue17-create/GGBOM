# -*- coding: utf-8 -*-
import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/inspect_enemies_result.txt"
OUT.parent.mkdir(parents=True, exist_ok=True)

ASSETS = unreal.EditorAssetLibrary
BPLIB = unreal.BlueprintEditorLibrary

lines = []

paths = [
    "/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker",
    "/Game/Blueprints/Characters/Enemies/BP_Enemy_MutantHound",
    "/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord"
]

for p in paths:
    lines.append(f"=== Asset: {p} ===")
    bp = ASSETS.load_asset(p)
    if not bp:
        lines.append("  FAILED TO LOAD")
        continue
    lines.append("  Variables:")
    for v in bp.new_variables:
        lines.append(f"    {v.var_name} (category: {v.var_type.category})")
    
    graph = BPLIB.find_event_graph(bp)
    if graph:
        ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
        nodes = ed.list_all_nodes()
        lines.append(f"  EventGraph Nodes ({len(nodes)}):")
        for n in nodes:
            lines.append(f"    - [{n.get_class().get_name()}] {n.get_name()} ({n.get_node_pos().x}, {n.get_node_pos().y})")

OUT.write_text("\n".join(lines), encoding="utf-8")
print("INSPECT_COMPLETE", flush=True)
