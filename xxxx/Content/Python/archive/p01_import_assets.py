"""Import P01 assets into UE5.8 with strict, manifest-declared grid slicing."""
from __future__ import annotations

import json
import re
import time
import traceback
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
MANIFEST_PATH = ROOT / "Config" / "AssetImportRules.json"
OUT = ROOT / "output"
ASSETS = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()


def log(message: str) -> None:
    unreal.log(f"[GGBOM-P01] {message}")


def command_mode() -> str:
    command = unreal.SystemLibrary.get_command_line()
    match = re.search(r"-P01Mode=(representative|full)", command, re.IGNORECASE)
    return match.group(1).lower() if match else "representative"


def mode_path(path: str, mode: str) -> str:
    if mode == "representative":
        return path.replace("/Game/P01/Imported", "/Game/P01/Representative", 1)
    return path


def ensure(path: str) -> None:
    if not ASSETS.does_directory_exist(path):
        ASSETS.make_directory(path)


def full_asset_path(record: dict, mode: str) -> str:
    return f"{mode_path(record['destination'], mode)}/Textures/{record['asset_name']}"


def import_textures(records: list[dict], mode: str, failures: list[dict]) -> dict[str, unreal.Texture2D]:
    textures: dict[str, unreal.Texture2D] = {}
    for start in range(0, len(records), 40):
        batch = records[start : start + 40]
        tasks: list[unreal.AssetImportTask] = []
        task_records: list[dict] = []
        for record in batch:
            source = ROOT / record["source"]
            if not source.is_file():
                failures.append({"source": record["source"], "stage": "source", "error": "missing"})
                continue
            destination = mode_path(record["destination"], mode) + "/Textures"
            ensure(destination)
            task = unreal.AssetImportTask()
            task.set_editor_property("filename", str(source))
            task.set_editor_property("destination_path", destination)
            task.set_editor_property("destination_name", record["asset_name"])
            task.set_editor_property("automated", True)
            task.set_editor_property("replace_existing", True)
            task.set_editor_property("save", True)
            tasks.append(task)
            task_records.append(record)
        if tasks:
            TOOLS.import_asset_tasks(tasks)
        for record in task_records:
            asset_path = full_asset_path(record, mode)
            texture = unreal.load_asset(asset_path)
            if not texture:
                failures.append({"source": record["source"], "stage": "texture_import", "error": asset_path})
                continue
            for prop, value in (
                ("compression_settings", unreal.TextureCompressionSettings.TC_EDITOR_ICON),
                ("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS),
                ("filter", unreal.TextureFilter.TF_BILINEAR),
                ("srgb", True),
            ):
                try:
                    texture.set_editor_property(prop, value)
                except Exception:
                    pass
            group = getattr(unreal.TextureGroup, "TEXTUREGROUP_2D_PIXELS", None) or getattr(unreal.TextureGroup, "TEXTUREGROUP_UI", None)
            if group is not None:
                try:
                    texture.set_editor_property("lod_group", group)
                except Exception:
                    pass
            ASSETS.save_loaded_asset(texture, only_if_is_dirty=False)
            textures[record["id"]] = texture
        log(f"texture progress {min(start + 40, len(records))}/{len(records)}")
    return textures


def pivot_for(record: dict):
    pivot = getattr(unreal, "SpritePivotMode", getattr(unreal, "PaperSpritePivotMode", None))
    if pivot is None:
        return None
    if record["category"] in {"01_Player", "02_Enemies", "05_VFX"}:
        return pivot.BOTTOM_CENTER
    return pivot.CENTER_CENTER


def create_sprite(name: str, folder: str, texture: unreal.Texture2D, record: dict, uv_x: int, uv_y: int, width: int, height: int) -> unreal.PaperSprite:
    ensure(folder)
    asset_path = f"{folder}/{name}"
    if ASSETS.does_asset_exist(asset_path):
        ASSETS.delete_asset(asset_path)
    sprite = TOOLS.create_asset(name, folder, unreal.PaperSprite, unreal.PaperSpriteFactory())
    if not sprite:
        raise RuntimeError(f"PaperSprite creation failed: {asset_path}")
    texture_width = float(texture.blueprint_get_size_x())
    texture_height = float(texture.blueprint_get_size_y())
    sprite.set_editor_property("source_texture", texture)
    sprite.set_editor_property("source_uv", unreal.Vector2D(float(uv_x), float(uv_y)))
    sprite.set_editor_property("source_dimension", unreal.Vector2D(float(width), float(height)))
    try:
        sprite.set_editor_property("source_texture_dimension", unreal.Vector2D(texture_width, texture_height))
    except Exception:
        pass
    sprite.set_editor_property("pixels_per_unreal_unit", 1.0)
    pivot = pivot_for(record)
    if pivot is not None:
        sprite.set_editor_property("pivot_mode", pivot)
    material = unreal.load_asset("/Paper2D/TranslucentUnlitSpriteMaterial")
    if material:
        sprite.set_editor_property("default_material", material)
    try:
        geometry = sprite.get_editor_property("render_geometry")
        geometry.set_editor_property("geometry_type", unreal.SpritePolygonMode.SOURCE_BOUNDING_BOX)
        sprite.set_editor_property("render_geometry", geometry)
    except Exception:
        pass
    ASSETS.save_loaded_asset(sprite, only_if_is_dirty=False)
    return sprite


def create_flipbook(record: dict, mode: str, sprites: list[unreal.PaperSprite]) -> unreal.PaperFlipbook:
    folder = mode_path(record["destination"], mode) + "/Flipbooks"
    ensure(folder)
    name = "FB_" + record["asset_name"]
    asset_path = f"{folder}/{name}"
    if ASSETS.does_asset_exist(asset_path):
        ASSETS.delete_asset(asset_path)
    flipbook = TOOLS.create_asset(name, folder, unreal.PaperFlipbook, unreal.PaperFlipbookFactory())
    if not flipbook:
        raise RuntimeError(f"PaperFlipbook creation failed: {asset_path}")
    keys = []
    for sprite in sprites:
        key = unreal.PaperFlipbookKeyFrame()
        key.set_editor_property("sprite", sprite)
        key.set_editor_property("frame_run", 1)
        keys.append(key)
    flipbook.set_editor_property("frames_per_second", float(record["fps"]))
    flipbook.set_editor_property("key_frames", keys)
    ASSETS.save_loaded_asset(flipbook, only_if_is_dirty=False)
    return flipbook


def create_runtime_assets(records: list[dict], textures: dict[str, unreal.Texture2D], mode: str, failures: list[dict]) -> tuple[int, int]:
    sprite_count = 0
    flipbook_count = 0
    for index, record in enumerate(records, 1):
        texture = textures.get(record["id"])
        if not texture:
            continue
        try:
            sprite_folder = mode_path(record["destination"], mode) + "/Sprites"
            if record["kind"] == "single_sprite":
                create_sprite("SP_" + record["asset_name"], sprite_folder, texture, record, 0, 0, record["width"], record["height"])
                sprite_count += 1
            elif record["generate_flipbook"]:
                rows = int(record["rows"])
                columns = int(record["columns"])
                if record["width"] % columns != 0 or record["height"] % rows != 0:
                    raise RuntimeError(f"strict grid failure {record['width']}x{record['height']} / {columns}x{rows}")
                cell_width = record["width"] // columns
                cell_height = record["height"] // rows
                sliced: list[unreal.PaperSprite] = []
                frame = 0
                frame_folder = sprite_folder + "/" + record["asset_name"]
                for row in range(rows):
                    for column in range(columns):
                        frame += 1
                        sliced.append(create_sprite(
                            f"SP_{record['asset_name']}_F{frame:03d}", frame_folder, texture, record,
                            column * cell_width, row * cell_height, cell_width, cell_height,
                        ))
                sprite_count += len(sliced)
                create_flipbook(record, mode, sliced)
                flipbook_count += 1
        except Exception as exc:
            failures.append({"source": record["source"], "stage": "derived_asset", "error": str(exc)})
        if index % 50 == 0:
            log(f"derived progress {index}/{len(records)}")
    return sprite_count, flipbook_count


def verify(records: list[dict], mode: str, failures: list[dict]) -> None:
    for record in records:
        if not ASSETS.does_asset_exist(full_asset_path(record, mode)):
            failures.append({"source": record["source"], "stage": "verify_texture", "error": "missing after save"})
        if record["generate_flipbook"]:
            path = f"{mode_path(record['destination'], mode)}/Flipbooks/FB_{record['asset_name']}"
            asset = unreal.load_asset(path)
            if not asset:
                failures.append({"source": record["source"], "stage": "verify_flipbook", "error": path})
            else:
                keys = asset.get_editor_property("key_frames")
                expected = int(record["rows"]) * int(record["columns"])
                if len(keys) != expected:
                    failures.append({"source": record["source"], "stage": "verify_flipbook", "error": f"frames={len(keys)} expected={expected}"})


def update_status(mode: str, report: dict) -> None:
    status_path = OUT / "P01_status.json"
    status = json.loads(status_path.read_text(encoding="utf-8"))
    if mode == "representative":
        status["P01_C"] = "PASS" if report["ImportFailCount"] == 0 and report["primary_record_count"] == 10 else "FAIL"
        status["NEXT_GATE"] = "RUN_P01_D" if status["P01_C"] == "PASS" else "BLOCK_P02"
    else:
        status["P01_D"] = "PASS" if report["ImportFailCount"] == 0 else "FAIL"
        status["ImportFailCount"] = report["ImportFailCount"]
        status["NEXT_GATE"] = "RUN_P01_E" if status["P01_D"] == "PASS" else "BLOCK_P02"
    status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")


def run() -> None:
    started = time.time()
    mode = command_mode()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    all_records = manifest["records"]
    if mode == "representative":
        selected = set(manifest["representative_ids"])
        records = [record for record in all_records if record["id"] in selected]
    else:
        records = all_records
    target_root = "/Game/P01/Representative" if mode == "representative" else "/Game/P01/Imported"
    if ASSETS.does_directory_exist(target_root):
        ASSETS.delete_directory(target_root)
    ensure(target_root)
    failures: list[dict] = []
    textures = import_textures(records, mode, failures)
    sprite_count, flipbook_count = create_runtime_assets(records, textures, mode, failures)
    verify(records, mode, failures)
    report = {
        "mode": mode,
        "success": not failures,
        "primary_record_count": len(records),
        "texture_count": len(textures),
        "sprite_count": sprite_count,
        "flipbook_count": flipbook_count,
        "ImportFailCount": len(failures),
        "failures": failures,
        "elapsed_seconds": round(time.time() - started, 2),
    }
    report_path = OUT / ("P01_C_representative_import.json" if mode == "representative" else "P01_D_full_import.json")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    update_status(mode, report)
    marker = "P01_C_IMPORT_OK" if mode == "representative" else "P01_D_IMPORT_OK"
    if failures:
        raise RuntimeError(json.dumps(report, ensure_ascii=False))
    log(f"{marker} records={len(records)} textures={len(textures)} sprites={sprite_count} flipbooks={flipbook_count}")
    unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")


try:
    run()
except Exception:
    unreal.log_error("[GGBOM-P01] " + traceback.format_exc())
    raise
