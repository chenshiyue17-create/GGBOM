# -*- coding: utf-8 -*-
import unreal
from pathlib import Path

ASSETS = unreal.EditorAssetLibrary
BPLIB = unreal.BlueprintEditorLibrary

bps = [
    "/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord",
    "/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker",
    "/Game/Blueprints/Characters/Enemies/BP_Enemy_MutantHound",
    "/Game/Blueprints/Player/BP_Player_Medic"
]

lines = []
subsys = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)

for p in bps:
    bp = ASSETS.load_asset(p)
    if not bp:
        continue
    lines.append(f"\n================ {p} ================")
    handles = subsys.k2_gather_subobject_data_for_blueprint(bp)
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data)
        is_root = unreal.SubobjectDataBlueprintFunctionLibrary.is_root_component(data)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        cname = obj.get_class().get_name() if obj else "None"
        lines.append(f"  Component: {vname} ({cname}) | is_root={is_root}")
        if isinstance(obj, unreal.PrimitiveComponent):
            lines.append(f"    CollisionEnabled: {obj.get_collision_enabled()}")
            lines.append(f"    Profile: {obj.get_collision_profile_name()}")
            lines.append(f"    ObjectType: {obj.get_collision_object_type()}")
            lines.append(f"    Resp WorldDyn: {obj.get_collision_response_to_channel(unreal.CollisionChannel.ECC_WORLD_DYNAMIC)}")
            lines.append(f"    Resp Pawn: {obj.get_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN)}")

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/component_hierarchy_audit.txt"
OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"Audit output to {OUT}")
