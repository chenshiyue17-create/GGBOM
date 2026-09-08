#!/usr/bin/env python3
"""Offline only. Success means data validation, never gameplay acceptance."""
import argparse
import json
from ggbom.paths import DATA_DIR
from ggbom.data_validation import load_tables, validate_tables, enemy_errors, weapon_errors, wave_errors


def validate_enemies(data):
    return not enemy_errors(data)


def validate_weapons(data):
    return not weapon_errors(data)


def validate_waves(data, enemies_data):
    return not wave_errors(data, enemies_data)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default=str(DATA_DIR))
    args = parser.parse_args(argv)
    try:
        errors = validate_tables(load_tables(args.data_dir))
    except (OSError, ValueError, TypeError) as exc:
        errors = [str(exc)]
    print(json.dumps({"scope": "DATA_SCHEMA_ONLY", "status": "FAIL" if errors else "PASS",
                      "errors": errors, "runtime_status": "NOT_RUN"}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
