import unreal

bp = unreal.load_asset("/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker")
graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
nodes = [unreal.BlueprintEditorLibrary.get_node_title(n) for n in ed.list_all_nodes()]
print(f"BP_Enemy_ZombieWalker nodes: {len(nodes)}")
for n in nodes:
    print(f"  - {n}")
