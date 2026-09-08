"""Map-only repair for the standalone black screen.

Keeps the existing camera actor as the sole Player0 orthographic view.  No
Blueprint graph is edited by this script.
"""
import json
from pathlib import Path
import unreal

MAP = "/Game/GGBOM/Maps/MAP_GGBOM_Main"
root = Path(unreal.Paths.project_dir()).resolve()
world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
cameras = [a for a in unreal.EditorLevelLibrary.get_all_level_actors() if isinstance(a, unreal.CameraActor)]
if not cameras:
    raise RuntimeError("No CameraActor in main map")

# The player blueprint selects the first CameraActor at BeginPlay, so repair
# that actor rather than adding another competing camera.
camera = cameras[0]
camera.set_actor_label("PortraitCamera_9x16")
camera.set_actor_location(unreal.Vector(0.0, -1000.0, 0.0), False, False)
camera.set_actor_rotation(unreal.Rotator(0.0, 90.0, 0.0), False)
camera.set_editor_property("auto_activate_for_player", unreal.AutoReceiveInput.PLAYER0)
component = camera.get_component_by_class(unreal.CameraComponent)
if not component:
    raise RuntimeError("CameraActor has no CameraComponent")
component.set_editor_property("projection_mode", unreal.CameraProjectionMode.ORTHOGRAPHIC)
component.set_editor_property("ortho_width", 941.0)
component.set_editor_property("aspect_ratio", 941.0 / 1672.0)
component.set_editor_property("constrain_aspect_ratio", True)
component.set_editor_property("use_pawn_control_rotation", False)
component.set_editor_property("auto_calculate_ortho_planes", False)
component.set_editor_property("ortho_near_clip_plane", -10000.0)
component.set_editor_property("ortho_far_clip_plane", 10000.0)

saved = bool(unreal.EditorLoadingAndSavingUtils.save_map(world, MAP))
report = {
    "BLACK_SCREEN_CAMERA_FIX": "PASS" if saved else "FAIL",
    "camera": camera.get_actor_label(),
    "location": [0, -1000, 0],
    "rotation": [0, 90, 0],
    "projection": "ORTHOGRAPHIC",
    "ortho_width": 941.0,
    "saved": saved,
}
(root / "output" / "black_runtime_camera_fix.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(f"BLACK_SCREEN_CAMERA_FIX={report['BLACK_SCREEN_CAMERA_FIX']}")
if not saved:
    raise RuntimeError(report)
