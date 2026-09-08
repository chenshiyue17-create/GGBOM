# -*- coding: utf-8 -*-
import unreal

BPLIB = unreal.BlueprintEditorLibrary
ASSETS = unreal.EditorAssetLibrary

bp_path = "/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord"
bp = ASSETS.load_asset(bp_path)
graph = BPLIB.find_event_graph(bp)
ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)

nodes = [
    "/Script/Engine.GameplayStatics.GetPlayerPawn",
    "/Script/Engine.KismetMathLibrary.NotEqual_ObjectObject",
    "/Script/Engine.Actor.K2_GetActorLocation",
    "/Script/Engine.KismetMathLibrary.Subtract_VectorVector",
    "/Script/Engine.KismetMathLibrary.Normal",
    "/Script/Engine.KismetMathLibrary.Multiply_VectorVector",
    "/Script/Engine.Actor.K2_AddActorWorldOffset"
]

res = []
for p in nodes:
    try:
        n = ed.add_call_function_node(p)
        res.append(f"SUCCESS: {p} -> {n.get_name() if n else 'None'}")
        if n: ed.remove_nodes([n])
    except Exception as e:
        res.append(f"FAIL: {p} -> {e}")

print("\n".join(res))
from pathlib import Path
ROOT = Path(unreal.Paths.project_dir()).resolve()
(ROOT / "output/test_overlap_nodes.txt").write_text("\n".join(res), encoding="utf-8")
