# -*- coding: utf-8 -*-
import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/probe_master_hud.txt"

bp_path = "/Game/GGBOM/Blueprints/BP_GGBOM_MasterHUD"
bp = unreal.EditorAssetLibrary.load_asset(bp_path)
lines = [f"MasterHUD BP: {bp.get_name() if bp else 'None'}"]

if bp:
    graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    nodes = ed.list_all_nodes()
    lines.append(f"EventGraph Nodes ({len(nodes)}):")
    for n in nodes:
        lines.append(f"  - [{n.get_class().get_name()}] {n.get_name()}")

OUT.write_text("\n".join(lines), encoding="utf-8")
print("PROBE_MASTER_HUD_DONE")
