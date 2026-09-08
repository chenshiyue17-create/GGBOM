# -*- coding: utf-8 -*-
import unreal
import sys
from pathlib import Path

ROOT = str(Path(unreal.Paths.project_dir()).resolve())
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

def log(msg):
    unreal.log(f"[TRACE_ALL] {msg}")
    print(f"[TRACE_ALL] {msg}", flush=True)

try:
    log("=== TEST BOSS ===")
    import Tools.build_complete_combat_ai_flocking as mod
    mod.setup_boss()
    log("=== BOSS OK ===")
except Exception as e:
    log(f"BOSS FAILED: {e}")
    sys.exit(1)

try:
    log("=== TEST HOUND ===")
    import Tools.build_complete_combat_ai_flocking as mod
    mod.setup_hound()
    log("=== HOUND OK ===")
except Exception as e:
    log(f"HOUND FAILED: {e}")
    sys.exit(1)

try:
    log("=== TEST ZOMBIE ===")
    import Tools.build_complete_combat_ai_flocking as mod
    mod.setup_zombie()
    log("=== ZOMBIE OK ===")
except Exception as e:
    log(f"ZOMBIE FAILED: {e}")
    sys.exit(1)

log("ALL 3 PASSED!")
