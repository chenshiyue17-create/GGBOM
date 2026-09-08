# -*- coding: utf-8 -*-
import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/event_types.txt"

BPLIB = unreal.BlueprintEditorLibrary
ASSETS = unreal.EditorAssetLibrary

lines = []
for bp_path in [
    "/Game/Blueprints/Characters/Enemies/BP_Enemy_MutantHound",
    "/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker",
    "/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord"
]:
    bp = ASSETS.load_asset(bp_path)
    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    lines.append(f"BP: {bp.get_name()}")
    for n in ed.list_all_nodes():
        if isinstance(n, unreal.K2Node_Event):
            # 获取事件名称
            ref = n.get_editor_property("EventReference")
            mname = ref.get_editor_property("member_name") if ref else "None"
            fname = n.get_editor_property("custom_function_name")
            lines.append(f"  EventNode: {n.get_name()}, MemberName={mname}, CustomName={fname}")

OUT.write_text("\n".join(lines), encoding="utf-8")
print("Saved event types")
