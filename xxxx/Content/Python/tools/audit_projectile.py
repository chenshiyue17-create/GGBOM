# -*- coding: utf-8 -*-
import unreal

bp_path = "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase"
bp = unreal.load_asset(bp_path)
lines = []

if bp:
    lines.append(f"BP_ProjectileBase Loaded: {bp_path}")
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = sub.k2_gather_subobject_data_for_blueprint(bp)
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        lines.append(f"Component: {vname} -> {type(obj).__name__}")
        if isinstance(obj, unreal.PaperFlipbookComponent):
            fb = obj.get_editor_property("source_flipbook")
            lines.append(f"  SourceFlipbook: {fb.get_path_name() if fb else 'None'}")
            lines.append(f"  Scale: {obj.get_editor_property('relative_scale3d')}")
            lines.append(f"  TranslucencySortPriority: {obj.get_editor_property('translucency_sort_priority')}")
        elif isinstance(obj, unreal.ProjectileMovementComponent):
            lines.append(f"  InitialSpeed: {obj.get_editor_property('initial_speed')}")
            lines.append(f"  MaxSpeed: {obj.get_editor_property('max_speed')}")
            lines.append(f"  RotationFollowsVelocity: {obj.get_editor_property('rotation_follows_velocity')}")
            lines.append(f"  InitialVelocityInLocalSpace: {obj.get_editor_property('initial_velocity_in_local_space')}")

# 查找所有 ProjectileFlight4 的 Flipbook
asset_reg = unreal.AssetRegistryHelpers.get_asset_registry()
filter = unreal.ARFilter(
    class_names=["PaperFlipbook"],
    package_paths=["/Game/P01"],
    recursive_paths=True
)
assets = asset_reg.get_assets(filter)
lines.append("\n=== Candidate Projectile Flipbooks ===")
for a in assets:
    p = str(a.package_name)
    if "Bullet" in p or "Projectile" in p:
        fb_obj = a.get_asset()
        fps = fb_obj.get_editor_property("frames_per_second")
        num_kf = fb_obj.get_num_key_frames()
        sp0 = fb_obj.get_sprite_at_frame(0)
        lines.append(f"FB: {p} | FPS={fps} | KF={num_kf} | Sprite0={sp0.get_name() if sp0 else 'None'}")

with open("/Users/cc/Desktop/GGBOM/xxxx/projectile_audit.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("AUDIT_PROJECTILE_WRITTEN")
