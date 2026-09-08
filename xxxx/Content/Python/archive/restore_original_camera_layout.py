"""Restore the approved pre-audit stage camera and placed-sprite transforms."""
import json
from pathlib import Path
import unreal

MAP = "/Game/GGBOM/Maps/MAP_GGBOM_Main"
root = Path(unreal.Paths.project_dir()).resolve()
world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    if isinstance(actor, unreal.CameraActor) and actor.get_actor_label() == "PortraitCamera_9x16":
        actor.set_actor_location(unreal.Vector(0.0, -600.0, 0.0), False, False)
        actor.set_actor_rotation(unreal.Rotator(0.0, 90.0, 0.0), False)
    elif isinstance(actor, unreal.PaperSpriteActor):
        actor.set_actor_rotation(unreal.Rotator(0.0, 0.0, 0.0), False)
saved = bool(unreal.EditorLoadingAndSavingUtils.save_map(world, MAP))
report={"ORIGINAL_CAMERA_LAYOUT_RESTORED":"PASS" if saved else "FAIL","saved":saved}
(root/"output"/"original_camera_layout_restored.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(f"ORIGINAL_CAMERA_LAYOUT_RESTORED={report['ORIGINAL_CAMERA_LAYOUT_RESTORED']}")
if not saved: raise RuntimeError(report)
