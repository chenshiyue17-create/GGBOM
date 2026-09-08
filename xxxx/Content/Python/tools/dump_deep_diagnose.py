# -*- coding: utf-8 -*-
import unreal

out_file = "/Users/cc/Desktop/GGBOM/xxxx/diagnose_output.txt"

with open(out_file, "w", encoding="utf-8") as f:
    f.write("=== DIAGNOSE START ===\n")

def log(msg):
    with open(out_file, "a", encoding="utf-8") as f:
        f.write(str(msg) + "\n")

def audit_bp(bp_path, label):
    log(f"\n================ {label}: {bp_path} ================")
    bp = unreal.load_asset(bp_path)
    if not bp:
        log("Asset not found!")
        return
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = sub.k2_gather_subobject_data_for_blueprint(bp)
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        log(f"\n[Component] {vname} : {type(obj).__name__}")
        for p in ["capsule_radius", "capsule_half_height", "box_extent", "sphere_radius", 
                  "initial_speed", "max_speed", "initial_velocity_in_local_space", 
                  "b_initial_velocity_in_local_space", "rotation_follows_velocity", 
                  "b_rotation_follows_velocity", "should_bounce", "b_should_bounce", 
                  "velocity", "relative_location", "relative_rotation", "relative_scale3d", 
                  "projectile_gravity_scale", "collision_profile_name", "collision_enabled"]:
            try:
                val = obj.get_editor_property(p)
                log(f"   {p} = {val}")
            except:
                pass
        try:
            bi = obj.get_editor_property("body_instance")
            log(f"   bi.collision_profile_name = {bi.get_editor_property('collision_profile_name')}")
            log(f"   bi.collision_enabled = {bi.get_editor_property('collision_enabled')}")
            log(f"   bi.object_type = {bi.get_editor_property('object_type')}")
        except:
            pass

audit_bp("/Game/Blueprints/Player/BP_Player_Medic", "PLAYER")
audit_bp("/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase", "PROJECTILE")

log("\n=== DIAGNOSE FINISHED ===")
