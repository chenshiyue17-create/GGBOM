# -*- coding: utf-8 -*-
import unreal

bps = [
    "/Game/Blueprints/Player/BP_Player_Medic",
    "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase",
    "/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker",
    "/Game/Blueprints/Characters/Enemies/BP_Enemy_MutantHound",
    "/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord",
    "/Game/Blueprints/Pickups/BP_Pickup_ExpGem",
    "/Game/Blueprints/Stage/BP_StageWaveManager"
]

with open("/Users/cc/Desktop/GGBOM/xxxx/output/all_bp_nodes.txt", "w", encoding="utf-8") as f:
    for p in bps:
        f.write(f"\n========================================\nAsset: {p}\n")
        bp = unreal.load_asset(p)
        if not bp:
            f.write("  FAILED TO LOAD!\n")
            continue
        graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
        if not graph:
            f.write("  NO EVENT GRAPH!\n")
            continue
        ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
        nodes = ed.list_all_nodes()
        f.write(f"  Total nodes: {len(nodes)}\n")
        for n in nodes:
            f.write(f"    Node: {n.get_name()} | Title: {unreal.BlueprintEditorLibrary.get_node_title(n)} | Class: {n.get_class().get_name()}\n")

print("Done check_all_bp_nodes.py")
