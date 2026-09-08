import unreal

GEN = "/Game/Blueprints/Characters/Enemies"
enemies = [
    "BP_Enemy_ZombieWalker",
    "BP_Enemy_ZombieRunner",
    "BP_Enemy_MutantHound",
    "BP_Enemy_VenomShooter",
    "BP_Enemy_ArmoredGuard",
    "BP_Enemy_MutantBrute",
    "BP_Boss_Overlord"
]

bplib = unreal.BlueprintEditorLibrary
subsystems = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)

for name in enemies:
    path = f"{GEN}/{name}"
    bp = unreal.load_asset(path)
    if not bp:
        print(f"FAILED TO LOAD: {path}")
        continue
    parent = bp.get_editor_property("parent_class")
    parent_name = parent.get_name() if parent else "None"
    print(f"=== {name} (Parent: {parent_name}) ===")
    
    handles = subsystems.k2_gather_subobject_data_for_blueprint(bp)
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        cls_name = obj.__class__.__name__ if obj else "None"
        print(f"  Component: {vname} ({cls_name})")
