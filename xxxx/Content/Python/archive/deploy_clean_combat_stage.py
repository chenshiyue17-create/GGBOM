"""Safe map-only deployment: no Blueprint graph mutation."""
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
MAP = "/Game/GGBOM/Maps/MAP_GGBOM_Main"
LAYOUT = [
    ("/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker", "CombatWave_Zombie_01", (0, 0, 120)),
    ("/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker", "CombatWave_Zombie_02", (-115, 0, 250)),
    ("/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker", "CombatWave_Zombie_03", (115, 0, 315)),
    ("/Game/Blueprints/Characters/Enemies/BP_Enemy_MutantHound", "CombatWave_Hound_01", (-180, 0, 435)),
    ("/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord", "CombatWave_Boss", (0, 0, 590)),
]

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP)
removed = []
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    label = actor.get_actor_label()
    if label.startswith("CombatWave_") or label.startswith("Enemy_") or label == "Boss_Overlord_Live":
        removed.append(label)
        unreal.EditorLevelLibrary.destroy_actor(actor)
spawned = []
for path, label, xyz in LAYOUT:
    bp = unreal.load_asset(path)
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(bp.generated_class(), unreal.Vector(*xyz))
    actor.set_actor_label(label)
    spawned.append({"label": label, "class": bp.generated_class().get_name(), "location": xyz})
saved = unreal.EditorLoadingAndSavingUtils.save_map(world, MAP)
report = {"STAGE_DEPLOY_STATUS":"PASS" if saved and len(spawned) == len(LAYOUT) else "FAIL", "removed_legacy_enemy_actors":removed, "spawned":spawned, "saved":bool(saved)}
(ROOT/"output/stage_deploy_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(f"STAGE_DEPLOY_STATUS={report['STAGE_DEPLOY_STATUS']}")
if report["STAGE_DEPLOY_STATUS"] != "PASS": raise RuntimeError(report)
