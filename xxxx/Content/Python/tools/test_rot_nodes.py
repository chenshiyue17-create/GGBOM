# -*- coding: utf-8 -*-
import unreal

bp = unreal.load_asset("/Game/Blueprints/Player/BP_Player_Medic")
graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)

n1 = ed.add_call_function_node("/Script/Engine.Actor.K2_GetActorRotation")
n2 = ed.add_call_function_node("/Script/Engine.Actor.K2_SetActorRotation")
print(f"K2_GetActorRotation: {n1 is not None}")
print(f"K2_SetActorRotation: {n2 is not None}")
if n1: ed.remove_node(n1)
if n2: ed.remove_node(n2)
