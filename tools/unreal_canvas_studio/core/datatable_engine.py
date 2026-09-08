# -*- coding: utf-8 -*-
"""
Unreal Canvas Studio - 通用 DataTable 引擎 (DataTable Engine)
功能：标准 UE5 DataTable JSON/CSV 读写、草稿沙盒隔离、原子写盘、.bak 自动备份与 Diff 审计守卫。
"""

import os
import csv
import json
import shutil
import time
from pathlib import Path
from .datatable_templates import STANDARD_TEMPLATES
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from ggbom.config_io import diff_rows, atomic_json

class DataTableEngine:
    def __init__(self, project_adapter):
        self.adapter = project_adapter
        self.audit_log_path = None
        if self.adapter.data_dir:
            self.audit_log_path = self.adapter.data_dir / "audit_log.json"

    def scaffold_missing_tables(self, tables=None):
        """对全新空白 UE5 项目自愈生成缺失的标准核心数据表"""
        target_tables = tables or list(STANDARD_TEMPLATES.keys())
        created = []
        data_dir = self.adapter.data_dir
        if not data_dir:
            raise RuntimeError("未定位到有效的数据表目录")
        data_dir.mkdir(parents=True, exist_ok=True)

        for t_name in target_tables:
            if t_name not in STANDARD_TEMPLATES:
                continue
            json_file = data_dir / f"{t_name}.json"
            if not json_file.exists():
                template = STANDARD_TEMPLATES[t_name]
                with open(json_file, "w", encoding="utf-8") as f:
                    json.dump(template["defaultRows"], f, ensure_ascii=False, indent=2)
                created.append(t_name)
                print(f"✨ [Scaffold] 已为新项目自愈生成标准数据表: {t_name}.json ({len(template['defaultRows'])} 条初始行)")

        return {
            "success": True,
            "createdTables": created,
            "totalAvailable": len(self.adapter.list_datatables())
        }

    def load_table(self, table_name):
        """加载指定数据表，返回 (data_list, format_type)"""
        data_dir = self.adapter.data_dir
        if not data_dir or not data_dir.exists():
            return [], "none"

        # 尝试匹配 json
        json_file = data_dir / f"{table_name}.json"
        if json_file.exists():
            with open(json_file, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    return data, "json"
                except Exception as e:
                    print(f"❌ 读取 {json_file} 失败: {e}")
                    return [], "json"

        # 尝试匹配 csv
        csv_file = data_dir / f"{table_name}.csv"
        if csv_file.exists():
            rows = []
            with open(csv_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    rows.append(r)
            return rows, "csv"

        return [], "none"

    def save_table(self, table_name, rows_data, format_type="json"):
        """原子化保存数据表，生成 .bak 备份与 Diff 审计日志"""
        data_dir = self.adapter.data_dir
        if not data_dir:
            raise RuntimeError("未配置数据表目录")

        if Path(table_name).name != table_name or "\\" in table_name or format_type not in ("json", "csv"):
            raise ValueError("Invalid table name or format")
        if format_type == "csv" and not rows_data:
            raise ValueError("Empty CSV requires an explicit column schema")

        target_file = data_dir / f"{table_name}.{format_type}"
        bak_file = data_dir / f"{table_name}.{format_type}.bak"

        # 1. 自动备份
        if target_file.exists():
            shutil.copy2(target_file, bak_file)

        # 2. 计算简要 Diff
        old_rows, _ = self.load_table(table_name)
        diff_summary = self._compute_diff_summary(old_rows, rows_data)

        # 3. 原子写入
        temp_file = data_dir / f"{table_name}.{format_type}.tmp"
        if format_type == "json":
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(rows_data, f, ensure_ascii=False, indent=2, allow_nan=False)
        elif format_type == "csv":
            if rows_data:
                fieldnames = list(rows_data[0].keys())
                with open(temp_file, "w", encoding="utf-8", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(rows_data)
        
        # 替换正式文件
        os.replace(temp_file, target_file)

        # 4. 写入审计日志
        self._record_audit(table_name, diff_summary)

        return {
            "success": True,
            "table": table_name,
            "rowsCount": len(rows_data),
            "backup": str(bak_file),
            "diffSummary": diff_summary
        }

    def _compute_diff_summary(self, old_rows, new_rows):
        """计算行级变更摘要"""
        return diff_rows(old_rows, new_rows)

    def _record_audit(self, table_name, diff_summary):
        """写入本地审计日志"""
        if not self.audit_log_path:
            return
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "table": table_name,
            "diff": diff_summary
        }
        history = []
        if self.audit_log_path.exists():
            try:
                with open(self.audit_log_path, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                history = []
        history.insert(0, log_entry)
        # 最多保留 100 条审计记录
        history = history[:100]
        try:
            with open(self.audit_log_path, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 写入审计日志失败: {e}")

