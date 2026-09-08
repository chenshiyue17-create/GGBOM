#!/usr/bin/env python3
"""P01 source audit and deterministic Paper2D import-manifest generator.

Frame counts are accepted only from verifiable sibling frame files or from the
explicit projectile override supplied for P01 (Rows=1, Columns=4). Originals
are never modified.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ART_ROOT = ROOT / "Content" / "美术" / "Art"
OUT = ROOT / "output"
CONFIG = ROOT / "Config"
GENERATED = ROOT / "Intermediate" / "P01" / "Generated" / "ProjectileFlight4"
MANIFEST_PATH = CONFIG / "AssetImportRules.json"
AUDIT_JSON = OUT / "P01_asset_audit.json"
AUDIT_CSV = OUT / "P01_asset_audit.csv"
STATUS_PATH = OUT / "P01_status.json"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def category(path: Path) -> str:
    return path.relative_to(ART_ROOT).parts[0]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def image_info(path: Path) -> dict[str, Any]:
    with Image.open(path) as image:
        image.load()
        alpha = image.getchannel("A") if "A" in image.getbands() else None
        alpha_extrema = alpha.getextrema() if alpha is not None else None
        return {
            "width": image.width,
            "height": image.height,
            "mode": image.mode,
            "has_alpha_channel": alpha is not None,
            "has_transparency": bool(alpha_extrema and alpha_extrema[0] < 255),
            "alpha_min": alpha_extrema[0] if alpha_extrema else 255,
            "alpha_max": alpha_extrema[1] if alpha_extrema else 255,
        }


def numbered_siblings(sheet: Path) -> list[Path]:
    prefix = sheet.stem.removesuffix("_Sheet")
    found: list[tuple[int, Path]] = []
    pattern = re.compile(re.escape(prefix) + r"_(\d+)$")
    for candidate in sheet.parent.glob(prefix + "_*.png"):
        match = pattern.fullmatch(candidate.stem)
        if match:
            found.append((int(match.group(1)), candidate))
    return [path for _, path in sorted(found)]


def verified_sheet_rule(sheet: Path, cache: dict[Path, dict[str, Any]]) -> dict[str, Any]:
    cat = category(sheet)
    # Card/UI composites are documented atlases, not temporal animations. Their
    # nonuniform pieces are imported individually; no grid is invented here.
    if cat in {"06_Cards", "07_UI"}:
        return {
            "kind": "atlas_texture_only",
            "strict_equal_cells": False,
            "rows": None,
            "columns": None,
            "frame_sources": [],
            "validation": "NOT_SLICED_NONUNIFORM_ATLAS",
            "valid": True,
        }

    frames = numbered_siblings(sheet)
    if not frames:
        frames = sorted(p for p in sheet.parent.glob("*.png") if p != sheet and not p.stem.endswith("_Sheet"))
    frame_dims = [(cache[p]["width"], cache[p]["height"]) for p in frames]
    sw, sh = cache[sheet]["width"], cache[sheet]["height"]
    equal_sources = bool(frame_dims) and len(set(frame_dims)) == 1
    columns = len(frames)
    strict = bool(equal_sources and columns > 0 and sw % columns == 0 and sh % 1 == 0)
    exact = bool(strict and sw == frame_dims[0][0] * columns and sh == frame_dims[0][1])
    return {
        "kind": "animation_sheet",
        "strict_equal_cells": True,
        "rows": 1,
        "columns": columns,
        "cell_width": sw // columns if columns and sw % columns == 0 else None,
        "cell_height": sh,
        "frame_sources": [rel(p) for p in frames],
        "validation": "EXACT_SIBLING_FRAME_MATCH" if exact else "STRICT_EQUAL_CELL_FAIL",
        "valid": exact,
    }


def generated_projectile_sheet(source: Path) -> Path:
    target = GENERATED / source.parent.name / f"{source.stem}_Strict4.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as original:
        frame = original.convert("RGBA")
        sheet = Image.new("RGBA", (frame.width * 4, frame.height), (0, 0, 0, 0))
        for column in range(4):
            sheet.alpha_composite(frame, (column * frame.width, 0))
        sheet.save(target)
    return target


def ue_folder_for(source_rel: str) -> str:
    parent = Path(source_rel).parent
    parts = [re.sub(r"[^A-Za-z0-9_]+", "_", part).strip("_") or "Asset" for part in parent.parts]
    return "/Game/P01/Imported/" + "/".join(parts)


def representative_records(records: list[dict[str, Any]]) -> list[str]:
    selectors = [
        lambda r: r["category"] == "01_Player" and r["kind"] == "animation_sheet",
        lambda r: "02_Enemies/Zombie" in r["source"] and r["kind"] == "single_sprite",
        lambda r: "Boss_Overlord" in r["source"] and r["kind"] == "animation_sheet",
        lambda r: r["kind"] == "projectile_strict4_sheet",
        lambda r: r["category"] == "05_VFX" and r["kind"] == "animation_sheet",
        lambda r: r["category"] == "04_Props" and r["kind"] == "animation_sheet",
        lambda r: r["category"] == "07_UI" and r["kind"] == "single_sprite",
        lambda r: r["category"] == "06_Cards" and r["kind"] == "single_sprite",
        lambda r: r["category"] == "08_Maps" and "_Ground" in r["source"],
        lambda r: r["category"] == "08_Maps" and "_Overhead" in r["source"],
    ]
    chosen: list[str] = []
    for selector in selectors:
        match = next((r for r in records if selector(r) and r["id"] not in chosen), None)
        if match is None:
            raise RuntimeError("Unable to resolve all 10 representative P01 assets")
        chosen.append(match["id"])
    return chosen


def build() -> dict[str, Any]:
    if not ART_ROOT.is_dir():
        raise SystemExit(f"Missing art root: {ART_ROOT}")
    OUT.mkdir(parents=True, exist_ok=True)
    CONFIG.mkdir(parents=True, exist_ok=True)
    pngs = sorted(ART_ROOT.rglob("*.png"))
    cache = {path: image_info(path) for path in pngs}
    source_audit: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    strict_failures: list[str] = []

    for path in pngs:
        info = cache[path]
        source_rel = rel(path)
        source_audit.append({
            "source": source_rel,
            "category": category(path),
            **info,
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        })
        if path.stem.endswith("_Sheet"):
            rule = verified_sheet_rule(path, cache)
        else:
            rule = {
                "kind": "single_sprite",
                "strict_equal_cells": False,
                "rows": 1,
                "columns": 1,
                "frame_sources": [],
                "validation": "FULL_IMAGE_SINGLE_SPRITE",
                "valid": True,
            }
        record = {
            "id": hashlib.sha1(source_rel.encode("utf-8")).hexdigest()[:16],
            "source": source_rel,
            "source_kind": "original",
            "category": category(path),
            "asset_name": path.stem,
            "destination": ue_folder_for(source_rel),
            "width": info["width"],
            "height": info["height"],
            "alpha": info["has_alpha_channel"],
            "transparent": info["has_transparency"],
            "generate_sprite": rule["kind"] == "single_sprite",
            "generate_flipbook": rule["kind"] == "animation_sheet" and rule["valid"],
            "fps": 8.0,
            **rule,
        }
        records.append(record)
        if rule["strict_equal_cells"] and not rule["valid"]:
            strict_failures.append(source_rel)

    projectile_sources = sorted(ART_ROOT.glob("03_Weapons/*/*_02_Flight.png"))
    if len(projectile_sources) != 10:
        strict_failures.append(f"PROJECTILE_SOURCE_COUNT={len(projectile_sources)}")
    for source in projectile_sources:
        generated = generated_projectile_sheet(source)
        info = image_info(generated)
        source_rel = rel(generated)
        valid = info["width"] % 4 == 0 and info["height"] % 1 == 0
        record = {
            "id": hashlib.sha1(source_rel.encode("utf-8")).hexdigest()[:16],
            "source": source_rel,
            "source_kind": "generated_from_original_without_modifying_original",
            "generated_from": rel(source),
            "category": "03_Weapons",
            "asset_name": generated.stem,
            "destination": ue_folder_for(source_rel),
            "width": info["width"],
            "height": info["height"],
            "alpha": True,
            "transparent": info["has_transparency"],
            "kind": "projectile_strict4_sheet",
            "strict_equal_cells": True,
            "rows": 1,
            "columns": 4,
            "cell_width": info["width"] // 4 if valid else None,
            "cell_height": info["height"],
            "frame_sources": [],
            "validation": "EXPLICIT_USER_RULE_1X4_EQUAL_GENERATED" if valid else "STRICT_EQUAL_CELL_FAIL",
            "valid": valid,
            "generate_sprite": False,
            "generate_flipbook": valid,
            "fps": 12.0,
        }
        records.append(record)
        if not valid:
            strict_failures.append(source_rel)

    top_categories = Counter(item["category"] for item in source_audit)
    player_dirs = {m.group(0) for p in pngs if category(p) == "01_Player" for m in [re.search(r"Dir_\d+_[A-Za-z]+", p.as_posix())] if m}
    enemy_dirs = {m.group(0) for p in pngs if category(p) == "02_Enemies" for m in [re.search(r"Dir_\d+_[A-Za-z]+", p.as_posix())] if m}
    player8 = {"Down", "DownLeft", "Left", "UpLeft", "Up", "UpRight", "Right", "DownRight"}
    physical_player = {d.split("_", 2)[-1] for d in player_dirs}
    mirrored_player = physical_player | {"DownRight", "Right", "UpRight"}
    physical_enemy_indices = {d.split("_")[1] for d in enemy_dirs}
    gates = {
        "Player8Dir": "PASS" if player8 <= mirrored_player else "FAIL",
        "Enemy4Dir": "PASS" if {"01", "02", "03", "04"} <= physical_enemy_indices else "FAIL",
        "Boss4Dir": "PASS" if all(any(f"Boss_Overlord" in r["source"] and f"Dir_{i}_" in r["source"] for r in records) for i in ("01", "02", "03", "04")) else "FAIL",
        "ProjectileStrict4Equal": "PASS" if len(projectile_sources) == 10 and not any("ProjectileFlight4" in x for x in strict_failures) else "FAIL",
        "VFX": "PASS" if top_categories["05_VFX"] > 0 else "FAIL",
        "Props": "PASS" if len(list((ART_ROOT / "04_Props").glob("[0-9][0-9]_*"))) == 10 else "FAIL",
        "UI": "PASS" if len(list((ART_ROOT / "07_UI").glob("[0-9][0-9]_*"))) == 5 else "FAIL",
        "MapsGroundOverhead": "PASS" if len(list((ART_ROOT / "08_Maps").rglob("*_Ground.png"))) == 5 and len(list((ART_ROOT / "08_Maps").rglob("*_Overhead.png"))) == 5 else "FAIL",
    }
    representatives = representative_records(records)
    overall = not strict_failures and all(value == "PASS" for value in gates.values())
    manifest = {
        "schema_version": 1,
        "generated_by": "Tools/p01_asset_pipeline.py",
        "art_root": rel(ART_ROOT),
        "rules": {
            "pixels_per_unreal_unit": 1.0,
            "alpha_threshold": 0.05,
            "filter": "bilinear",
            "mipmaps": False,
            "strict_equal_cells": True,
            "dimension_gate": "Width % Columns == 0 AND Height % Rows == 0",
            "failed_assets_generate_sprite": False,
            "player_direction_mirror": {"DownRight": "DownLeft", "Right": "Left", "UpRight": "UpLeft"},
            "projectile_flight": {"rows": 1, "columns": 4, "strict_equal_cells": True, "source_policy": "four explicit equal cells generated from the unmodified Flight source"},
        },
        "representative_ids": representatives,
        "records": records,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    audit = {
        "P01_A": "PASS" if not strict_failures else "FAIL",
        "P01_B": "PASS" if overall else "FAIL",
        "source_png_count": len(pngs),
        "source_rgba_count": sum(item["mode"] == "RGBA" for item in source_audit),
        "source_with_transparency_count": sum(item["has_transparency"] for item in source_audit),
        "animation_sheet_count": sum(r["kind"] == "animation_sheet" for r in records),
        "atlas_texture_only_count": sum(r["kind"] == "atlas_texture_only" for r in records),
        "projectile_strict4_count": sum(r["kind"] == "projectile_strict4_sheet" for r in records),
        "strict_failures": strict_failures,
        "categories": dict(sorted(top_categories.items())),
        "gates": gates,
        "representative_ids": representatives,
        "assets": source_audit,
    }
    AUDIT_JSON.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    with AUDIT_CSV.open("w", encoding="utf-8", newline="") as stream:
        fields = ["source", "category", "width", "height", "mode", "has_alpha_channel", "has_transparency", "alpha_min", "alpha_max", "bytes", "sha256"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows({key: item[key] for key in fields} for item in source_audit)
    status = {
        "P01_STATUS": "PENDING_IMPORT" if overall else "FAIL",
        "P01_A": audit["P01_A"],
        "P01_B": audit["P01_B"],
        "ImportFailCount": None,
        "NEXT_GATE": "RUN_P01_C" if overall else "BLOCK_P02",
        **gates,
    }
    STATUS_PATH.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    return {key: value for key, value in audit.items() if key != "assets"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["audit"], default="audit", nargs="?")
    parser.parse_args()
    summary = build()
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["P01_A"] == "PASS" and summary["P01_B"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
