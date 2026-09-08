"""Apply existing enemy numeric defaults. All gameplay and disk-reload gates remain NOT_RUN."""
import json
import os
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools"))
from ggbom.paths import DATA_DIR, REPORT_DIR
from ggbom.config_io import atomic_json
from ggbom.config_service import enemy_binding_plan
from ggbom.data_validation import load_tables, validate_tables
from ggbom.editor_apply import apply_enemy_defaults


def main():
    import unreal
    run_id = os.environ.get("GGBOM_RUN_ID", "manual")
    report_file = REPORT_DIR / "config_apply.json"
    report = {"status": "FAIL", "run_id": run_id, "runtime_status": "NOT_RUN"}
    try:
        active_project = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())).resolve()
        if active_project != (REPO / "xxxx").resolve():
            raise RuntimeError(f"Wrong active Unreal project: {active_project}")
        tables = load_tables(DATA_DIR)
        errors = validate_tables(tables)
        if errors:
            raise ValueError("\n".join(errors))
        plan = enemy_binding_plan(tables["DT_Enemies.json"])
        report.update(apply_enemy_defaults(unreal, plan))
        # CDO readback/save does not establish runtime data consumption.
        atomic_json(report_file, report)
        unreal.log(json.dumps(report, ensure_ascii=False))
    except Exception as exc:
        report.update(status="FAIL", error=str(exc))
        atomic_json(report_file, report)
        raise


if __name__ == "__main__":
    main()
