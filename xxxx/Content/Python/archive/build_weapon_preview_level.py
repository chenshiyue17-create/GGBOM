# -*- coding: utf-8 -*-
"""Build dedicated Weapon Preview Level /Game/Preview/L_Preview_Weapon"""
import unreal

world_subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
level_editor_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
editor_asset_lib = unreal.EditorAssetLibrary

map_package = "/Game/Preview/L_Preview_Weapon"
preview_dir = "/Game/Preview"

# Ensure directory exists
if not editor_asset_lib.does_directory_exist(preview_dir):
    editor_asset_lib.make_directory(preview_dir)

# Create new empty level
level_editor_subsystem.new_level(map_package)
world = world_subsystem.get_editor_world()

print(f"Created new level: {map_package}")

# 1. Spawn Orthographic Camera
cam_class = unreal.EditorPlatformLibrary.load_class("/Script/Engine.CameraActor") if hasattr(unreal, "EditorPlatformLibrary") else unreal.CameraActor
cam_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(0, -1000, 0), unreal.Rotator(0, 90, 0))
if cam_actor:
    cam_actor.set_actor_label("Preview_Orthographic_Camera")
    cam_comp = cam_actor.camera_component
    cam_comp.projection_mode = unreal.CameraProjectionMode.ORTHOGRAPHIC
    cam_comp.ortho_width = 941.0
    cam_comp.aspect_ratio = 0.562799
    cam_comp.constrain_aspect_ratio = True

# 2. Spawn Player Dummy (Visual reference)
player_dummy = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PaperSpriteActor, unreal.Vector(0, 0, -200), unreal.Rotator(0, 0, 0))
if player_dummy:
    player_dummy.set_actor_label("Player_Hold_Dummy")
    sprite_comp = player_dummy.render_component
    sprite_asset = editor_asset_lib.load_asset("/Game/GGBOM/Art/Sprites/SP_Player.SP_Player")
    if sprite_asset:
        sprite_comp.set_sprite(sprite_asset)
    player_dummy.set_actor_scale3d(unreal.Vector(0.5, 0.5, 0.5))

# 3. Spawn Target Dummy
target_dummy = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PaperSpriteActor, unreal.Vector(0, 0, 200), unreal.Rotator(0, 0, 0))
if target_dummy:
    target_dummy.set_actor_label("Target_Impact_Dummy")
    sprite_comp = target_dummy.render_component
    sprite_asset = editor_asset_lib.load_asset("/Game/GGBOM/Art/Sprites/SP_ZombieBrute.SP_ZombieBrute")
    if sprite_asset:
        sprite_comp.set_sprite(sprite_asset)
    target_dummy.set_actor_scale3d(unreal.Vector(0.5, 0.5, 0.5))

# 4. Spawn Background Grid / Ground
ground_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PaperSpriteActor, unreal.Vector(0, 80, 0), unreal.Rotator(0, 0, 0))
if ground_actor:
    ground_actor.set_actor_label("Preview_Ground_Layer")
    sprite_comp = ground_actor.render_component
    sprite_asset = editor_asset_lib.load_asset("/Game/GGBOM/Art/Sprites/SP_Map_Ground.SP_Map_Ground")
    if sprite_asset:
        sprite_comp.set_sprite(sprite_asset)

# Save level
level_editor_subsystem.save_current_level()
print("Saved /Game/Preview/L_Preview_Weapon successfully.")
