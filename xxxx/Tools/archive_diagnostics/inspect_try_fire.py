# -*- coding: utf-8 -*-
import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/try_fire_nodes.txt"

bp = unreal.EditorAssetLibrary.load_asset("/Game/Blueprints/Player/BP_Player_Medic")
lines = []

for g in bp.function_graphs:
    if "TryFireProjectile" in g.get_name():
        lines.append(f"Function Graph: {g.get_name()}")
        ed = unreal.BlueprintGraphEditor.get_graph_editor(g)
        nodes = ed.list_all_nodes()
        for n in nodes:
            lines.append(f"  - [{n.get_class().get_name()}] {n.get_name()} | Title: {unreal.BlueprintEditorLibrary.get_node_title(n)}")

OUT.write_text("\n".join(lines), encoding="utf-8")
print("TRY_FIRE_DONE")
