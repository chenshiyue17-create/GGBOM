"""Face all placed Paper2D stage sprites toward the portrait runtime camera.

PaperSprite's native plane is XY.  This level is played and viewed on X/Z, so
the placed stage sprites need a 90 degree pitch to face the camera travelling
along the Y axis.  Blueprint assets are deliberately not modified.
"""
import json
from pathlib import Path
import unreal

MAP = "/Game/GGBOM/Maps/MAP_GGBOM_Main"
root = Path(unreal.Paths.project_dir()).resolve()
world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
changed = []
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    if isinstance(actor, unreal.PaperSpriteActor):
        actor.set_actor_rotation(unreal.Rotator(90.0, 0.0, 0.0), False)
        changed.append(actor.get_actor_label())
saved = bool(unreal.EditorLoadingAndSavingUtils.save_map(world, MAP))
report = {
    "PAPER2D_STAGE_ORIENTATION": "PASS" if saved and changed else "FAIL",
    "plane": "XZ",
    "camera_axis": "+Y",
    "rotated_actor_count": len(changed),
    "actors": changed,
    "saved": saved,
}
(root / "output" / "paper2d_stage_orientation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"PAPER2D_STAGE_ORIENTATION={report['PAPER2D_STAGE_ORIENTATION']} count={len(changed)}")
if report["PAPER2D_STAGE_ORIENTATION"] != "PASS":
    raise RuntimeError(report)
