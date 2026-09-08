# -*- coding: utf-8 -*-
"""
深入诊断玩家胶囊体、碰撞配置、子弹 ProjectileMovement 与发射关系
"""
import unreal

bp_player_path = "/Game/Blueprints/Player/BP_Player_Medic"
bp_proj_path = "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase"

print("=" * 60)
print("DIAG_START: 诊断玩家与子弹碰撞及属性设置...")
print("=" * 60)

bp_player = unreal.load_asset(bp_player_path)
if bp_player:
    print(f"PLAYER_BP_FOUND: {bp_player_path}")
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = sub.k2_gather_subobject_data_for_blueprint(bp_player)
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp_player)
        print(f"  [Player Comp] {vname}: {type(obj).__name__}")
        if isinstance(obj, unreal.ShapeComponent):
            col_prof = obj.get_editor_property("collision_profile_name")
            col_enabled = obj.get_editor_property("collision_enabled")
            print(f"     CollisionProfile: {col_prof}, CollisionEnabled: {col_enabled}")
            if isinstance(obj, unreal.CapsuleComponent):
                r = obj.get_editor_property("capsule_radius")
                h_val = obj.get_editor_property("capsule_half_height")
                print(f"     CapsuleRadius: {r}, CapsuleHalfHeight: {h_val}")
            elif isinstance(obj, unreal.BoxComponent):
                ext = obj.get_editor_property("box_extent")
                print(f"     BoxExtent: {ext}")

bp_proj = unreal.load_asset(bp_proj_path)
if bp_proj:
    print(f"\nPROJ_BP_FOUND: {bp_proj_path}")
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = sub.k2_gather_subobject_data_for_blueprint(bp_proj)
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp_proj)
        print(f"  [Proj Comp] {vname}: {type(obj).__name__}")
        if isinstance(obj, unreal.ShapeComponent):
            col_prof = obj.get_editor_property("collision_profile_name")
            col_enabled = obj.get_editor_property("collision_enabled")
            print(f"     CollisionProfile: {col_prof}, CollisionEnabled: {col_enabled}")
            if isinstance(obj, unreal.SphereComponent):
                r = obj.get_editor_property("sphere_radius")
                print(f"     SphereRadius: {r}")
        elif isinstance(obj, unreal.ProjectileMovementComponent):
            init_sp = obj.get_editor_property("initial_speed")
            max_sp = obj.get_editor_property("max_speed")
            in_local = obj.get_editor_property("initial_velocity_in_local_space")
            rot_fol = obj.get_editor_property("rotation_follows_velocity")
            bounce = obj.get_editor_property("should_bounce")
            grav = obj.get_editor_property("projectile_gravity_scale")
            vel = obj.get_editor_property("velocity")
            print(f"     InitialSpeed: {init_sp}, MaxSpeed: {max_sp}")
            print(f"     InitialVelocityInLocalSpace: {in_local}")
            print(f"     RotationFollowsVelocity: {rot_fol}")
            print(f"     ShouldBounce: {bounce}")
            print(f"     GravityScale: {grav}")
            print(f"     Default Velocity: {vel}")

print("DIAG_END")
