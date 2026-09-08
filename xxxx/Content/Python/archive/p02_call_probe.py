from __future__ import annotations

import json
from pathlib import Path

import unreal


def try_call(obj, name, *args):
    try:
        return {"ok": True, "value": str(obj.call_method(name, args))}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def main() -> None:
    root = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
    out = root / "output"
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    assets = unreal.EditorAssetLibrary
    folder = "/Game/Tests/P02CallProbe"
    if assets.does_directory_exist(folder):
        assets.delete_directory(folder)
    assets.make_directory(folder)
    enum = tools.create_asset("ProbeEnum3", folder, unreal.UserDefinedEnum, unreal.EnumFactory())
    struct = tools.create_asset("ProbeStruct3", folder, unreal.UserDefinedStruct, unreal.StructureFactory())
    report = {}
    for method in [
        "NumEnums",
        "GetNameStringByIndex",
        "SetEnums",
        "SetMetaData",
        "GetDisplayNameTextByIndex",
        "AddNewEnumeratorForUserDefinedEnum",
    ]:
        report["enum_" + method] = try_call(enum, method, 0) if method.startswith("Get") else try_call(enum, method)
    for method in [
        "AddVariable",
        "GetGuid",
        "SetMetaData",
        "GetAuthoredNameForField",
    ]:
        report["struct_" + method] = try_call(struct, method)
    (out / "P02_call_probe.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    unreal.log("[GGBOM-P02] CALL_PROBE_OK")


if __name__ == "__main__":
    main()
