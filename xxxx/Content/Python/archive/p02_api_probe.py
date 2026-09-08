from __future__ import annotations

import json
from pathlib import Path

import unreal


def main() -> None:
    root = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
    out = root / "output"
    out.mkdir(parents=True, exist_ok=True)
    names = dir(unreal)
    report = {
        "enum_related": sorted([n for n in names if "Enum" in n])[:200],
        "struct_related": sorted([n for n in names if "Struct" in n])[:200],
        "data_table_related": sorted([n for n in names if "DataTable" in n])[:200],
        "blueprint_factory": hasattr(unreal, "BlueprintFactory"),
        "interface_class": hasattr(unreal, "Interface"),
        "blueprint_type": [n for n in names if n == "BlueprintType"],
        "subsystems": sorted([n for n in names if n.endswith("Subsystem") and ("Enum" in n or "Struct" in n or "DataTable" in n or "Asset" in n)])[:200],
    }
    for cls in ["UserDefinedEnumFactory", "UserDefinedStructFactory", "DataTableFactory", "BlueprintFactory"]:
        obj = getattr(unreal, cls, None)
        report[cls] = bool(obj)
        if obj:
            try:
                inst = obj()
                report[cls + "_props"] = [str(p) for p in inst.get_editor_property_names()] if hasattr(inst, "get_editor_property_names") else []
            except Exception as exc:
                report[cls + "_error"] = str(exc)
    (out / "P02_api_probe.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    unreal.log("[GGBOM-P02] API_PROBE_OK")


if __name__ == "__main__":
    main()
