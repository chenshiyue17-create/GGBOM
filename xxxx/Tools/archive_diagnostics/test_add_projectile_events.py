# -*- coding: utf-8 -*-
import unreal

bp_path = "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase"
bp = unreal.EditorAssetLibrary.load_asset(bp_path)
graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)

print("Testing adding events to BP_ProjectileBase...")

import json

results = {
    "bplib_methods": [m for m in dir(unreal.BlueprintEditorLibrary) if "event" in m.lower() or "node" in m.lower() or "override" in m.lower()],
    "ed_methods": [m for m in dir(ed) if "event" in m.lower() or "node" in m.lower() or "override" in m.lower()],
    "tests": {}
}

for idx, ev_name in enumerate(["ReceiveHit", "ReceiveActorBeginOverlap", "ReceiveBeginPlay"]):
    try:
        node = unreal.BlueprintEditorLibrary.add_event_override(bp, ev_name, unreal.IntPoint(0, idx * 300))
        if node:
            pins = [str(unreal.BlueprintGraphPinLibrary.get_pin_name(p)) for p in unreal.BlueprintEditorLibrary.list_all_pins(node)]
            results["tests"][f"bplib_{ev_name}"] = {
                "success": True,
                "title": str(unreal.BlueprintEditorLibrary.get_node_title(node)),
                "pins": pins
            }
        else:
            results["tests"][f"bplib_{ev_name}"] = {"success": False, "error": "returned None"}
    except Exception as e:
        results["tests"][f"bplib_{ev_name}"] = {"success": False, "error": str(e)}

with open("/Users/cc/Desktop/GGBOM/xxxx/output/event_test_result.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

unreal.BlueprintEditorLibrary.compile_blueprint(bp)



