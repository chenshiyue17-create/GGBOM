#!/usr/bin/env python3
"""Compare actual before/after asset-byte inventories, not filenames or synthetic structures."""
import argparse
import json
from pathlib import Path
import re
from ggbom.data_validation import load_json
from ggbom.config_io import atomic_json
from ggbom.paths import REPORT_DIR
from snapshot_blueprint_structure import TARGETS


def compare(before, after):
    indexes = []
    for snapshot in (before, after):
        if snapshot.get("kind") != "ASSET_BINARY_INVENTORY":
            raise ValueError("Only actual ASSET_BINARY_INVENTORY snapshots are accepted")
        index = {}
        for item in snapshot.get("assets", []):
            path, digest = item.get("asset_path"), item.get("sha256")
            if not item.get("exists") or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise ValueError(f"Missing asset/hash: {path}")
            if path in index:
                raise ValueError(f"Duplicate asset: {path}")
            index[path] = digest
        if not set(TARGETS).issubset(index):
            raise ValueError("Inventory does not cover all required core assets")
        indexes.append(index)
    old, new = indexes
    changed = sorted(key for key in old.keys() | new.keys() if old.get(key) != new.get(key))
    return {"scope": "CORE_ASSET_BYTES_ONLY", "status": "FAIL" if changed else "PASS", "changed_assets": changed,
            "runtime_status": "NOT_RUN", "data_driven_success": None,
            "note": "Binary equality proves unchanged bytes only; it does not prove third-weapon functionality."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", type=Path)
    parser.add_argument("--after", type=Path)
    parser.add_argument("--output", type=Path, default=REPORT_DIR / "weapon_core_diff.json")
    args = parser.parse_args(argv)
    try:
        if not args.before or not args.after or args.before.resolve() == args.after.resolve():
            raise ValueError("Supply distinct --before and --after captures around the change")
        report = compare(load_json(args.before), load_json(args.after))
    except (ValueError, OSError, TypeError) as exc:
        report = {"status": "BLOCKED", "reason": str(exc), "runtime_status": "NOT_RUN"}
    atomic_json(args.output, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return {"PASS": 0, "FAIL": 1, "BLOCKED": 2}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
