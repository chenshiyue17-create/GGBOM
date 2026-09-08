"""Read the saved game without trusting historical PASS reports."""
import json
from pathlib import Path
import unreal as u
root = Path(u.Paths.project_dir()).resolve()
B, P = u.BlueprintEditorLibrary, u.BlueprintGraphPinLibrary
result = {"assets": {}, "map": []}
paths = ["/Game/Blueprints/Player/BP_Player_Medic", "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase", "/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker", "/Game/Blueprints/Stage/BP_StageWaveManager"]
for path in paths:
    bp = u.load_asset(path)
    item = {"graphs": [], "components": []}
    for graph in B.list_graphs(bp):
        ed = u.BlueprintGraphEditor.get_graph_editor(graph)
        nodes = ed.list_all_nodes()
        item["graphs"].append({"name": graph.get_name(), "count": len(nodes), "errors": [B.get_node_title(n) for n in ed.list_nodes_with_errors()], "nodes": [{"title":B.get_node_title(n),"outputs":[{"name":str(P.get_pin_name(p)),"links":len(P.list_connected_pins(p))} for p in B.list_output_pins(n)]} for n in nodes]})
    cdo = u.get_default_object(bp.generated_class())
    for c in cdo.get_components_by_class(u.ActorComponent):
        item["components"].append({"name":c.get_name(),"class":c.get_class().get_name()})
    result["assets"][path] = item
world = u.EditorLoadingAndSavingUtils.load_map("/Game/GGBOM/Maps/MAP_GGBOM_Main")
for a in u.EditorLevelLibrary.get_all_level_actors():
    item={"label":a.get_actor_label(),"class":a.get_class().get_name(),"location":str(a.get_actor_location())}
    if isinstance(a,u.CameraActor):
        item.update(right=str(a.get_actor_right_vector()),up=str(a.get_actor_up_vector()),rotation=str(a.get_actor_rotation()))
    result["map"].append(item)
(root/"output/current_playable_audit.json").write_text(json.dumps(result,ensure_ascii=False,indent=2))
print("CURRENT_AUDIT_COMPLETE",flush=True)
