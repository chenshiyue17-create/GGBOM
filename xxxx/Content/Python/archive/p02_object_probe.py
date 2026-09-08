from __future__ import annotations

import json
from pathlib import Path

import unreal


def props(obj):
    found = []
    for name in dir(obj):
        if name.startswith("_"):
            continue
        try:
            obj.get_editor_property(name)
            found.append(name)
        except Exception:
            pass
    return sorted(found)


def main() -> None:
    root = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
    out = root / "output"
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    assets = unreal.EditorAssetLibrary
    folder = "/Game/Tests/P02ObjectProbe"
    if assets.does_directory_exist(folder):
        assets.delete_directory(folder)
    assets.make_directory(folder)
    enum = tools.create_asset("ProbeEnum2", folder, unreal.UserDefinedEnum, unreal.EnumFactory())
    struct = tools.create_asset("ProbeStruct2", folder, unreal.UserDefinedStruct, unreal.StructureFactory())
    report = {
        "enum_dir": sorted([n for n in dir(enum) if not n.startswith("_")]),
        "struct_dir": sorted([n for n in dir(struct) if not n.startswith("_")]),
        "enum_props": props(enum),
        "struct_props": props(struct),
        "calls": {},
    }
    for call in [
        ("enum_num", lambda: enum.get_num_enum_entries()),
        ("enum_names", lambda: [enum.get_name_string_by_index(i) for i in range(enum.get_num_enum_entries())]),
        ("enum_display", lambda: [str(enum.get_display_name_text_by_index(i)) for i in range(enum.get_num_enum_entries())]),
        ("struct_fields", lambda: unreal.BlueprintEditorLibrary.list_member_variable_names(struct)),
        ("struct_type", lambda: str(unreal.BlueprintEditorLibrary.get_struct_type(struct))),
    ]:
        name, fn = call
        try:
            report["calls"][name] = fn()
        except Exception as exc:
            report["calls"][name] = "ERR " + str(exc)
    (out / "P02_object_probe.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    unreal.log("[GGBOM-P02] OBJECT_PROBE_OK")


if __name__ == "__main__":
    main()
