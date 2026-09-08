# -*- coding: utf-8 -*-
import unreal

graph = unreal.BlueprintEditorLibrary.find_event_graph(unreal.load_asset("/Game/Blueprints/Player/BP_Player_Medic"))
ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)

methods = [m for m in dir(ed) if not m.startswith("_")]
bplib_methods = [m for m in dir(unreal.BlueprintEditorLibrary) if not m.startswith("_")]

with open("/Users/cc/Desktop/GGBOM/xxxx/output/api_methods.txt", "w", encoding="utf-8") as f:
    f.write("=== BlueprintGraphEditor METHODS ===\n")
    for m in sorted(methods):
        f.write(f"  {m}\n")
    f.write("\n=== BlueprintEditorLibrary METHODS ===\n")
    for m in sorted(bplib_methods):
        f.write(f"  {m}\n")

print("Done writing api_methods.txt")
