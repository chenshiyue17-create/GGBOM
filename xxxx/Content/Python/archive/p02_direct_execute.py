from __future__ import annotations

import json
import re
import time
import traceback
import zipfile
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
OUT = ROOT / "output"
ZIP_PATH = Path("/Volumes/NINJAV 2/sucai/GGBOM_UE58_P02_DirectWrite.zip")
SPEC_NAME = "GGBOM_UE58_P02_DirectWrite/P02_DIRECT_ASSET_SPEC.json"
EXEC_NAME = "GGBOM_UE58_P02_DirectWrite/P02_DIRECT_EXEC.md"
ASSETS = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
BPLIB = unreal.BlueprintEditorLibrary


def log(message: str) -> None:
    unreal.log("[GGBOM-P02] " + message)


def ensure_dir(path: str) -> None:
    if not ASSETS.does_directory_exist(path):
        ASSETS.make_directory(path)


def delete_asset(path: str) -> None:
    if ASSETS.does_asset_exist(path):
        ASSETS.delete_asset(path)


def save_asset(asset) -> bool:
    return bool(asset and ASSETS.save_loaded_asset(asset, only_if_is_dirty=False))


def load_spec() -> tuple[dict, str]:
    with zipfile.ZipFile(ZIP_PATH) as archive:
        spec = json.loads(archive.read(SPEC_NAME).decode("utf-8"))
        direct_exec = archive.read(EXEC_NAME).decode("utf-8")
    return spec, direct_exec


def validate_preconditions() -> None:
    status_path = OUT / "P01_status.json"
    status = json.loads(status_path.read_text(encoding="utf-8"))
    if status.get("P01_STATUS") != "PASS" or status.get("NEXT_GATE") != "ALLOW_P02":
        raise RuntimeError("P01_STATUS is not PASS or NEXT_GATE is not ALLOW_P02")


def register_tags(tags: list[str]) -> int:
    config = ROOT / "Config" / "DefaultGameplayTags.ini"
    existing = config.read_text(encoding="utf-8") if config.exists() else ""
    lines = []
    if "[/Script/GameplayTags.GameplayTagsList]" not in existing:
        lines.append("[/Script/GameplayTags.GameplayTagsList]")
    for tag in tags:
        entry = f'+GameplayTagList=(Tag="{tag}",DevComment="P02")'
        if entry not in existing:
            lines.append(entry)
    if lines:
        config.write_text((existing.rstrip() + "\n\n" + "\n".join(lines) + "\n").lstrip(), encoding="utf-8")
    return len(tags)


def create_enum_assets(enum_spec: dict[str, list[str]], problems: list[str]) -> int:
    folder = "/Game/Blueprints/Core/Types"
    ensure_dir(folder)
    valid = 0
    for name, expected_items in enum_spec.items():
        path = f"{folder}/{name}"
        delete_asset(path)
        enum_asset = TOOLS.create_asset(name, folder, unreal.UserDefinedEnum, unreal.EnumFactory())
        if not save_asset(enum_asset):
            problems.append(f"enum asset save failed: {name}")
            continue
        # UE5.8 Python can create UserDefinedEnum assets, but does not expose enumerator editing.
        problems.append(f"enum items not writable through pure UE Python: {name} expected={len(expected_items)}")
        valid += 1
    return valid


def create_struct_assets(struct_spec: dict[str, list[list]], problems: list[str]) -> int:
    folder = "/Game/Blueprints/Core/Types"
    ensure_dir(folder)
    valid = 0
    for name, fields in struct_spec.items():
        path = f"{folder}/{name}"
        delete_asset(path)
        struct_asset = TOOLS.create_asset(name, folder, unreal.UserDefinedStruct, unreal.StructureFactory())
        if not save_asset(struct_asset):
            problems.append(f"struct asset save failed: {name}")
            continue
        # UE5.8 Python can create UserDefinedStruct assets, but FStructureEditorUtils is not exposed.
        problems.append(f"struct fields/defaults not writable through pure UE Python: {name} expected={len(fields)}")
        valid += 1
    return valid


def create_projectile_base(problems: list[str]) -> bool:
    folder = "/Game/Blueprints/Projectiles"
    ensure_dir(folder)
    path = f"{folder}/BP_Projectile_Base"
    delete_asset(path)
    bp = BPLIB.create_blueprint_asset_with_parent(path, unreal.Actor.static_class())
    ok = bool(bp and BPLIB.compile_blueprint(bp) and save_asset(bp))
    if not ok:
        problems.append("BP_Projectile_Base compile/save failed")
    return ok


def create_interface_assets(problems: list[str]) -> int:
    folder = "/Game/Blueprints/Core/Interfaces"
    ensure_dir(folder)
    names = [
        "BPI_CombatInterface",
        "BPI_InteractableInterface",
        "BPI_Targetable",
        "BPI_Pickup",
        "BPI_Placeable",
    ]
    created = 0
    for name in names:
        path = f"{folder}/{name}"
        delete_asset(path)
        bp = None
        try:
            factory = unreal.BlueprintFactory()
            factory.set_editor_property("parent_class", unreal.Interface.static_class())
            if hasattr(unreal, "BlueprintType"):
                factory.set_editor_property("blueprint_type", unreal.BlueprintType.BPTYPE_INTERFACE)
            bp = TOOLS.create_asset(name, folder, unreal.Blueprint, factory)
        except Exception as exc:
            problems.append(f"BPI factory failed {name}: {exc}")
        if not bp:
            try:
                bp = BPLIB.create_blueprint_asset_with_parent(path, unreal.Interface.static_class())
            except Exception as exc:
                problems.append(f"BPI fallback failed {name}: {exc}")
        if bp and BPLIB.compile_blueprint(bp) and save_asset(bp):
            problems.append(f"BPI functions not writable through pure UE Python: {name}")
            created += 1
        else:
            problems.append(f"BPI compile/save failed: {name}")
    return created


