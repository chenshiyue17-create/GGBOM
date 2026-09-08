# -*- coding: utf-8 -*-
import unreal

bp_path = "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase"
bp = unreal.load_asset(bp_path)
out = []

if bp:
    graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    if graph:
        nodes = graph.get_editor_property("nodes")
        out.append(f"Graph nodes count: {len(nodes)}")
        for n in nodes:
            out.append(f"Node: {n.get_name()} ({type(n).__name__})")

with open("/Users/cc/Desktop/GGBOM/proj_graph.txt", "w") as f:
    f.write("\n".join(out))
print("DONE_PROJ_GRAPH")
