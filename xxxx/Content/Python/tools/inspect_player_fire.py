# -*- coding: utf-8 -*-
import unreal

bp = unreal.load_asset("/Game/Blueprints/Player/BP_Player_Medic")
graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
nodes = ed.list_all_nodes()

with open("/Users/cc/Desktop/GGBOM/xxxx/output/player_spawn_inspect.txt", "w", encoding="utf-8") as f:
    for n in nodes:
        title = unreal.BlueprintEditorLibrary.get_node_title(n)
        if "spawn" in title.lower() or "actor" in title.lower():
            f.write(f"Node: {n.get_name()} | Title: {title} | Class: {n.get_class().get_name()}\n")
            inputs = unreal.BlueprintEditorLibrary.list_input_pins(n)
            for inp in inputs:
                p_name = unreal.BlueprintGraphPinLibrary.get_pin_name(inp)
                p_val = unreal.BlueprintGraphPinLibrary.get_pin_value(inp)
                f.write(f"    InPin: {p_name} = {p_val}\n")

print("Done inspect_player_fire.py")
