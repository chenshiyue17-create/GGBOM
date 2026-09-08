"""Config Studio save contract and a narrowly scoped editor-default binding plan."""
import hashlib
import json
from pathlib import Path
from .config_io import commit_json_files, diff_rows
from .data_validation import load_tables, validate_tables, load_json, enemy_errors

TABLE_KEYS = {"characters": "DT_Characters.json", "enemies": "DT_Enemies.json",
              "weapons": "DT_Weapons.json", "cards": "DT_TacticalCards.json",
              "waves": "DT_WaveProgression.json", "tiles": "DT_MapTiles.json",
              "hit_effects": "DT_HitEffects.json"}
ENEMY_FIELDS = ("MaxHealth", "MoveSpeed", "ContactDamage", "ScoreReward", "ExpGemValue")


def content_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode("utf-8")).hexdigest()


def save_request(directory, body):
    if not isinstance(body, dict):
        raise ValueError("Request must be an object")
    updates, diffs = {}, {}
    for key, name in TABLE_KEYS.items():
        if key not in body:
            continue
        value = body[key]
        if not isinstance(value, dict) or not value or any(not isinstance(row, dict) for row in value.values()):
            raise ValueError(f"{key}: expected a non-empty object of rows")
        cleaned = {rid: {field: item for field, item in row.items() if field != "ArtInfo"} for rid, row in value.items()}
        updates[name] = cleaned
    if not updates:
        raise ValueError("No supported tables supplied")
    validation = {}
    def validate_current():
        candidate = load_tables(directory)
        candidate.update(updates)
        errors = validate_tables(candidate)
        if errors:
            raise ValueError("\n".join(errors))
        for name, value in updates.items():
            path = Path(directory) / name
            diffs[name] = diff_rows(load_json(path) if path.exists() else {}, value)
        validation["config_hash"] = content_hash(candidate)
    commit_json_files(directory, updates, validate_current=validate_current)
    return {"modified_tables": list(updates), "raw_diff": diffs, **validation,
            "scope": "SOURCE_JSON", "runtime_status": "NOT_RUN"}


def enemy_binding_plan(enemies):
    errors = enemy_errors(enemies)
    if errors:
        raise ValueError("\n".join(errors))
    plans, seen = [], set()
    for row_id, row in enemies.items():
        class_path = row["BlueprintClass"]
        if class_path in seen:
            raise ValueError(f"Multiple enemy IDs target one BlueprintClass: {class_path}")
        seen.add(class_path)
        plans.append({"row_id": row_id, "class_path": class_path,
                      "asset_path": class_path.split(".")[0],
                      "properties": {field: row[field] for field in ENEMY_FIELDS if field in row},
                      "unapplied_fields": sorted(set(row) - set(ENEMY_FIELDS) - {"BlueprintClass"})})
    return {"scope": "ENEMY_EDITOR_DEFAULTS_ONLY", "config_hash": content_hash(enemies), "bindings": plans,
            "runtime_status": "NOT_RUN", "not_applied": ["weapons", "waves", "characters", "cards", "art", "live_instances"]}
