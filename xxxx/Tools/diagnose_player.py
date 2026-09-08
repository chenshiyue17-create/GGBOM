# -*- coding: utf-8 -*-
import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/diagnose_player_setup.txt"

LEVEL_SUBSYS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUBSYS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ASSETS = unreal.EditorAssetLibrary

LEVEL_SUBSYS.load_level("/Game/GGBOM/Maps/MAP_GGBOM_Main")
world = unreal.EditorLevelLibrary.get_editor_world()

actors = ACTOR_SUBSYS.get_all_level_actors()
lines = ["=== PLAYER & GAMEMODE AUDIT ==="]

# 1. 关卡内所有 Player / Start / Camera / Controller Actor
for a in actors:
    lbl = a.get_actor_label()
    cls_name = a.get_class().get_name()
    if any(k in lbl.lower() or k in cls_name.lower() for k in ["player", "pawn", "start", "camera", "gamemode"]):
        loc = a.get_actor_location()
        lines.append(f"Actor: [{lbl}] Class: {cls_name}, Loc: {loc}")

# 2. WorldSettings
ws = world.get_world_settings()
gm_override = ws.get_editor_property("game_mode_override")
lines.append(f"WorldSettings GameModeOverride: {gm_override.get_path_name() if gm_override else 'None'}")

# 3. DefaultEngine.ini 的 GameMode
ini_path = ROOT / "Config/DefaultEngine.ini"
lines.append(f"DefaultEngine.ini exists: {ini_path.exists()}")

OUT.write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
