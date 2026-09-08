# -*- coding: utf-8 -*-
import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/verify_zombie_clean.txt"

bp_path = "/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker"
bp = unreal.EditorAssetLibrary.load_asset(bp_path)
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
saved = unreal.EditorAssetLibrary.save_loaded_asset(bp)
OUT.write_text(f"ZOMBIE_CLEAN_OK: {saved}\n", encoding="utf-8")
print(f"ZOMBIE_CLEAN_OK: {saved}")
