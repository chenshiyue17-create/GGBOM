#!/usr/bin/env python3
"""Capture actual asset bytes. Offline inventory is NOT a Blueprint structural export."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from ggbom.config_io import atomic_json
from ggbom.paths import REPO_ROOT, PROJECT_ROOT, REPORT_DIR

TARGETS = ["/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase",
           "/Game/Blueprints/Projectiles/BP_Projectile_Base", "/Game/Blueprints/Player/BP_Player_Medic",
           "/Game/Blueprints/Core/Components/BPC_WeaponInventory",
           "/Game/GGBOM/Blueprints/Components/BPC_WeaponInventory", "/Game/GGBOM/UI/WBP_GGBOM_CombatHUD"]


def capture(project=PROJECT_ROOT):
    result = []
    for asset_path in TARGETS:
        path = Path(project) / "Content" / (asset_path.removeprefix("/Game/") + ".uasset")
        result.append({"asset_path": asset_path, "exists": path.is_file(),
                       "sha256": hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None})
    try:
        commit = subprocess.check_output(["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        commit = None
    return {"schema_version": 1, "kind": "ASSET_BINARY_INVENTORY", "commit": commit,
            "assets": result, "structure_status": "BLOCKED", "runtime_status": "NOT_RUN",
            "reason": "UE live graph export is required; no parent/components/nodes have been inferred."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=REPORT_DIR / "asset_inventory.json")
    args = parser.parse_args(argv)
    report = capture()
    atomic_json(args.output, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 2  # A caller requesting a structural gate must not interpret an inventory as PASS.


if __name__ == "__main__":
    raise SystemExit(main())
