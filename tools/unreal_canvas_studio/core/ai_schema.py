# -*- coding: utf-8 -*-
"""
Unreal Canvas Studio - AI Schema 与元数据自省引擎 (AI Schema Engine)
功能：生成目标工程全部 DataTable 的 JSON Schema 与 Markdown Codebook，供 AI Agent 学习。
"""

import json
from pathlib import Path

class AISchemaEngine:
    def __init__(self, project_adapter, property_engine):
        self.adapter = project_adapter
        self.prop_engine = property_engine

    def dump_project_schema(self):
        """推导并导出全工程统一 JSON Schema"""
        tables = self.adapter.list_datatables()
        schema_doc = {
            "projectName": self.adapter.project_name,
            "projectPath": str(self.adapter.project_path),
            "tables": {}
        }
        for t in tables:
            stem = t["stem"]
            custom_fields = self.prop_engine.get_custom_schema(stem)
            schema_doc["tables"][stem] = {
                "file": t["filename"],
                "format": t["format"],
                "customFields": custom_fields
            }
        return schema_doc

    def dump_markdown_codebook(self):
        """导出人类与 AI 均可秒懂的 Markdown 数据字典"""
        schema = self.dump_project_schema()
        lines = [
            f"# 《{schema['projectName']}》UE5 蓝图数据字典与 Schema 说明书",
            f"> 挂载路径: `{schema['projectPath']}`\n",
            "## 1. 数据表索引清单\n"
        ]
        for t_name, info in schema["tables"].items():
            lines.append(f"- **`{t_name}`** (`{info['file']}`): 自定义扩展字段 {len(info['customFields'])} 个")
            if info["customFields"]:
                lines.append("  | 字段名 (Key) | 中文名 | 类型 | 默认值 | 作用域 | 说明 |")
                lines.append("  | :--- | :--- | :--- | :--- | :--- | :--- |")
                for k, f in info["customFields"].items():
                    lines.append(f"  | `{k}` | {f['displayName']} | `{f['type']}` | `{f['defaultValue']}` | {f['scope']} | {f['tooltip']} |")
            lines.append("")
        return "\n".join(lines)
