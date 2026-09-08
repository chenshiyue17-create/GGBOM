import unreal

bp = unreal.load_asset("/Game/Blueprints/Stage/BP_StageWaveManager")
if bp:
    bplib = unreal.BlueprintEditorLibrary
    graph = bplib.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph) if graph else None
    nodes = [bplib.get_node_title(n) for n in ed.list_all_nodes()] if ed else []
    print(f"BP_StageWaveManager Nodes: {nodes}")
    unreal.log(f"BP_StageWaveManager Nodes: {nodes}")
else:
    print("BP_StageWaveManager not found")
