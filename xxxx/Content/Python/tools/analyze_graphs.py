# -*- coding: utf-8 -*-
import unreal

bp_paths = [
    "/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker",
    "/Game/Blueprints/Characters/Enemies/BP_Enemy_MutantHound",
    "/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord",
    "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase",
    "/Game/Blueprints/Player/BP_Player_Medic"
]

out = []
for p in bp_paths:
    bp = unreal.load_asset(p)
    if not bp:
        out.append(f"[BP] NOT FOUND: {p}")
        continue
    graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    nodes = graph.get_editor_property("nodes") if graph else []
    out.append(f"\n=== BP: {p} (Nodes: {len(nodes)}) ===")
    for n in nodes:
        title = unreal.BlueprintEditorLibrary.get_node_title(n)
        cls_name = n.get_class().get_name()
        out.append(f"  - Node: {title} ({cls_name})")

with open("/Users/cc/Desktop/GGBOM/xxxx/Content/Python/tools/graph_analysis.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
unreal.log("Finished writing graph_analysis.txt")
