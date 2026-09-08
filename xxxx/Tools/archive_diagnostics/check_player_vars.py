# -*- coding: utf-8 -*-
import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/player_var_defaults.txt"

bp = unreal.EditorAssetLibrary.load_asset("/Game/Blueprints/Player/BP_Player_Medic")
cdo = unreal.get_default_object(bp.generated_class())

lines = []
for prop in ["FireCooldown", "FireCooldownRemaining", "MoveSpeed", "FacingDirection", "ShotDirection"]:
    if hasattr(cdo, prop):
        lines.append(f"{prop} = {getattr(cdo, prop)}")
    else:
        lines.append(f"{prop} NOT FOUND ON CDO")

OUT.write_text("\n".join(lines), encoding="utf-8")
print("CHECK_PLAYER_VARS_DONE")
