# -*- coding: utf-8 -*-
import unreal

def inspect_bp(path):
    print(f"\n================ INSPECTING: {path} ================")
    bp = unreal.load_asset(path)
    if not bp:
        print("Asset not found!")
        return
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = sub.k2_gather_subobject_data_for_blueprint(bp)
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        print(f"Component: {vname} | Class: {type(obj).__name__}")
        for prop_name in ["capsule_radius", "capsule_half_height", "box_extent", "sphere_radius", 
                          "initial_speed", "max_speed", "initial_velocity_in_local_space", 
                          "rotation_follows_velocity", "should_bounce", "velocity", 
                          "relative_location", "relative_rotation", "relative_scale3d"]:
            try:
                val = obj.get_editor_property(prop_name)
                print(f"    {prop_name} = {val}")
            except Exception:
                pass

inspect_bp("/Game/Blueprints/Player/BP_Player_Medic")
inspect_bp("/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase")
print("\nINSPECT_COMPLETE_SUCCESS")
