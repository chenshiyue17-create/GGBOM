# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import unreal


PROJECT_ROOT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
MAP_PATH = "/Game/GGBOM/Maps/MAP_GGBOM_Main"
PLAYER_BP_PATH = "/Game/Blueprints/Player/BP_Player_Medic"
PLAYER_LABEL = "Player_Medic_Runtime"
REPORT_PATH = PROJECT_ROOT / "output" / "player_visibility_status.json"
HANDOFF_PATH = PROJECT_ROOT / "Docs" / "AI_HANDOFF_PLAYER_VISIBILITY.md"

ASSETS = unreal.EditorAssetLibrary
BPLIB = unreal.BlueprintEditorLibrary
SUBOBJECTS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)

FB_IDLE_DOWN = "/Game/P01/Imported/Content/Asset/Art/01_Player/01_Idle_Run/Dir_01_Down/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_01_Down_Sheet"
FB_IDLE_UP = "/Game/P01/Imported/Content/Asset/Art/01_Player/01_Idle_Run/Dir_05_Up/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_05_Up_Sheet"


def log(msg: str) -> None:
    unreal.log(f"[GGBOM-PlayerVisible] {msg}")


def set_prop(obj, prop: str, value) -> bool:
    try:
        obj.set_editor_property(prop, value)
        return True
    except Exception:
        return False


def make_rotator(pitch: float, yaw: float, roll: float) -> unreal.Rotator:
    r = unreal.Rotator()
    set_prop(r, "pitch", pitch)
    set_prop(r, "yaw", yaw)
    set_prop(r, "roll", roll)
    return r


def safe_label(actor) -> str:
    try:
        return actor.get_actor_label()
    except Exception:
        return actor.get_name()


def add_component(bp: unreal.Blueprint, name: str, cls: unreal.Class):
    handles = SUBOBJECTS.k2_gather_subobject_data_for_blueprint(bp)
    params = unreal.AddNewSubobjectParams()
    params.set_editor_property("parent_handle", handles[0])
    params.set_editor_property("new_class", cls)
    params.set_editor_property("blueprint_context", bp)
    handle, reason = SUBOBJECTS.add_new_subobject(params)
    if not unreal.SubobjectDataBlueprintFunctionLibrary.is_handle_valid(handle):
        raise RuntimeError(f"Component {name} failed: {reason}")
    SUBOBJECTS.rename_subobject(handle, unreal.Text(name))
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    return unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)


def get_or_add_component(bp, cdo, cls, name):
    comps = list(cdo.get_components_by_class(cls))
    if comps:
        return comps[0], False
    return add_component(bp, name, cls.static_class() if hasattr(cls, "static_class") else cls), True


def configure_player_blueprint() -> dict:
    result = {
        "bp_found": False,
        "flipbook_found": False,
        "flipbook_component_found": False,
        "flipbook_component_added": False,
        "camera_component_found": False,
        "camera_component_added": False,
        "collision_component_found": False,
        "collision_component_added": False,
        "compiled": False,
        "saved": False,
    }
    bp = unreal.load_asset(PLAYER_BP_PATH)
    result["bp_found"] = bool(bp)
    if not bp:
        return result

    cdo = unreal.get_default_object(bp.generated_class())
    set_prop(cdo, "auto_receive_input", unreal.AutoReceiveInput.PLAYER0)
    # GameMode will possess the spawned pawn. Do not force a placed pawn to steal
    # the view target unless the engine picks this pawn instance.
    set_prop(cdo, "auto_possess_player", unreal.AutoReceiveInput.DISABLED)

    flipbook = unreal.load_asset(FB_IDLE_DOWN) or unreal.load_asset(FB_IDLE_UP)
    result["flipbook_found"] = bool(flipbook)

    fb_components = list(cdo.get_components_by_class(unreal.PaperFlipbookComponent))
    if fb_components:
        fb_comp = fb_components[0]
    else:
        fb_comp = add_component(bp, "VisibleFlipbook", unreal.PaperFlipbookComponent.static_class())
        result["flipbook_component_added"] = True
    result["flipbook_component_found"] = bool(fb_comp)

    if fb_comp:
        if flipbook:
            set_prop(fb_comp, "source_flipbook", flipbook)
        set_prop(fb_comp, "visible", True)
        set_prop(fb_comp, "hidden_in_game", False)
        set_prop(fb_comp, "translucency_sort_priority", 2000)
        set_prop(fb_comp, "relative_location", unreal.Vector(0.0, 0.0, 0.0))
        set_prop(fb_comp, "relative_rotation", make_rotator(0.0, 0.0, 0.0))
        mat = unreal.load_asset("/Paper2D/TranslucentUnlitSpriteMaterial")
        if mat:
            try:
                fb_comp.set_material(0, mat)
            except Exception:
                pass

    col_components = list(cdo.get_components_by_class(unreal.BoxComponent))
    if col_components:
        col = col_components[0]
    else:
        col = add_component(bp, "PlayerCollision", unreal.BoxComponent.static_class())
        result["collision_component_added"] = True
    result["collision_component_found"] = bool(col)
    if col:
        set_prop(col, "box_extent", unreal.Vector(36.0, 24.0, 60.0))
        try:
            col.set_collision_profile_name("Pawn")
        except Exception:
            pass

    cam_components = list(cdo.get_components_by_class(unreal.CameraComponent))
    if cam_components:
        cam = cam_components[0]
    else:
        cam = add_component(bp, "RuntimeOrthographicCamera", unreal.CameraComponent.static_class())
        result["camera_component_added"] = True
    result["camera_component_found"] = bool(cam)
    if cam:
        # Pawn spawn point is near Z=-560. This relative offset recreates the
        # verified world camera at roughly (0,-1000,0) while still following the
        # possessed player enough for UE to render through it.
        set_prop(cam, "relative_location", unreal.Vector(0.0, -980.0, 560.0))
        set_prop(cam, "relative_rotation", make_rotator(0.0, 90.0, 0.0))
        set_prop(cam, "projection_mode", unreal.CameraProjectionMode.ORTHOGRAPHIC)
        set_prop(cam, "ortho_width", 941.0)
        set_prop(cam, "aspect_ratio", 941.0 / 1672.0)
        set_prop(cam, "b_constrain_aspect_ratio", True)
        set_prop(cam, "auto_activate", True)
        set_prop(cam, "auto_calculate_ortho_planes", False)
        set_prop(cam, "ortho_near_clip_plane", -10000.0)
        set_prop(cam, "ortho_far_clip_plane", 10000.0)

    try:
        BPLIB.compile_blueprint(bp)
        result["compiled"] = True
    except Exception as exc:
        result["compile_error"] = str(exc)
    result["saved"] = bool(ASSETS.save_loaded_asset(bp, only_if_is_dirty=False))
    return result