def create_data_table_placeholders(problems: list[str]) -> int:
    # A real P02 DataTable requires the five generated row structs to contain fields.
    # Since pure UE Python cannot write those struct fields in this UE5.8 binding,
    # do not create misleading DataTable assets.
    names = ["DT_WeaponConfig", "DT_CardUpgrades", "DT_EnemyConfig", "DT_StageWaveConfig"]
    for name in names:
        problems.append(f"DataTable blocked by missing valid row struct: {name}")
    return 0


def create_test_actor(problems: list[str]) -> bool:
    folder = "/Game/Tests"
    ensure_dir(folder)
    path = f"{folder}/BP_Test_CoreData"
    delete_asset(path)
    bp = BPLIB.create_blueprint_asset_with_parent(path, unreal.Actor.static_class())
    if not bp:
        problems.append("BP_Test_CoreData creation failed")
        return False
    try:
        graph = BPLIB.find_event_graph(bp)
        editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
        begin = editor.find_event_node("ReceiveBeginPlay")
        printer = editor.add_call_function_node("/Script/Engine.KismetSystemLibrary.PrintString")
        printer.set_node_pos(unreal.IntPoint(300, 0))
        pinlib = unreal.BlueprintGraphPinLibrary
        in_pins = {str(pinlib.get_pin_name(p)): p for p in BPLIB.list_input_pins(printer)}
        out_pins = {str(pinlib.get_pin_name(p)): p for p in BPLIB.list_output_pins(begin)}
        pinlib.set_pin_value(in_pins["InString"], "P02_DATA_FAIL")
        pinlib.set_pin_value(in_pins["bPrintToLog"], "true")
        pinlib.set_pin_value(in_pins["bPrintToScreen"], "true")
        pinlib.try_create_connection(out_pins["then"], in_pins["execute"])
    except Exception as exc:
        problems.append(f"BP_Test_CoreData graph fallback failed: {exc}")
    ok = bool(BPLIB.compile_blueprint(bp) and save_asset(bp))
    if not ok:
        problems.append("BP_Test_CoreData compile/save failed")
    return ok


def count_log(pattern: str) -> int:
    log_dir = Path.home() / "Library" / "Logs" / "Unreal Engine" / "xxxxEditor"
    if not log_dir.exists():
        return 0
    files = sorted(log_dir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)[:4]
    total = 0
    rx = re.compile(pattern)
    for path in files:
        try:
            total += len(rx.findall(path.read_text(errors="ignore")))
        except Exception:
            pass
    return total


def main() -> None:
    started = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    problems: list[str] = []
    status = {
        "P02_STATUS": "FAIL",
        "ENUMS": "0/9",
        "STRUCTS": "0/5",
        "BPIS": "0/5",
        "DATATABLES": "0/4",
        "P02_DATA_OK": False,
        "P02_DATA_FAIL": False,
        "BROKEN_REFERENCES": 0,
        "BLUEPRINT_RUNTIME_ERRORS": 0,
        "ACCESSED_NONE": 0,
        "BLOCKING_ERROR": "NONE",
        "NEXT_GATE": "BLOCK_P03",
    }
    try:
        spec, direct_exec = load_spec()
        if "P02_DATA_OK" not in direct_exec:
            raise RuntimeError("P02_DIRECT_EXEC.md content check failed")
        validate_preconditions()
        for directory in spec["dirs"]:
            ensure_dir(directory)
        tags_registered = register_tags(spec["tags"])
        enum_count = create_enum_assets(spec["enums"], problems)
        projectile_ok = create_projectile_base(problems)
        struct_count = create_struct_assets(spec["structs"], problems)
        bpi_count = create_interface_assets(problems)
        dt_count = create_data_table_placeholders(problems)
        test_bp_ok = create_test_actor(problems)
        status.update({
            "ENUMS": f"{enum_count}/9",
            "STRUCTS": f"{struct_count}/5",
            "BPIS": f"{bpi_count}/5",
            "DATATABLES": f"{dt_count}/4",
            "tags_registered": tags_registered,
            "projectile_base": projectile_ok,
            "test_blueprint": test_bp_ok,
            "BLOCKING_ERROR": "; ".join(problems[:6]) if problems else "NONE",
        })
        status["P02_DATA_FAIL"] = True
        status["BROKEN_REFERENCES"] = len(problems)
    except Exception as exc:
        status["BLOCKING_ERROR"] = str(exc)
        status["traceback"] = traceback.format_exc()
    status["BLUEPRINT_RUNTIME_ERRORS"] = count_log(r"Blueprint Runtime Error")
    status["ACCESSED_NONE"] = count_log(r"Accessed None")
    status["elapsed_seconds"] = round(time.time() - started, 2)
    status["problems"] = problems
    (OUT / "P02_status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    log("P02_STATUS=" + status["P02_STATUS"])
    log("P02_DATA_FAIL")


if __name__ == "__main__":
    main()
