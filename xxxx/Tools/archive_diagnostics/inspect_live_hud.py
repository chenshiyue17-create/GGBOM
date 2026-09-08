# -*- coding: utf-8 -*-
import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/live_hud_comps.txt"

map_path = "/Game/GGBOM/Maps/MAP_GGBOM_Main"
unreal.EditorLevelLibrary.load_level(map_path)

actors = unreal.EditorLevelLibrary.get_all_level_actors()
hud_actor = None
for a in actors:
    if "MasterHUD" in a.get_name() or "HUD" in a.get_name():
        hud_actor = a
        break

lines = [f"Found HUD Actor: {hud_actor.get_name() if hud_actor else 'None'}"]
if hud_actor:
    comps = hud_actor.get_components_by_class(unreal.PaperSpriteComponent)
    lines.append(f"Sprite Components ({len(comps)}):")
    for c in comps:
        sp_name = c.source_sprite.get_name() if c.source_sprite else "None"
        loc = c.get_editor_property("relative_location")
        lines.append(f"  Comp: {c.get_name()} | Sprite: {sp_name} | Pos: ({loc.x}, {loc.y}, {loc.z})")

OUT.write_text("\n".join(lines), encoding="utf-8")
print("INSPECT_LIVE_HUD_DONE")