def ensure_placed_player() -> dict:
    result = {"placed": False, "spawned": False, "label": PLAYER_LABEL, "location": [0.0, -20.0, -560.0], "visible_component": False}
    bp = unreal.load_asset(PLAYER_BP_PATH)
    if not bp:
        result["error"] = "player blueprint missing"
        return result
    player_class = bp.generated_class()
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    player = None
    for actor in actors:
        if safe_label(actor) == PLAYER_LABEL:
            player = actor
            break
    if not player:
        player = unreal.EditorLevelLibrary.spawn_actor_from_object(player_class, unreal.Vector(0.0, -20.0, -560.0), make_rotator(0.0, 0.0, 0.0))
        result["spawned"] = bool(player)
    if player:
        result["placed"] = True
        player.set_actor_label(PLAYER_LABEL)
        try:
            player.set_actor_location(unreal.Vector(0.0, -20.0, -560.0), False, True)
        except Exception:
            player.set_actor_location(unreal.Vector(0.0, -20.0, -560.0), False)
        try:
            player.set_actor_rotation(make_rotator(0.0, 0.0, 0.0), False)
        except Exception:
            pass
        player.set_actor_scale3d(unreal.Vector(1.0, 1.0, 1.0))
        set_prop(player, "auto_receive_input", unreal.AutoReceiveInput.DISABLED)
        set_prop(player, "auto_possess_player", unreal.AutoReceiveInput.DISABLED)
        try:
            player.set_editor_property("folder_path", "03_Player")
        except Exception:
            pass
        fb = player.get_component_by_class(unreal.PaperFlipbookComponent)
        if fb:
            set_prop(fb, "visible", True)
            set_prop(fb, "hidden_in_game", False)
            set_prop(fb, "translucency_sort_priority", 2000)
            result["visible_component"] = True

    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if safe_label(actor) == "PlayerStart":
            try:
                actor.set_actor_location(unreal.Vector(0.0, -20.0, -560.0), False, True)
            except Exception:
                actor.set_actor_location(unreal.Vector(0.0, -20.0, -560.0), False)
            break
    return result


def main() -> None:
    log("Fix player visibility and placement")
    unreal.EditorLevelLibrary.load_level(MAP_PATH)
    world = unreal.EditorLevelLibrary.get_editor_world()
    bp_result = configure_player_blueprint()
    placed_result = ensure_placed_player()
    map_saved = False
    try:
        map_saved = bool(unreal.EditorLoadingAndSavingUtils.save_map(world, MAP_PATH))
    except Exception:
        map_saved = bool(ASSETS.save_asset(MAP_PATH, only_if_is_dirty=False))
    ASSETS.save_directory("/Game", only_if_is_dirty=False, recursive=True)
    status = "PASS" if bp_result.get("compiled") and bp_result.get("flipbook_found") and placed_result.get("placed") and map_saved else "FAIL"
    report = {
        "time": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "pure_blueprint": True,
        "map": MAP_PATH,
        "player_blueprint": PLAYER_BP_PATH,
        "player_label": PLAYER_LABEL,
        "blueprint": bp_result,
        "placed_player": placed_result,
        "map_saved": map_saved,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    HANDOFF_PATH.parent.mkdir(parents=True, exist_ok=True)
    HANDOFF_PATH.write_text(
        "\n".join(
            [
                "# GGBOM Player Visibility Handoff",
                "",
                f"- Time: {report['time']}",
                f"- Status: {status}",
                f"- Map: {MAP_PATH}",
                f"- Player Blueprint: {PLAYER_BP_PATH}",
                f"- Runtime Player Actor: {PLAYER_LABEL}",
                "- The player must be visible near bottom center at Location=(0,-20,-560).",
                "- Keep PaperFlipbookComponent visible, not hidden in game, sort priority 2000.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    log(f"PLAYER_VISIBILITY_STATUS={status}")
    log(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
