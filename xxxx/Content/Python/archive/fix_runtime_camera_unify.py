# -*- coding: utf-8 -*-
"""
Fix Standalone/PIE runtime camera mismatch for GGBOM.

The editor viewport can look correct while Standalone uses the default spawned
camera. This script makes the placed orthographic camera the Player0 view and
keeps the pure Blueprint project boundary.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import unreal


PROJECT_ROOT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
MAP_PATH = "/Game/GGBOM/Maps/MAP_GGBOM_Main"
GAMEMODE_PATH = "/Game/GGBOM/Blueprints/BP_GGBOM_GameMode"
PAWN_PATH = "/Game/Blueprints/Player/BP_Player_Medic"
REPORT_PATH = PROJECT_ROOT / "output" / "runtime_camera_unify_status.json"
HANDOFF_PATH = PROJECT_ROOT / "Docs" / "AI_HANDOFF_RUNTIME_CAMERA.md"

ASSETS = unreal.EditorAssetLibrary
BPLIB = unreal.BlueprintEditorLibrary

MAP_W = 941.0
MAP_H = 1672.0
CAMERA_LABEL = "Master_Orthographic_Camera"


def log(message: str) -> None:
    unreal.log(f"[GGBOM-RuntimeCamera] {message}")


def safe_label(actor: unreal.Actor) -> str:
    try:
        return actor.get_actor_label()
    except Exception:
        return actor.get_name()


def set_prop(obj, prop: str, value) -> bool:
    try:
        obj.set_editor_property(prop, value)
        return True
    except Exception:
        return False


def set_actor_transform(actor: unreal.Actor, loc: unreal.Vector, rot: unreal.Rotator) -> dict:
    result = {"location": False, "rotation": False}
    try:
        actor.set_actor_location(loc, False, True)
        result["location"] = True
    except Exception:
        try:
            actor.set_actor_location(loc, False)
            result["location"] = True
        except Exception:
            pass
    try:
        actor.set_actor_rotation(rot, False)
        result["rotation"] = True
    except Exception:
        try:
            actor.set_actor_rotation(rot)
            result["rotation"] = True
        except Exception:
            pass
    return result


def make_rotator(pitch: float, yaw: float, roll: float) -> unreal.Rotator:
    """Build a Rotator with verified field values across UE Python constructor variants."""
    rot = unreal.Rotator()
    set_prop(rot, "pitch", pitch)
    set_prop(rot, "yaw", yaw)
    set_prop(rot, "roll", roll)
    return rot


def find_or_create_camera() -> unreal.CameraActor:
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    for actor in actors:
        if isinstance(actor, unreal.CameraActor) and safe_label(actor) == CAMERA_LABEL:
            return actor
    camera = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.CameraActor,
        unreal.Vector(0.0, -1000.0, 0.0),
        make_rotator(0.0, 90.0, 0.0),
    )
    camera.set_actor_label(CAMERA_LABEL)
    return camera


def configure_camera(camera: unreal.CameraActor) -> dict:
    # Paper2D sprites in this project live on the X/Z plane. Camera looks from
    # negative Y toward +Y, so the 2D map is face-on in game runtime.
    transform_ok = set_actor_transform(
        camera,
        unreal.Vector(0.0, -1000.0, 0.0),
        make_rotator(0.0, 90.0, 0.0),
    )

    auto_activate_ok = set_prop(camera, "auto_activate_for_player", unreal.AutoReceiveInput.PLAYER0)

    comp = camera.get_component_by_class(unreal.CameraComponent)
    camera_props = {}
    if comp:
        camera_props["projection_mode"] = set_prop(comp, "projection_mode", unreal.CameraProjectionMode.ORTHOGRAPHIC)
        camera_props["ortho_width"] = set_prop(comp, "ortho_width", MAP_W)
        camera_props["aspect_ratio"] = set_prop(comp, "aspect_ratio", MAP_W / MAP_H)
        camera_props["constrain_aspect_ratio"] = set_prop(comp, "b_constrain_aspect_ratio", True) or set_prop(comp, "constrain_aspect_ratio", True)
        camera_props["use_pawn_control_rotation"] = set_prop(comp, "use_pawn_control_rotation", False)
        camera_props["auto_calculate_ortho_planes"] = set_prop(comp, "auto_calculate_ortho_planes", False)
        camera_props["ortho_near_clip_plane"] = set_prop(comp, "ortho_near_clip_plane", -10000.0)
        camera_props["ortho_far_clip_plane"] = set_prop(comp, "ortho_far_clip_plane", 10000.0)
    else:
        camera_props["camera_component_found"] = False

    try:
        camera.set_editor_property("folder_path", "01_Camera")
    except Exception:
        pass

    return {
        "camera_label": safe_label(camera),
        "transform": transform_ok,
        "auto_activate_player0": auto_activate_ok,
        "camera_props": camera_props,
        "location": [camera.get_actor_location().x, camera.get_actor_location().y, camera.get_actor_location().z],
        "rotation": [
            camera.get_actor_rotation().pitch,
            camera.get_actor_rotation().yaw,
            camera.get_actor_rotation().roll,
        ],
    }


def configure_game_mode() -> dict:
    result = {"game_mode_found": False, "pawn_found": False, "default_pawn_set": False, "compiled": False, "saved": False}
    game_mode = unreal.load_asset(GAMEMODE_PATH)
    pawn = unreal.load_asset(PAWN_PATH)
    result["game_mode_found"] = bool(game_mode)
    result["pawn_found"] = bool(pawn)
    if not game_mode or not pawn:
        return result

    gm_cdo = unreal.get_default_object(game_mode.generated_class())
    pawn_class = pawn.generated_class()
    result["default_pawn_set"] = set_prop(gm_cdo, "default_pawn_class", pawn_class)

    try:
        BPLIB.compile_blueprint(game_mode)
        result["compiled"] = True
    except Exception as exc:
        result["compile_error"] = str(exc)

    result["saved"] = ASSETS.save_loaded_asset(game_mode, only_if_is_dirty=False)
    return result


def configure_pawn() -> dict:
    result = {"pawn_found": False, "auto_receive_input": False, "auto_possess_player": False, "compiled": False, "saved": False}
    pawn = unreal.load_asset(PAWN_PATH)
    result["pawn_found"] = bool(pawn)
    if not pawn:
        return result
    cdo = unreal.get_default_object(pawn.generated_class())
    result["auto_receive_input"] = set_prop(cdo, "auto_receive_input", unreal.AutoReceiveInput.PLAYER0)
    # Keep spawned GameMode pawn valid. If this placed/spawned pawn exists, Player0 still receives input.
    result["auto_possess_player"] = set_prop(cdo, "auto_possess_player", unreal.AutoReceiveInput.PLAYER0)
    try:
        BPLIB.compile_blueprint(pawn)
        result["compiled"] = True
    except Exception as exc:
        result["compile_error"] = str(exc)
    result["saved"] = ASSETS.save_loaded_asset(pawn, only_if_is_dirty=False)
    return result


def configure_world_settings() -> dict:
    result = {"world_settings_found": False, "game_mode_override_set": False}
    world = unreal.EditorLevelLibrary.get_editor_world()
    ws = world.get_world_settings() if world else None
    result["world_settings_found"] = bool(ws)
    game_mode = unreal.load_asset(GAMEMODE_PATH)
    if ws and game_mode:
        result["game_mode_override_set"] = set_prop(ws, "default_game_mode", game_mode.generated_class())
    return result


def write_handoff(report: dict) -> None:
    HANDOFF_PATH.parent.mkdir(parents=True, exist_ok=True)
    HANDOFF_PATH.write_text(
        "\n".join(
            [
                "# GGBOM Runtime Camera Handoff",
                "",
                f"- Time: {report['time']}",
                f"- Status: {report['status']}",
                f"- Map: {MAP_PATH}",
                f"- RuntimeCamera: {CAMERA_LABEL}",
                "- Camera plane rule: sprites are viewed face-on from negative Y toward +Y.",
                "- Camera transform target: Location=(0,-1000,0), Rotation=(Pitch=0,Yaw=90,Roll=0).",
                f"- OrthoWidth: {MAP_W}",
                f"- PortraitAspect: {MAP_W / MAP_H:.6f}",
                "- Standalone should be launched with `-game -windowed -ResX=360 -ResY=640 -ForceRes`.",
                "- Do not use Simulate as visual acceptance; use Standalone/PIE with this camera.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    log("Load main map and unify runtime camera")
    unreal.EditorLevelLibrary.load_level(MAP_PATH)
    world = unreal.EditorLevelLibrary.get_editor_world()

    camera = find_or_create_camera()
    camera_result = configure_camera(camera)
    pawn_result = configure_pawn()
    game_mode_result = configure_game_mode()
    world_settings_result = configure_world_settings()

    map_saved = False
    try:
        map_saved = bool(unreal.EditorLoadingAndSavingUtils.save_map(world, MAP_PATH))
    except Exception:
        map_saved = bool(ASSETS.save_asset(MAP_PATH, only_if_is_dirty=False))

    ASSETS.save_directory("/Game/GGBOM", only_if_is_dirty=False, recursive=True)

    status = "PASS"
    if not (
        map_saved
        and camera_result["auto_activate_player0"]
        and all(camera_result["transform"].values())
        and game_mode_result["game_mode_found"]
        and pawn_result["pawn_found"]
    ):
        status = "PARTIAL"

    report = {
        "time": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "pure_blueprint": True,
        "map": MAP_PATH,
        "camera": camera_result,
        "pawn": pawn_result,
        "game_mode": game_mode_result,
        "world_settings": world_settings_result,
        "map_saved": map_saved,
        "recommended_test_command": "Tools/launch_lightweight_game.sh /Game/GGBOM/Maps/MAP_GGBOM_Main",
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_handoff(report)

    log(f"RUNTIME_CAMERA_UNIFY_STATUS={status}")
    log(f"CAMERA={camera_result}")
    log(f"GAMEMODE={game_mode_result}")
    log(f"PAWN={pawn_result}")
    log(f"MAP_SAVED={map_saved}")


if __name__ == "__main__":
    main()
