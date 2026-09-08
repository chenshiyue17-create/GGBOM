"""Probe UE5.8 Blueprint graph actions needed by the GGBOM pure-BP build."""
from __future__ import annotations

import json
from pathlib import Path

import unreal


def pins(node, output: bool) -> list[str]:
    lib = unreal.BlueprintEditorLibrary
    values = lib.list_output_pins(node) if output else lib.list_input_pins(node)
    return [str(unreal.BlueprintGraphPinLibrary.get_pin_name(pin)) for pin in values]


def main() -> None:
    root = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
    out = root / "output"
    out.mkdir(parents=True, exist_ok=True)
    package = "/Game/GGBOM/Generated"
    unreal.EditorAssetLibrary.make_directory(package)
    asset_path = f"{package}/BP_GGBOM_Probe"
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        unreal.EditorAssetLibrary.delete_asset(asset_path)
    bp = unreal.BlueprintEditorLibrary.create_blueprint_asset_with_parent(
        asset_path, unreal.Actor.static_class()
    )
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    graph = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    report: dict[str, object] = {"actions": {}, "functions": {}, "events": {}}
    actions = [
        "Space Bar", "A", "D", "Left", "Right", "InputKey SpaceBar",
        "Get Player Controller", "Spawn Actor from Class", "Restart Level",
    ]
    for name in actions:
        try:
            node = editor.create_node_from_name(name, unreal.Vector2D(0, 0), [], None)
            report["actions"][name] = (
                {"valid": True, "in": pins(node, False), "out": pins(node, True)}
                if node else {"valid": False}
            )
        except Exception as exc:
            report["actions"][name] = {"valid": False, "error": str(exc)}
    functions = [
        "/Script/Engine.GameplayStatics.GetPlayerController",
        "/Script/Engine.PlayerController.IsInputKeyDown",
        "/Script/Engine.GameplayStatics.GetActorOfClass",
        "/Script/Engine.Actor.K2_GetActorLocation",
        "/Script/Engine.Actor.K2_SetActorLocation",
        "/Script/Engine.Actor.K2_AddActorWorldOffset",
        "/Script/Engine.KismetMathLibrary.MakeVector",
        "/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble",
        "/Script/Engine.KismetMathLibrary.Multiply_VectorFloat",
        "/Script/Engine.KismetMathLibrary.GetDirectionUnitVector",
        "/Script/Engine.KismetMathLibrary.Vector_Distance",
        "/Script/Engine.KismetMathLibrary.LessEqual_DoubleDouble",
        "/Script/Engine.KismetSystemLibrary.PrintString",
        "/Script/Engine.GameplayStatics.OpenLevel",
        "/Script/Engine.KismetSystemLibrary.QuitGame",
    ]
    for path in functions:
        try:
            node = editor.add_call_function_node(path)
            report["functions"][path] = (
                {"valid": True, "in": pins(node, False), "out": pins(node, True)}
                if node else {"valid": False}
            )
        except Exception as exc:
            report["functions"][path] = {"valid": False, "error": str(exc)}
    for event in ["ReceiveBeginPlay", "ReceiveTick", "ReceiveActorBeginOverlap", "ReceiveAnyDamage"]:
        try:
            node = editor.find_event_node(event)
            report["events"][event] = (
                {"valid": True, "in": pins(node, False), "out": pins(node, True)}
                if node else {"valid": False}
            )
        except Exception as exc:
            report["events"][event] = {"valid": False, "error": str(exc)}
    (out / "blueprint_api_probe.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    unreal.log("[GGBOM-Probe] PROBE_OK")


if __name__ == "__main__":
    main()
