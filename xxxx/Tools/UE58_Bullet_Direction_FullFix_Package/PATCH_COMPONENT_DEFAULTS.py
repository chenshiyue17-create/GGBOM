# -*- coding: utf-8 -*-
"""
UE5.8 SAFE COMPONENT DEFAULT PATCH
==================================
This script performs only non-destructive default-component fixes on:
    /Game/Blueprints/Combat/Projectiles/BP_ProjectileBase

It intentionally DOES NOT claim to complete the full direction-system rewrite.

Full fix still requires:
    - LastAimDirection in BP_Player_Medic
    - unified Fire path
    - InitializeProjectile(Direction, Speed)
    - world Velocity assignment
    - BulletFlipbook-only visual rotation

Use IDE_AGENT_TASK.md for the complete implementation.
"""

import unreal

PROJ_BP_PATH = "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase"

ASSETS = unreal.EditorAssetLibrary
BPLIB = unreal.BlueprintEditorLibrary
SUBOBJECTS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)


def _get_subobject(bp, wanted_name: str):
    handles = SUBOBJECTS.k2_gather_subobject_data_for_blueprint(bp)
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = str(
            unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data)
        )
        if vname == wanted_name:
            return unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(
                data, bp
            )
    return None


def patch_projectile_defaults():
    bp = unreal.load_asset(PROJ_BP_PATH)
    if not bp:
        raise RuntimeError(f"Projectile Blueprint not found: {PROJ_BP_PATH}")

    bullet = _get_subobject(bp, "BulletFlipbook")
    movement = _get_subobject(bp, "ProjectileMovement")

    if not bullet:
        raise RuntimeError("BulletFlipbook component not found.")
    if not movement:
        raise RuntimeError("ProjectileMovement component not found.")

    # Visual only. Collision is deliberately not scaled here.
    bullet.set_editor_property(
        "relative_scale3d",
        unreal.Vector(0.03, 0.03, 0.03)
    )
    bullet.set_editor_property("translucency_sort_priority", 2800)
    bullet.set_editor_property("visible", True)
    bullet.set_editor_property("hidden_in_game", False)

    # Trajectory must NOT start from a hard-coded +X velocity.
    movement.set_editor_property("initial_speed", 600.0)
    movement.set_editor_property("max_speed", 600.0)
    movement.set_editor_property("projectile_gravity_scale", 0.0)
    movement.set_editor_property("velocity", unreal.Vector(0.0, 0.0, 0.0))

    # These properties exist on UE ProjectileMovementComponent in UE5.x.
    # Guard them so the patch does not abort if reflection naming differs.
    for prop_name, value in (
        ("initial_velocity_in_local_space", False),
        ("rotation_follows_velocity", False),
    ):
        try:
            movement.set_editor_property(prop_name, value)
        except Exception as exc:
            unreal.log_warning(
                f"[BulletFix] Could not set {prop_name}: {exc}. "
                "Set it manually in BP_ProjectileBase."
            )

    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)

    unreal.log(
        "[BulletFix] Safe projectile defaults patched. "
        "FULL BLUEPRINT DIRECTION REWRITE IS STILL REQUIRED."
    )


if __name__ == "__main__":
    patch_projectile_defaults()
