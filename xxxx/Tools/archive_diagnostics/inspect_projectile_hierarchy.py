import unreal
import json

def inspect():
    bp_path = "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase"
    bp = unreal.EditorAssetLibrary.load_asset(bp_path)
    if not bp:
        print("Failed to load BP_ProjectileBase")
        return
        
    subsys = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = subsys.k2_gather_subobject_data_for_blueprint(bp)
    
    components = []
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        if not obj:
            continue
            
        parent_handle = unreal.SubobjectDataBlueprintFunctionLibrary.get_parent_handle(data)
        parent_name = "None"
        if unreal.SubobjectDataBlueprintFunctionLibrary.is_handle_valid(parent_handle):
            pdata = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(parent_handle)
            parent_name = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(pdata))
            
        comp_info = {
            "name": vname,
            "class": obj.get_class().get_name(),
            "parent": parent_name
        }
        
        if isinstance(obj, unreal.SceneComponent):
            comp_info["relative_scale3d"] = str(obj.get_editor_property("relative_scale3d"))
            comp_info["relative_location"] = str(obj.get_editor_property("relative_location"))
            comp_info["relative_rotation"] = str(obj.get_editor_property("relative_rotation"))
            comp_info["visible"] = obj.is_visible() if hasattr(obj, "is_visible") else True
            comp_info["hidden_in_game"] = obj.get_editor_property("hidden_in_game") if hasattr(obj, "hidden_in_game") else False
            
        if isinstance(obj, unreal.ProjectileMovementComponent):
            comp_info["initial_speed"] = obj.get_editor_property("initial_speed")
            comp_info["max_speed"] = obj.get_editor_property("max_speed")
            comp_info["velocity"] = str(obj.get_editor_property("velocity"))
            comp_info["gravity_scale"] = obj.get_editor_property("projectile_gravity_scale")
            comp_info["updated_component"] = str(obj.get_editor_property("updated_component"))
            
        components.append(comp_info)
        
    out_file = "/Users/cc/Desktop/GGBOM/xxxx/output/projectile_hierarchy.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(components, f, ensure_ascii=False, indent=2)
    print("Exported hierarchy to", out_file)

inspect()
