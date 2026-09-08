from __future__ import annotations

import json
from pathlib import Path

import unreal


def serial(obj):
    result = {}
    for name in sorted(dir(obj)):
        if name.startswith("_"):
            continue
        if any(k in name.lower() for k in ["enum", "struct", "var", "member", "function", "blueprint", "interface", "row", "table", "property", "pin"]):
            result[name] = str(getattr(obj, name, None))
    return result


def main() -> None:
    root = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
    out = root / "output"
    out.mkdir(parents=True, exist_ok=True)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    assets = unreal.EditorAssetLibrary
    folder = "/Game/Tests/P02Probe"
    if assets.does_directory_exist(folder):
        assets.delete_directory(folder)
    assets.make_directory(folder)
    report = {
        "BlueprintEditorLibrary": serial(unreal.BlueprintEditorLibrary),
        "BlueprintFactory": serial(unreal.BlueprintFactory()),
        "DataTableFactory": serial(unreal.DataTableFactory()),
    }
    for cls_name, asset_cls, factory_cls in [
        ("UserDefinedEnum", unreal.UserDefinedEnum, unreal.EnumFactory),
        ("UserDefinedStruct", unreal.UserDefinedStruct, unreal.StructureFactory),
    ]:
        try:
            obj = tools.create_asset("Probe_" + cls_name, folder, asset_cls, factory_cls())
            report[cls_name] = {
                "asset": obj.get_path_name() if obj else None,
                "methods": serial(obj) if obj else {},
            }
            if obj:
                report[cls_name]["editor_props"] = []
                for n in dir(obj):
                    if n.startswith("_"):
                        continue
                    try:
                        obj.get_editor_property(n)
                        report[cls_name]["editor_props"].append(n)
                    except Exception:
                        pass
        except Exception as exc:
            report[cls_name] = {"error": str(exc)}
    (out / "P02_deep_probe.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    unreal.log("[GGBOM-P02] DEEP_PROBE_OK")


if __name__ == "__main__":
    main()
