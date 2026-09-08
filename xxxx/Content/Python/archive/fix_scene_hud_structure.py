# -*- coding: utf-8 -*-
"""
GGBOM scene/HUD structure cleanup.

Pure Blueprint-safe editor automation:
- Does not create or require C++ modules/plugins.
- Does not delete existing placed combat art.
- Moves world actors into stable Outliner folders.
- Archives old HUD PaperSpriteActor widgets away from gameplay folders.
- Ensures HUD Widget Blueprint shell assets exist and compile/save.
- Writes a lightweight audit report for AI handoff.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import unreal


PROJECT_ROOT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
MAP_PATH = "/Game/GGBOM/Maps/MAP_GGBOM_Main"
GEN_ROOT = "/Game/GGBOM"
UI_DIR = f"{GEN_ROOT}/UI"
BP_UI_DIR = f"{GEN_ROOT}/Blueprints/UI"
REPORT_PATH = PROJECT_ROOT / "output" / "scene_hud_structure_status.json"
HANDOFF_PATH = PROJECT_ROOT / "Docs" / "AI_HANDOFF_SCENE_HUD_STRUCTURE.md"

ASSETS = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
BPLIB = unreal.BlueprintEditorLibrary


FOLDERS = {
    "core": "00_Core_Runtime",
    "camera": "01_Camera",
    "stage": "02_Stage_Map",
    "player": "03_Player",
    "enemies": "04_Enemies",
    "boss": "04_Enemies/Boss",
    "defense": "05_Defense_Lanes",
    "props": "06_Combat_Props",
    "pickups": "07_Pickups_VFX",
    "hud_runtime": "08_HUD_Runtime",
    "hud_legacy": "90_ARCHIVE_Legacy_WorldSpace_HUD",
    "system": "99_Engine_Runtime",
}


def log(message: str) -> None:
    unreal.log(f"[GGBOM-SceneHUD] {message}")


def ensure_dir(path: str) -> None:
    if not ASSETS.does_directory_exist(path):
        ASSETS.make_directory(path)


def safe_label(actor: unreal.Actor) -> str:
    try:
        return actor.get_actor_label()
    except Exception:
        return actor.get_name()


def class_name(actor: unreal.Actor) -> str:
    try:
        return actor.get_class().get_name()
    except Exception:
        return str(actor.get_class())


def set_actor_folder(actor: unreal.Actor, folder: str) -> bool:
    """Set Outliner folder via the editor property when exposed."""
    for prop in ("folder_path", "FolderPath"):
        try:
            actor.set_editor_property(prop, folder)
            return True
        except Exception:
            pass
    try:
        # Some UE builds expose folder path as a call_method target.
        actor.call_method("SetFolderPath", (folder,))
        return True
    except Exception:
        return False


def set_hidden(actor: unreal.Actor, hidden: bool) -> None:
    try:
        actor.set_actor_hidden_in_game(hidden)
    except Exception:
        pass
    try:
        actor.set_is_temporarily_hidden_in_editor(hidden)
    except Exception:
        pass


def classify_actor(label: str, klass: str) -> tuple[str, bool]:
    l = label.lower()
    k = klass.lower()

    if label.startswith("HUD_") or label.startswith("UI_") or "bossbar" in l or "btn_pause" in l or "card_" in l:
        return FOLDERS["hud_legacy"], True
    if label in {"HUD0"} or k == "hud":
        return FOLDERS["hud_runtime"], False
    if "camera" in l or "cameramanager" in l:
        return FOLDERS["camera"], False
    if "gamemode" in l or "gamestate" in l or "gamesession" in l or "networkmanager" in l:
        return FOLDERS["core"], False
    if "ground" in l or "overhead" in l or "stage" in l or "map" in l:
        return FOLDERS["stage"], False
    if "player" in l or "medic" in l:
        return FOLDERS["player"], False
    if "boss" in l or "overlord" in l:
        return FOLDERS["boss"], False
    if "zombie" in l or "hound" in l or "brute" in l or "enemy" in l:
        return FOLDERS["enemies"], False
    if "barricade" in l or "defenseline" in l or "defense" in l:
        return FOLDERS["defense"], False
    if "barrel" in l or "mine" in l or "medpod" in l or "prop" in l:
        return FOLDERS["props"], False
    if "gem" in l or "exp" in l or "vfx" in l or "particle" in l:
        return FOLDERS["pickups"], False
    return FOLDERS["system"], False


def create_widget_blueprint(name: str) -> bool:
    ensure_dir(UI_DIR)
    asset_path = f"{UI_DIR}/{name}"
    try:
        if ASSETS.does_asset_exist(asset_path):
            bp = unreal.load_asset(asset_path)
        else:
            bp = TOOLS.create_asset(name, UI_DIR, unreal.WidgetBlueprint, unreal.WidgetBlueprintFactory())
        if not bp:
            return False
        BPLIB.compile_blueprint(bp)
        ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
        return True
    except Exception as exc:
        log(f"Widget create/compile failed {name}: {exc}")
        return False


def create_hud_presenter_actor() -> bool:
    """Create a pure Blueprint actor shell that documents the single HUD owner."""
    ensure_dir(BP_UI_DIR)
    asset_path = f"{BP_UI_DIR}/BP_GGBOM_HUDPresenter"
    try:
        if ASSETS.does_asset_exist(asset_path):
            bp = unreal.load_asset(asset_path)
        else:
            factory = unreal.BlueprintFactory()
            factory.set_editor_property("parent_class", unreal.Actor)
            bp = TOOLS.create_asset("BP_GGBOM_HUDPresenter", BP_UI_DIR, unreal.Blueprint, factory)
        if not bp:
            return False
        BPLIB.compile_blueprint(bp)
        ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
        return True
    except Exception as exc:
        log(f"HUD presenter create/compile failed: {exc}")
        return False


def write_handoff(report: dict) -> None:
    HANDOFF_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# GGBOM Scene + HUD Structure Handoff",
        "",
        f"- Time: {report['time']}",
        f"- Map: {MAP_PATH}",
        f"- PureBlueprint: {report['pure_blueprint']}",
        f"- FolderSetSuccess: {report['folder_set_success']}/{report['actor_count']}",
        f"- LegacyWorldHUDArchived: {report['legacy_world_hud_archived']}",
        f"- LegacyWorldHUDHidden: {report['legacy_world_hud_hidden']}",
        f"- WidgetBlueprints: {report['widget_blueprints']}",
        f"- HUDPresenterBlueprint: {report['hud_presenter_blueprint']}",
        "",
        "## Planned Outliner Structure",
        "",
    ]
    for key, value in FOLDERS.items():
        lines.append(f"- `{value}`")
    lines.extend(
        [
            "",
            "## Rule for next AI",
            "",
            "Do not place screen HUD as PaperSpriteActor in the gameplay world. Use `/Game/GGBOM/UI/WBP_GGBOM_CombatHUD` as the screen HUD root and keep any old world-space HUD actors under `90_ARCHIVE_Legacy_WorldSpace_HUD` hidden.",
            "",
        ]
    )
    HANDOFF_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    log("Start scene/HUD structure cleanup")
    unreal.EditorLevelLibrary.load_level(MAP_PATH)
    world = unreal.EditorLevelLibrary.get_editor_world()
    actors = unreal.EditorLevelLibrary.get_all_level_actors()

    moved = 0
    hidden_legacy = 0
    folder_failures = []
    actor_rows = []

    for actor in actors:
        label = safe_label(actor)
        klass = class_name(actor)
        folder, should_hide = classify_actor(label, klass)
        ok = set_actor_folder(actor, folder)
        if ok:
            moved += 1
        else:
            folder_failures.append(label)
        if should_hide:
            set_hidden(actor, True)
            hidden_legacy += 1
        actor_rows.append(
            {
                "label": label,
                "class": klass,
                "folder": folder,
                "legacy_world_hud": should_hide,
                "folder_set": ok,
            }
        )

    widget_results = {
        "WBP_GGBOM_CombatHUD": create_widget_blueprint("WBP_GGBOM_CombatHUD"),
        "WBP_HUD_WeaponSlot": create_widget_blueprint("WBP_HUD_WeaponSlot"),
        "WBP_HUD_TacticalSlot": create_widget_blueprint("WBP_HUD_TacticalSlot"),
        "WBP_HUD_ZoneTracker": create_widget_blueprint("WBP_HUD_ZoneTracker"),
    }
    presenter_ok = create_hud_presenter_actor()

    save_ok = False
    try:
        save_ok = bool(unreal.EditorLoadingAndSavingUtils.save_map(world, MAP_PATH))
    except Exception:
        try:
            save_ok = bool(ASSETS.save_asset(MAP_PATH, only_if_is_dirty=False))
        except Exception:
            save_ok = False

    ASSETS.save_directory(GEN_ROOT, only_if_is_dirty=False, recursive=True)

    report = {
        "time": datetime.now().isoformat(timespec="seconds"),
        "map": MAP_PATH,
        "pure_blueprint": True,
        "actor_count": len(actors),
        "folder_set_success": moved,
        "folder_set_failures": folder_failures,
        "legacy_world_hud_archived": hidden_legacy,
        "legacy_world_hud_hidden": hidden_legacy,
        "widget_blueprints": widget_results,
        "hud_presenter_blueprint": presenter_ok,
        "map_saved": save_ok,
        "outliner_folders": FOLDERS,
        "actors": actor_rows,
        "status": "PASS" if moved == len(actors) and all(widget_results.values()) and presenter_ok and save_ok else "PARTIAL",
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_handoff(report)

    log(f"SCENE_HUD_STRUCTURE_STATUS={report['status']}")
    log(f"ACTORS={len(actors)} FOLDER_SET={moved} LEGACY_HUD_ARCHIVED={hidden_legacy} MAP_SAVED={save_ok}")


if __name__ == "__main__":
    main()
