# -*- coding: utf-8 -*-
import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/inspect_gamemode_and_level_bp.txt"

lines = []

gm_path = "/Game/GGBOM/Blueprints/BP_GGBOM_GameMode"
bp = unreal.EditorAssetLibrary.load_asset(gm_path)
if bp:
    lines.append(f"GameMode: {gm_path}")
    graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    nodes = ed.list_all_nodes() if ed else []
    lines.append(f"GameMode nodes: {len(nodes)}")
    for n in nodes:
        t = n.get_node_title(unreal.NodeTitleType.FULL_TITLE) if hasattr(n, "get_node_title") else str(n)
        lines.append(f"  GM Node: {t} [{n.get_class().get_name()}]")

# 检查关卡
map_path = "/Game/GGBOM/Maps/MAP_GGBOM_Main"
lvl = unreal.EditorAssetLibrary.load_asset(map_path)
lines.append(f"Map: {map_path} -> {lvl}")

OUT.write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
