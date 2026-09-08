# -*- coding: utf-8 -*-
"""Read-only audit of the live player/projectile Blueprint direction graphs."""
from __future__ import annotations

import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
OUT = ROOT / "output" / "direction_graph_after_fix.json"
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary


def describe_graph(graph) -> dict:
    editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    nodes = []
    for node in editor.list_all_nodes():
        item = {
            "name": node.get_name(),
            "title": BPLIB.get_node_title(node),
            "class": node.get_class().get_name(),
            "inputs": [],
            "outputs": [],
        }
        for key, output in (("inputs", False), ("outputs", True)):
            pins = BPLIB.list_output_pins(node) if output else BPLIB.list_input_pins(node)
            for graph_pin in pins:
                linked = PINLIB.list_connected_pins(graph_pin)
                item[key].append({
                    "name": str(PINLIB.get_pin_name(graph_pin)),
                    "value": PINLIB.get_pin_value(graph_pin),
                    "linked_count": len(linked),
                    "linked_nodes": [p.get_owning_node().get_name() for p in linked],
                })
        nodes.append(item)
    return {
        "name": graph.get_name(),
        "node_count": len(nodes),
        "compiler_errors": [BPLIB.get_node_title(n) for n in editor.list_nodes_with_errors()],
        "nodes": nodes,
    }


def describe_blueprint(path: str) -> dict:
    bp = unreal.load_asset(path)
    if not bp:
        return {"path": path, "found": False}
    variables = [str(v) for v in BPLIB.list_member_variable_names(bp, False)]
    graphs = [describe_graph(graph) for graph in BPLIB.list_graphs(bp)]
    event_graph = next((graph for graph in graphs if graph["name"] == "EventGraph"), None)
    return {
        "path": path,
        "found": True,
        "variables": variables,
        "node_count": event_graph["node_count"] if event_graph else 0,
        "compiler_errors": [error for graph in graphs for error in graph["compiler_errors"]],
        "graphs": graphs,
    }


payload = {
    "player": describe_blueprint("/Game/Blueprints/Player/BP_Player_Medic"),
    "projectile": describe_blueprint("/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase"),
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
unreal.log(f"DIRECTION_AUDIT_WRITTEN={OUT}")
