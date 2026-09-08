# -*- coding: utf-8 -*-
import unreal
import json
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/bullet_connections_dump.json"

bp = unreal.EditorAssetLibrary.load_asset('/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase')
graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)

nodes_info = []
for n in ed.list_all_nodes():
    title = str(unreal.BlueprintEditorLibrary.get_node_title(n))
    pins = unreal.BlueprintEditorLibrary.list_all_pins(n)
    pin_links = []
    for p in pins:
        pname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(p))
        linked = unreal.BlueprintGraphPinLibrary.get_linked_to_pins(p)
        if linked:
            links = []
            for lp in linked:
                lnode = str(unreal.BlueprintEditorLibrary.get_node_title(unreal.BlueprintGraphPinLibrary.get_owning_node(lp)))
                lpname = str(unreal.BlueprintGraphPinLibrary.get_pin_name(lp))
                links.append(f"{lnode}.{lpname}")
            pin_links.append({"pin": pname, "linked_to": links})
    nodes_info.append({"title": title, "links": pin_links})

OUT.write_text(json.dumps(nodes_info, ensure_ascii=False, indent=2))
print("DONE DUMP")
