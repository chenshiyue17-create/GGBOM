# -*- coding: utf-8 -*-
import unreal

bplib = unreal.BlueprintEditorLibrary
subsystems = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)

for bp_path in ["/Game/Blueprints/Player/BP_Player_Medic", "/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker"]:
    bp = unreal.load_asset(bp_path)
    print(f"=== Inspecting: {bp_path} ===")
    handles = subsystems.k2_gather_subobject_data_for_blueprint(bp)
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        is_root = unreal.SubobjectDataBlueprintFunctionLibrary.is_root_component(data)
        vname = unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data)
        print(f"   Name: {vname}, Class: {obj.get_class().get_name() if obj else 'None'}, IsRoot: {is_root}")
