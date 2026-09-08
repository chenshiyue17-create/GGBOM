import unreal

bplib = unreal.BlueprintEditorLibrary
enemies = [
    "BP_Enemy_ZombieWalker",
    "BP_Enemy_ZombieRunner",
    "BP_Enemy_MutantHound",
    "BP_Enemy_VenomShooter",
    "BP_Enemy_ArmoredGuard",
    "BP_Enemy_MutantBrute",
    "BP_Boss_Overlord"
]

for name in enemies:
    path = f"/Game/Blueprints/Characters/Enemies/{name}"
    bp = unreal.load_asset(path)
    if not bp:
        unreal.log(f"MISSING: {path}")
        continue
    graph = bplib.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph) if graph else None
    nodes = [bplib.get_node_title(n) for n in ed.list_all_nodes()] if ed else []
    unreal.log(f"{name} EventGraph Nodes ({len(nodes)}): {nodes}")
