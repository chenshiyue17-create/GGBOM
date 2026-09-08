"""Schema and cross-table validation for GGBOM's current dictionary data format."""
import json
import math
from pathlib import Path

CORE_TABLES = ("DT_Enemies.json", "DT_Weapons.json", "DT_WaveProgression.json")


def load_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result
    def invalid(value):
        raise ValueError(f"Non-finite JSON constant: {value}")
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=pairs,
                      parse_constant=invalid)


def rows(data, label, errors):
    if not isinstance(data, dict) or not data:
        errors.append(f"{label}: expected a non-empty object keyed by row ID")
        return []
    result = []
    for key, value in data.items():
        if not isinstance(key, str) or not key or not isinstance(value, dict):
            errors.append(f"{label}.{key}: invalid row")
        else:
            result.append((key, value))
    return result


def number(row, key, label, errors, minimum=0, exclusive=False, integer=False, required=True):
    if key not in row and not required:
        return None
    value = row.get(key)
    valid = type(value) in (int, float) and math.isfinite(value)
    if integer:
        valid = valid and type(value) is int
    if valid:
        valid = value > minimum if exclusive else value >= minimum
    if not valid:
        op = ">" if exclusive else ">="
        errors.append(f"{label}.{key}: expected finite {'integer' if integer else 'number'} {op} {minimum}")
        return None
    return value


def text(row, key, label, errors):
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label}.{key}: expected non-empty string")
        return None
    return value


def enemy_errors(data):
    errors = []
    for key, row in rows(data, "Enemies", errors):
        label = f"Enemies.{key}"
        text(row, "DisplayName", label, errors)
        asset = text(row, "BlueprintClass", label, errors)
        if asset and (not asset.startswith("/Game/") or not asset.endswith("_C")):
            errors.append(f"{label}.BlueprintClass: expected /Game/...Object_C")
        for field in ("MaxHealth", "MoveSpeed", "Scale"):
            number(row, field, label, errors, exclusive=True)
        for field in ("ContactDamage", "ExpGemValue"):
            number(row, field, label, errors)
        number(row, "ScoreReward", label, errors, required=False)
    return errors


def weapon_errors(data):
    errors = []
    for key, row in rows(data, "Weapons", errors):
        label = f"Weapons.{key}"
        text(row, "DisplayName", label, errors)
        for field in ("Damage", "FireRate", "ProjectileSpeed", "LifeSpan"):
            number(row, field, label, errors, exclusive=True)
        number(row, "PelletCount", label, errors, minimum=1, integer=True)
        number(row, "PierceCount", label, errors, integer=True, required=False)
        for field in ("BulletScale", "CollisionRadius", "CollisionHeight"):
            number(row, field, label, errors, exclusive=True, required=False)
        for field in ("SpreadAngle", "ExplosionRadius", "ExplosionDamage"):
            number(row, field, label, errors, required=False)
    return errors


def wave_errors(data, enemies):
    errors = []
    for sid, stage in rows(data, "Waves", errors):
        label = f"Waves.{sid}"
        duration = number(stage, "TotalDuration", label, errors, exclusive=True)
        victory = number(stage, "VictoryTriggerTime", label, errors, required=False)
        if duration is not None and victory is not None and victory > duration:
            errors.append(f"{label}.VictoryTriggerTime exceeds TotalDuration")
        lanes = stage.get("SpawnLanesX")
        if not isinstance(lanes, list) or not lanes:
            errors.append(f"{label}.SpawnLanesX: expected non-empty list")
            lanes = []
        for lane in lanes:
            if type(lane) not in (int, float) or not math.isfinite(lane):
                errors.append(f"{label}.SpawnLanesX: lane must be finite number")
        waves = stage.get("Waves")
        if not isinstance(waves, list) or not waves:
            errors.append(f"{label}.Waves: expected non-empty list")
            continue
        last = -1
        for index, wave in enumerate(waves):
            tag = f"{label}.Waves[{index}]"
            if not isinstance(wave, dict):
                errors.append(f"{tag}: expected object")
                continue
            time = number(wave, "TimeOffset", tag, errors)
            count = number(wave, "Count", tag, errors, minimum=1, integer=True)
            interval = number(wave, "Interval", tag, errors)
            lane = number(wave, "LaneIndex", tag, errors, integer=True)
            if lane is not None and lane >= len(lanes):
                errors.append(f"{tag}.LaneIndex: out of bounds")
            enemy = wave.get("EnemyType")
            if not isinstance(enemy, str) or not isinstance(enemies, dict) or enemy not in enemies:
                errors.append(f"{tag}.EnemyType: unknown enemy {enemy!r}")
            if time is not None:
                if time < last:
                    errors.append(f"{tag}.TimeOffset: time order must be non-decreasing")
                last = time
                if duration is not None and time > duration:
                    errors.append(f"{tag}.TimeOffset exceeds TotalDuration")
            if None not in (time, count, interval, duration):
                if time + (count - 1) * interval > duration:
                    errors.append(f"{tag}: final spawn exceeds TotalDuration")
            if "DangerAlert" in wave and type(wave["DangerAlert"]) is not bool:
                errors.append(f"{tag}.DangerAlert: expected boolean")
    return errors


def validate_tables(tables):
    errors = []
    for name in CORE_TABLES:
        if name not in tables:
            errors.append(f"Missing table: {name}")
    enemies = tables.get("DT_Enemies.json")
    errors += enemy_errors(enemies)
    errors += weapon_errors(tables.get("DT_Weapons.json"))
    errors += wave_errors(tables.get("DT_WaveProgression.json"), enemies)
    # Optional effect tables become authoritative when supplied.
    for rid, row in (tables.get("DT_Weapons.json") or {}).items() if isinstance(tables.get("DT_Weapons.json"), dict) else []:
        if not isinstance(row, dict):
            continue
        for field, table in (("HitEffectID", "DT_HitEffects.json"), ("InflictDebuffID", "DT_StatusEffects.json")):
            ref = row.get(field)
            if table in tables and ref not in (None, "", "None"):
                if not isinstance(ref, str) or ref not in tables[table]:
                    errors.append(f"Weapons.{rid}.{field}: unknown ID {ref!r}")
    return errors


def load_tables(directory):
    directory = Path(directory)
    result = {name: load_json(directory / name) for name in CORE_TABLES}
    for name in ("DT_HitEffects.json", "DT_StatusEffects.json"):
        if (directory / name).exists():
            result[name] = load_json(directory / name)
    return result
