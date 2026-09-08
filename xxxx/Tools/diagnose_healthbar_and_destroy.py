# -*- coding: utf-8 -*-
import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/diagnose_healthbar.txt"
OUT.parent.mkdir(parents=True, exist_ok=True)

LEVEL_SUBSYS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUBSYS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LEVEL_SUBSYS.load_level("/Game/GGBOM/Maps/MAP_GGBOM_Main")

actors = ACTOR_SUBSYS.get_all_level_actors()
lines = ["=== MAP_GGBOM_Main ACTORS DIAGNOSIS ==="]
for a in actors:
    lbl = a.get_actor_label()
    if any(k in lbl for k in ["Boss", "Bar", "Zombie", "Hound", "Presenter"]):
        loc = a.get_actor_location()
        scale = a.get_actor_scale3d()
        parent = a.get_attach_parent_actor()
        parent_lbl = parent.get_actor_label() if parent else "None"
        rc = a.get_editor_property("root_component")
        rel_loc = rc.get_editor_property("relative_location") if rc else "N/A"
        tags = [str(t) for t in a.tags]
        lines.append(f"[{lbl}] Loc: {loc}, RelLoc: {rel_loc}, Scale: {scale}, Parent: {parent_lbl}, Tags: {tags}")

lines.append("=== DIAGNOSIS COMPLETE ===")
OUT.write_text("\n".join(lines), encoding="utf-8")
unreal.log("\n".join(lines))
