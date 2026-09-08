# -*- coding: utf-8 -*-
import unreal

bp_proj_path = "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase"
bp = unreal.load_asset(bp_proj_path)

out = []
if bp:
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = sub.k2_gather_subobject_data_for_blueprint(bp)
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        if isinstance(obj, unreal.ProjectileMovementComponent):
            out.append(f"PMC: initial_speed={obj.get_editor_property('initial_speed')}, max_speed={obj.get_editor_property('max_speed')}, velocity={obj.get_editor_property('velocity')}")
        elif isinstance(obj, (unreal.PaperFlipbookComponent, unreal.PaperSpriteComponent)):
            out.append(f"{type(obj).__name__}: scale={obj.get_editor_property('relative_scale3d')}, sort={obj.get_editor_property('translucency_sort_priority')}")

with open("/Users/cc/Desktop/GGBOM/proj_settings.txt", "w") as f:
    f.write("\n".join(out))
print("DONE_PROJ_SETTINGS")
