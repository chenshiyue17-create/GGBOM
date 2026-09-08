# -*- coding: utf-8 -*-
import unreal
from pathlib import Path

BPLIB = unreal.BlueprintEditorLibrary
ASSETS = unreal.EditorAssetLibrary

bp_path = "/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord"
bp = ASSETS.load_asset(bp_path)
graph = BPLIB.find_event_graph(bp)
ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)

nodes_to_test = [
    "/Script/Engine.GameplayStatics.GetPlayerPawn",
    "/Script/Engine.Actor.K2_GetActorLocation",
    "/Script/Engine.KismetMathLibrary.Vector_Distance",
    "/Script/Engine.KismetMathLibrary.Greater_DoubleDouble",
    "/Script/Engine.KismetMathLibrary.Subtract_VectorVector",
    "/Script/Engine.KismetMathLibrary.Normal",
    "/Script/Engine.KismetMathLibrary.BreakVector",
    "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble",
    "/Script/Engine.KismetMathLibrary.MakeVector",
    "/Script/Engine.Actor.K2_AddActorWorldOffset",
    "/Script/Engine.Actor.GetComponentByClass",
    "/Script/Engine.KismetMathLibrary.Abs",
    "/Script/Paper2D.PaperFlipbookComponent.SetFlipbook"
]

results = []
for p in nodes_to_test:
    try:
        n = ed.add_call_function_node(p)
        results.append(f"SUCCESS: {p} -> {n.get_name() if n else 'None'}")
        if n:
            ed.remove_nodes([n])
    except Exception as e:
        results.append(f"FAIL: {p} -> {e}")

out = Path(unreal.Paths.project_dir()).resolve() / "output/test_fn_nodes.txt"
out.write_text("\n".join(results), encoding="utf-8")
print("Finished testing nodes")
