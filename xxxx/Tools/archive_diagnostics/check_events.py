# -*- coding: utf-8 -*-
import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/check_events.txt"

bp = unreal.EditorAssetLibrary.load_asset("/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker")
graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
nodes = ed.list_all_nodes()

lines = []
for n in nodes:
    if isinstance(n, unreal.K2Node_Event):
        # 打印 event 节点的详细信息
        fn_name = n.event_reference.member_name if hasattr(n, "event_reference") else "None"
        lines.append(f"EventNode: {n.get_name()} | member_name: {fn_name}")

OUT.write_text("\n".join(lines), encoding="utf-8")
print("CHECK_EVENTS_DONE")
