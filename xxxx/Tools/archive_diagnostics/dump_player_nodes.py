# -*- coding: utf-8 -*-
import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/player_all_nodes.txt"

bp = unreal.EditorAssetLibrary.load_asset("/Game/Blueprints/Player/BP_Player_Medic")
graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
nodes = ed.list_all_nodes()

lines = [f"Player Medic Total Nodes: {len(nodes)}"]
for n in nodes:
    title = str(unreal.BlueprintEditorLibrary.get_node_title(n))
    lines.append(f"Node: {n.get_name()} | Title: {title} | Class: {n.get_class().get_name()}")

OUT.write_text("\n".join(lines), encoding="utf-8")
print("PLAYER_ALL_NODES_DONE")
