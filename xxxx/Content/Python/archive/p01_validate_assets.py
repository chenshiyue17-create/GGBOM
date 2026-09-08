"""P01-E cold-load validation plus a playable Flipbook inspection map."""
from __future__ import annotations

import json
import time
import traceback
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
OUT = ROOT / "output"
MANIFEST = json.loads((ROOT / "Config" / "AssetImportRules.json").read_text(encoding="utf-8"))
ASSETS = unreal.EditorAssetLibrary


def log(message: str) -> None:
    unreal.log(f"[GGBOM-P01-E] {message}")


def path_for(record: dict, suffix: str) -> str:
    destination = record["destination"]
    if suffix == "texture":
        return f"{destination}/Textures/{record['asset_name']}"
    if suffix == "flipbook":
        return f"{destination}/Flipbooks/FB_{record['asset_name']}"
    return f"{destination}/Sprites/SP_{record['asset_name']}"


def spawn_camera() -> None:
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.CameraActor, unreal.Vector(0, -500, 0), unreal.Rotator(pitch=0.0, yaw=90.0, roll=0.0)
    )
    camera = actor.get_component_by_class(unreal.CameraComponent)
    camera.set_editor_property("projection_mode", unreal.CameraProjectionMode.ORTHOGRAPHIC)
    camera.set_editor_property("ortho_width", 1080.0)
    camera.set_editor_property("aspect_ratio", 0.5625)
    actor.set_editor_property("auto_activate_for_player", unreal.AutoReceiveInput.PLAYER0)
    actor.set_actor_label("P01_OrthographicCamera_1080")


def text(label: str, x: float, z: float, size: float = 28.0) -> None:
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.TextRenderActor, unreal.Vector(x, -60, z), unreal.Rotator(pitch=0.0, yaw=-90.0, roll=0.0)
    )
    component = actor.get_component_by_class(unreal.TextRenderComponent)
    component.set_editor_property("text", unreal.Text(label))
    component.set_editor_property("world_size", size)
    component.set_editor_property("text_render_color", unreal.Color(220, 245, 255, 255))
    component.set_editor_property("translucency_sort_priority", 100)


def spawn_flipbook(flipbook: unreal.PaperFlipbook, label: str, x: float, z: float, scale: float) -> None:
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PaperFlipbookActor, unreal.Vector(x, 0, z), unreal.Rotator())
    component = actor.get_component_by_class(unreal.PaperFlipbookComponent)
    if not component:
        raise RuntimeError("PaperFlipbookActor has no PaperFlipbookComponent")
    component.set_editor_property("source_flipbook", flipbook)
    component.set_looping(True)
    component.set_play_rate(1.0)
    component.play_from_start()
    component.set_editor_property("translucency_sort_priority", 20)
    actor.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    actor.set_actor_label("P01_Playing_" + label)
    text(label, x, z - 245 * scale, 24)


def spawn_sprite(sprite: unreal.PaperSprite, label: str, x: float, z: float, scale: float) -> None:
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PaperSpriteActor, unreal.Vector(x, 0, z), unreal.Rotator())
    component = actor.get_component_by_class(unreal.PaperSpriteComponent)
    component.set_editor_property("source_sprite", sprite)
    component.set_editor_property("translucency_sort_priority", 20)
    actor.set_actor_scale3d(unreal.Vector(scale, scale, scale))
    actor.set_actor_label("P01_Opened_" + label)
    text(label, x, z - 220 * scale, 22)


def main() -> None:
    started = time.time()
    representative_ids = set(MANIFEST["representative_ids"])
    records = [r for r in MANIFEST["records"] if r["id"] in representative_ids]
    failures: list[dict] = []
    checks: list[dict] = []
    assets: dict[str, object] = {}
    for record in records:
        texture = unreal.load_asset(path_for(record, "texture"))
        if not texture:
            failures.append({"source": record["source"], "kind": "texture", "error": "cold_load_failed"})
            continue
        item = {"source": record["source"], "texture": texture.get_path_name(), "opened": True}
        if record["generate_flipbook"]:
            flipbook = unreal.load_asset(path_for(record, "flipbook"))
            expected = int(record["rows"]) * int(record["columns"])
            count = len(flipbook.get_editor_property("key_frames")) if flipbook else 0
            if not flipbook or count != expected:
                failures.append({"source": record["source"], "kind": "flipbook", "frames": count, "expected": expected})
            else:
                item.update({"flipbook": flipbook.get_path_name(), "frames": count, "playing": True})
                assets[record["id"]] = flipbook
        else:
            sprite = unreal.load_asset(path_for(record, "sprite"))
            if not sprite:
                failures.append({"source": record["source"], "kind": "sprite", "error": "cold_load_failed"})
            else:
                item["sprite"] = sprite.get_path_name()
                assets[record["id"]] = sprite
        checks.append(item)

    unreal.EditorLevelLibrary.new_level("/Game/P01/Maps/MAP_P01_FlipbookValidation")
    spawn_camera()
    text("P01-E  FLIPBOOK PLAYBACK  |  STRICT MANIFEST", 0, 900, 39)
    flip_records = [r for r in records if r["generate_flipbook"]]
    sprite_records = [r for r in records if not r["generate_flipbook"]]
    positions = [(-330, 520, 0.36), (0, 520, 0.38), (330, 520, 0.42), (-180, 40, 0.32), (180, 40, 0.32)]
    for record, (x, z, scale) in zip(flip_records, positions):
        spawn_flipbook(assets[record["id"]], Path(record["source"]).stem.replace("_Sheet", "")[:24], x, z, scale)
    for record, (x, z, scale) in zip(sprite_records, [(-290, -500, 0.22), (0, -500, 0.25), (290, -500, 0.18), (0, -770, 0.23), (350, -770, 0.10)]):
        spawn_sprite(assets[record["id"]], Path(record["source"]).stem[:24], x, z, scale)
    text("5 Flipbooks autoplay  |  5 source Sprites opened  |  1 UU = 1 px", 0, -900, 24)
    world = unreal.EditorLevelLibrary.get_editor_world()
    if not unreal.EditorLoadingAndSavingUtils.save_map(world, "/Game/P01/Maps/MAP_P01_FlipbookValidation"):
        failures.append({"kind": "map", "error": "save_failed"})
    report = {
        "P01_E": "PASS" if not failures else "FAIL",
        "cold_opened_assets": len(checks),
        "flipbooks_playing": len(flip_records),
        "map": "/Game/P01/Maps/MAP_P01_FlipbookValidation",
        "checks": checks,
        "failures": failures,
        "elapsed_seconds": round(time.time() - started, 2),
    }
    (OUT / "P01_E_asset_open_playback.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    status_path = OUT / "P01_status.json"
    status = json.loads(status_path.read_text(encoding="utf-8"))
    status["P01_E"] = report["P01_E"]
    if not failures:
        status["P01_STATUS"] = "PASS"
        status["NEXT_GATE"] = "ALLOW_P02"
    else:
        status["P01_STATUS"] = "FAIL"
        status["NEXT_GATE"] = "BLOCK_P02"
    status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    if failures:
        raise RuntimeError(json.dumps(report, ensure_ascii=False))
    log(f"P01_E_OPEN_AND_PLAY_OK assets={len(checks)} flipbooks={len(flip_records)}")


try:
    main()
except Exception:
    unreal.log_error("[GGBOM-P01-E] " + traceback.format_exc())
    raise
