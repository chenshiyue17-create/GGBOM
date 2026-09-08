# -*- coding: utf-8 -*-
"""Disposable build probe for Sequence and cross-object variable nodes."""
import json
from pathlib import Path

import unreal

root = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
out = root / "output" / "direction_build_api_probe.json"
assets = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
bplib = unreal.BlueprintEditorLibrary
pinlib = unreal.BlueprintGraphPinLibrary
base = "/Game/Tests/DirectionProbe"
assets.make_directory(base)


def pins(node):
    if not node:
        return None
    return {
        "class": node.get_class().get_name(),
        "title": bplib.get_node_title(node),
        "inputs": [str(pinlib.get_pin_name(p)) for p in bplib.list_input_pins(node)],
        "outputs": [str(pinlib.get_pin_name(p)) for p in bplib.list_output_pins(node)],
    }


def make_bp(name):
    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", unreal.Actor.static_class())
    return tools.create_asset(name, base, unreal.Blueprint, factory)


result = {"sequence": [], "variables": {}}
bp_a = make_bp("BP_ProbeA")
bp_b = make_bp("BP_ProbeB")
try:
    ed_a = unreal.BlueprintGraphEditor.get_graph_editor(bplib.find_event_graph(bp_a))
    for candidate in (
        "Utilities|Flow Control|Sequence",
        "Utilities|FlowControl|Sequence",
        "Flow Control|Sequence",
        "工具|流程控制|Sequence",
        "工具|流控制|Sequence",
    ):
        try:
            node = ed_a.create_node_from_name(candidate, unreal.Vector2D(0, 0), [])
            result["sequence"].append({"candidate": candidate, "node": pins(node)})
            if node:
                ed_a.remove_nodes([node])
        except Exception as exc:
            result["sequence"].append({"candidate": candidate, "error": str(exc)})

    vector_type = bplib.get_struct_type(unreal.Vector.static_struct())
    result["variables"]["add_a"] = ed_a.add_member_variable("MoveInput", vector_type, "0,0,0")
    ed_b = unreal.BlueprintGraphEditor.get_graph_editor(bplib.find_event_graph(bp_b))
    result["variables"]["add_b"] = ed_b.add_member_variable("ShotDirection", vector_type, "0,0,-1")
    bplib.compile_blueprint(bp_a)
    bplib.compile_blueprint(bp_b)
    result["variables"]["get_self"] = pins(ed_a.add_get_member_variable_node("MoveInput"))
    result["variables"]["set_self"] = pins(ed_a.add_set_member_variable_node("MoveInput"))
    b_class_path = bp_b.generated_class().get_path_name()
    result["variables"]["b_class_path"] = b_class_path
    result["variables"]["set_other"] = pins(ed_a.add_set_member_variable_node("ShotDirection", b_class_path))
finally:
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    assets.delete_asset(f"{base}/BP_ProbeA")
    assets.delete_asset(f"{base}/BP_ProbeB")
