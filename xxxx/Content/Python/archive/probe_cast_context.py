import json
from pathlib import Path
import unreal

root = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
factory = unreal.BlueprintFactory(); factory.set_editor_property("parent_class", unreal.Actor.static_class())
bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset("BP_CastContextProbe", "/Game/Tests/DirectionProbe", unreal.Blueprint, factory)
ed = unreal.BlueprintGraphEditor.create_and_edit_function_graph(bp, "Probe")
spawn = ed.add_call_function_node("/Script/Engine.GameplayStatics.BeginDeferredActorSpawnFromClass")
inputs = unreal.BlueprintEditorLibrary.list_input_pins(spawn)
for p in inputs:
    if str(unreal.BlueprintGraphPinLibrary.get_pin_name(p)) == "ActorClass":
        unreal.BlueprintGraphPinLibrary.set_pin_value(p, "Class'/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase.BP_ProjectileBase_C'")
ret = [p for p in unreal.BlueprintEditorLibrary.list_output_pins(spawn) if str(unreal.BlueprintGraphPinLibrary.get_pin_name(p)) == "ReturnValue"][0]
items = [str(x) for x in ed.list_available_nodes([ret])]
matches = [x for x in items if "cast" in x.lower() or "projectile" in x.lower() or "投射" in x]
(root / "output" / "cast_context_probe.json").write_text(json.dumps({"count": len(items), "matches": matches}, ensure_ascii=False, indent=2), encoding="utf-8")
