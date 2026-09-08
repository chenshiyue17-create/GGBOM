"""Process launch and fresh-run report checking; process exit alone is never acceptance."""
import json
import os
import subprocess
import uuid
from .paths import PROJECT_ROOT, DATA_DIR, REPORT_DIR, engine_binary
from .config_io import config_lock
from .config_service import enemy_binding_plan
from .data_validation import load_tables, validate_tables


def apply_config():
    try:
        binary = engine_binary(commandlet=True)
        with config_lock(DATA_DIR):
            tables = load_tables(DATA_DIR)
            errors = validate_tables(tables)
            if errors:
                raise ValueError("\n".join(errors))
            plan = enemy_binding_plan(tables["DT_Enemies.json"])
            run_id = uuid.uuid4().hex
            env = dict(os.environ, GGBOM_RUN_ID=run_id)
            command = [str(binary), str(PROJECT_ROOT / "xxxx.uproject"), "-run=pythonscript",
                       f"-script={PROJECT_ROOT / 'Content/Python/apply_data_config.py'}",
                       "-stdout", "-FullStdOutLogOutput", "-unattended", "-nosplash"]
            result = subprocess.run(command, capture_output=True, text=True, timeout=180, env=env)
            path = REPORT_DIR / "config_apply.json"
            report = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
            valid = (result.returncode == 0 and report.get("run_id") == run_id
                     and report.get("config_hash") == plan["config_hash"]
                     and report.get("status") == "APPLIED_EDITOR_DEFAULTS")
            return {"status": "success" if valid else "error", "report": report if report.get("run_id") == run_id else {},
                    "output": (result.stdout + result.stderr)[-6000:], "returncode": result.returncode,
                    "message": "敌人现有数值默认值已保存；运行生效、磁盘重载尚未验证。武器、波次和美术未应用。" if valid
                               else "应用失败或缺少本次运行的匹配回读报告，请检查日志。"}
    except FileNotFoundError as exc:
        return {"status": "blocked", "message": str(exc), "runtime_status": "NOT_RUN"}
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        return {"status": "error", "message": str(exc), "runtime_status": "NOT_RUN"}
