#!/usr/bin/env python3
"""GGBOM cross-device entry: python tools/dev.py --help"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from ggbom.paths import REPO_ROOT, PROJECT_ROOT, DATA_DIR, engine_binary, local_settings
from ggbom.data_validation import load_tables, validate_tables
from ggbom.config_service import enemy_binding_plan


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate", help="Validate source data only; no runtime PASS")
    sub.add_parser("test", help="Run tooling regression tests without Unreal")
    sub.add_parser("doctor", help="Check checkout and machine-local Unreal path")
    sub.add_parser("config", help="Start the local configuration UI")
    sub.add_parser("config-plan", help="Show exactly which enemy defaults can be applied")
    sub.add_parser("apply-enemy-defaults", help="Apply existing enemy numeric defaults in UE; no graph/scene rebuild")
    run = sub.add_parser("run", help="Launch an independent game window")
    run.add_argument("--mode", choices=("lite", "visual"), default="lite")
    run.add_argument("--map")
    preview = sub.add_parser("preview", help="Open an existing preview map; visual acceptance remains NOT_RUN")
    preview.add_argument("target", choices=("ui", "weapon", "enemy"))
    preview.add_argument("asset_id", nargs="?")
    args = parser.parse_args(argv)
    if args.command == "validate":
        from validate_data_tables import main as validate
        return validate([])
    if args.command == "test":
        codes = [subprocess.call([sys.executable, "-m", "unittest", "discover", "-s", str(directory), "-v"], cwd=REPO_ROOT)
                 for directory in (REPO_ROOT / "tests", PROJECT_ROOT / "tests")]
        return 1 if any(codes) else 0
    if args.command == "config":
        return subprocess.call([sys.executable, str(PROJECT_ROOT / "Content/Python/tools/config_studio/server.py")], cwd=REPO_ROOT)
    if args.command == "apply-enemy-defaults":
        from ggbom.runner import apply_config
        result = apply_config()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "success" else 2 if result["status"] == "blocked" else 1
    try:
        if args.command == "config-plan":
            tables = load_tables(DATA_DIR)
            errors = validate_tables(tables)
            if errors:
                raise ValueError("\n".join(errors))
            print(json.dumps(enemy_binding_plan(tables["DT_Enemies.json"]), ensure_ascii=False, indent=2))
            return 0
        if args.command == "doctor":
            if not (PROJECT_ROOT / "xxxx.uproject").is_file():
                raise FileNotFoundError("Missing xxxx/xxxx.uproject")
            binary = engine_binary()
            print(json.dumps({"status": "PATHS_READY", "project": str(PROJECT_ROOT), "ue_binary": str(binary),
                              "runtime_status": "NOT_RUN"}, ensure_ascii=False, indent=2))
            return 0
        if args.command == "preview":
            asset = "/Game/Preview/L_Preview_" + {"ui": "UI", "weapon": "Weapon", "enemy": "Enemy"}[args.target]
            if args.asset_id:
                print("BLOCKED: asset-specific preview selection is not implemented; no view or approval was generated.")
                return 2
            package = PROJECT_ROOT / "Content" / (asset.removeprefix("/Game/") + ".umap")
            if not package.exists():
                raise FileNotFoundError(f"Preview map missing: {asset}")
            print("Opening existing map; visual acceptance and screenshot capture are NOT_RUN.")
        else:
            asset = args.map or local_settings().get("start_map", "/Game/GGBOM/Maps/MAP_GGBOM_Main")
        binary = engine_binary()
        lite = args.command == "run" and args.mode == "lite"
        command = [str(binary), str(PROJECT_ROOT / "xxxx.uproject"), asset, "-game", "-windowed", "-NoSplash"]
        command += ["-ResX=360", "-ResY=640", "-ForceRes", "-ExecCmds=sg.ShadowQuality 0,sg.PostProcessQuality 0,t.MaxFPS 30"] if lite else ["-ResX=540", "-ResY=960"]
        return subprocess.call(command)
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc), "runtime_status": "NOT_RUN"}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
