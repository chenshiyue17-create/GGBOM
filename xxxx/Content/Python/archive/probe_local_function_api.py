# -*- coding: utf-8 -*-
import json
from pathlib import Path
import unreal

root = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
base = "/Game/Tests/DirectionProbe"
unreal.EditorAssetLibrary.make_directory(base)
factory = unreal.BlueprintFactory()
factory.set_editor_property("parent_class", unreal.Actor.static_class())
bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset("BP_LocalFunctionProbe", base, unreal.Blueprint, factory)
result = {}
try:
    fed = unreal.BlueprintGraphEditor.create_and_edit_function_graph(bp, "ProbeFunction")
    result["entry"] = str(fed.find_graph_entry_pin().get_owning_node().get_name())
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(unreal.BlueprintEditorLibrary.find_event_graph(bp))
    for path in (
        f"{bp.generated_class().get_path_name()}:ProbeFunction",
        f"{bp.get_path_name()}.BP_LocalFunctionProbe_C:ProbeFunction",
        f"{bp.get_path_name()}:ProbeFunction",
    ):
        try:
            node = ed.add_call_function_node(path)
            result[path] = None if not node else {
                "title": unreal.BlueprintEditorLibrary.get_node_title(node),
                "inputs": [str(unreal.BlueprintGraphPinLibrary.get_pin_name(p)) for p in unreal.BlueprintEditorLibrary.list_input_pins(node)],
                "outputs": [str(unreal.BlueprintGraphPinLibrary.get_pin_name(p)) for p in unreal.BlueprintEditorLibrary.list_output_pins(node)],
            }
        except Exception as exc:
            result[path] = {"error": repr(exc)}
finally:
    (root / "output" / "local_function_api_probe.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    unreal.EditorAssetLibrary.delete_asset(f"{base}/BP_LocalFunctionProbe")
