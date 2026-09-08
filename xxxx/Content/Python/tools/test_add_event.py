# -*- coding: utf-8 -*-
import unreal

bp = unreal.load_asset("/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase")
graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)

print("Testing find ReceiveTick:", ed.find_event_node("ReceiveTick"))
try:
    node = unreal.BlueprintEditorLibrary.add_event_override(bp, "ReceiveTick")
    print("add_event_override returned:", node)
except Exception as e:
    print("add_event_override error:", e)

print("After override, find ReceiveTick:", ed.find_event_node("ReceiveTick"))
