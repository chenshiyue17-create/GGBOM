# -*- coding: utf-8 -*-
import unreal

bp = unreal.load_asset("/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase")
graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)

nodes = ed.list_all_nodes()
with open("/Users/cc/Desktop/GGBOM/xxxx/output/proj_nodes.txt", "w", encoding="utf-8") as f:
    f.write(f"Node count: {len(nodes)}\n")
    for n in nodes:
        f.write(f"Node: {n.get_name()} | Title: {unreal.BlueprintEditorLibrary.get_node_title(n)} | Class: {n.get_class().get_name()}\n")

print("Done writing proj_nodes.txt")
