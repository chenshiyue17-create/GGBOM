# -*- coding: utf-8 -*-
import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/existing_hud_comps.txt"

bp_path = "/Game/GGBOM/Blueprints/BP_GGBOM_MasterHUD"
bp = unreal.EditorAssetLibrary.load_asset(bp_path)
lines = []

scs = bp.simple_construction_script
if scs:
    all_nodes = scs.get_all_nodes()
    lines.append(f"SCS Nodes ({len(all_nodes)}):")
    for n in all_nodes:
        c = n.component_template
        cname = n.get_variable_name()
        cclass = c.get_class().get_name() if c else "None"
        sp = "None"
        if hasattr(c, "source_sprite") and c.source_sprite:
            sp = c.source_sprite.get_name()
        lines.append(f"  {cname} ({cclass}) -> Sprite: {sp}")

OUT.write_text("\n".join(lines), encoding="utf-8")
print("GET_EXISTING_HUD_COMPS_DONE")
