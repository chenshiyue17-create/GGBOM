# -*- coding: utf-8 -*-
import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/player_fire_nodes.txt"

bp_path = "/Game/Blueprints/Player/BP_Player_Medic"
bp = unreal.EditorAssetLibrary.load_asset(bp_path)
graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
nodes = ed.list_all_nodes()

lines = [f"Player Medic Nodes ({len(nodes)}):"]
for n in nodes:
    title = str(unreal.BlueprintEditorLibrary.get_node_title(n))
    if any(k in title.lower() or k in n.get_name().lower() for k in ["spawn", "bullet", "shoot", "key", "projectile", "j"]):
        lines.append(f"  - [{n.get_class().get_name()}] {n.get_name()} | Title: {title} | Pos: ({n.get_node_pos().x}, {n.get_node_pos().y})")

OUT.write_text("\n".join(lines), encoding="utf-8")
print("INSPECT_PLAYER_FIRE_DONE")
