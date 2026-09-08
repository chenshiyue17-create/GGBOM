# -*- coding: utf-8 -*-
import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/projectile_comps.txt"

bp_path = "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase"
bp = unreal.EditorAssetLibrary.load_asset(bp_path)
cdo = unreal.get_default_object(bp.generated_class())

lines = [f"Projectile CDO: {cdo.get_name() if cdo else 'None'}"]
if cdo:
    for c in cdo.get_components_by_class(unreal.ActorComponent):
        lines.append(f"  Component: {c.get_name()} ({c.get_class().get_name()})")
        if isinstance(c, unreal.ProjectileMovementComponent):
            lines.append(f"    Speed: {c.initial_speed}, MaxSpeed: {c.max_speed}, Gravity: {c.projectile_gravity_scale}, Velocity: {c.velocity}")
        elif isinstance(c, unreal.PaperSpriteComponent):
            sp = c.source_sprite.get_name() if c.source_sprite else "None"
            lines.append(f"    Sprite: {sp}, Visible: {c.get_editor_property('visible')}, HiddenInGame: {c.get_editor_property('hidden_in_game')}")

OUT.write_text("\n".join(lines), encoding="utf-8")
print("PROJ_COMPS_DONE")
