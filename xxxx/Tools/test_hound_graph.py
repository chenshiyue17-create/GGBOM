# -*- coding: utf-8 -*-
import unreal

ASSETS = unreal.EditorAssetLibrary
BPLIB = unreal.BlueprintEditorLibrary

bp = ASSETS.load_asset("/Game/Blueprints/Characters/Enemies/BP_Enemy_MutantHound")
graph = BPLIB.find_event_graph(bp)
print(f"MutantHound BP: {bp}, Graph: {graph}")
ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
print(f"Editor: {ed}")
if ed:
    node = ed.add_call_function_node("/Script/Engine.KismetMathLibrary.Subtract_DoubleDouble")
    print(f"Node created: {node}")
