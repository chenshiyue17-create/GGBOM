import unreal

bp_path = "/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker"
bp = unreal.load_asset(bp_path)

subsystems = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
handles = subsystems.k2_gather_subobject_data_for_blueprint(bp)

pmc = None
for h in handles:
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
    if isinstance(obj, unreal.ProjectileMovementComponent):
        pmc = obj
        break

if not pmc:
    params = unreal.AddNewSubobjectParams()
    params.set_editor_property("parent_handle", handles[0])
    params.set_editor_property("new_class", unreal.ProjectileMovementComponent.static_class())
    params.set_editor_property("blueprint_context", bp)
    h, reason = subsystems.add_new_subobject(params)
    if unreal.SubobjectDataBlueprintFunctionLibrary.is_handle_valid(h):
        subsystems.rename_subobject(h, unreal.Text("EnemyMovement"))
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        pmc = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)

if pmc:
    pmc.set_editor_property("initial_speed", 65.0)
    pmc.set_editor_property("max_speed", 65.0)
    pmc.set_editor_property("velocity", unreal.Vector(0.0, 0.0, -65.0))
    pmc.set_editor_property("projectile_gravity_scale", 0.0)
    try:
        pmc.set_editor_property("rotation_follows_velocity", False)
    except Exception:
        pass
    print("Successfully configured ProjectileMovementComponent on ZombieWalker!")

unreal.BlueprintEditorLibrary.compile_blueprint(bp)
unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
print("Compiled and saved ZombieWalker successfully!")
