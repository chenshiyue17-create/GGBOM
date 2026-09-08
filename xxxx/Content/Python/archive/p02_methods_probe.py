from __future__ import annotations

import inspect
import json
from pathlib import Path

import unreal


def sig(obj, name):
    fn = getattr(obj, name, None)
    if not fn:
        return None
    try:
        return str(inspect.signature(fn))
    except Exception as exc:
        return "ERR " + str(exc)


def main() -> None:
    root = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
    out = root / "output"
    report = {}
    targets = {
        "BlueprintEditorLibrary": [
            "add_member_variable",
            "change_member_variable_type",
            "add_function_graph",
            "add_function_override",
            "list_member_variable_names",
            "get_member_variable_type",
            "get_struct_type",
        ],
        "DataTableFunctionLibrary": [],
        "DataTable": [],
        "KismetSystemLibrary": ["print_string"],
    }
    for cls_name, method_names in targets.items():
        obj = getattr(unreal, cls_name, None)
        if not obj:
            report[cls_name] = None
            continue
        names = method_names or [n for n in dir(obj) if not n.startswith("_")]
        report[cls_name] = {n: sig(obj, n) for n in names if any(k in n.lower() for k in ["row", "table", "member", "struct", "function", "print"])}
    for needle in ["Structure", "Struct", "Enum", "Kismet"]:
        report["global_" + needle] = sorted([n for n in dir(unreal) if needle in n])[:300]
    (out / "P02_methods_probe.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    unreal.log("[GGBOM-P02] METHODS_PROBE_OK")


if __name__ == "__main__":
    main()
