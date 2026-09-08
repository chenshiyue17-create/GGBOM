#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unreal Canvas Studio - 统一 CLI 命令行工具 (AI-First CLI)
使用方法：
  python3 cli.py info
  python3 cli.py schema
  python3 cli.py slice --image <path> --rows 2 --cols 4
  python3 cli.py remove-black --image <path>
  python3 cli.py custom-prop add --table DT_Weapons --key CritRate --type float --name "暴击率"
"""

import sys
import json
import argparse
from pathlib import Path

CURRENT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(CURRENT_DIR))

from core.project_adapter import UEProjectAdapter
from core.datatable_engine import DataTableEngine
from core.property_engine import PropertyEngine
from core.asset_pipeline import AssetPipelineEngine
from core.hud_engine import HUDEngine
from core.ai_schema import AISchemaEngine

def get_context(project_path):
    adapter = UEProjectAdapter(project_path)
    dt_engine = DataTableEngine(adapter)
    prop_engine = PropertyEngine(adapter)
    asset_engine = AssetPipelineEngine(adapter)
    hud_engine = HUDEngine(adapter)
    schema_engine = AISchemaEngine(adapter, prop_engine)
    return adapter, dt_engine, prop_engine, asset_engine, hud_engine, schema_engine

def main():
    parser = argparse.ArgumentParser(description="Unreal Canvas Studio CLI")
    parser.add_argument("--project", "-p", default="/Users/cc/Desktop/GGBOM/xxxx", help="目标 UE 工程路径")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # 1. info
    subparsers.add_parser("info", help="查看当前挂载工程概览")

    # 2. schema
    schema_parser = subparsers.add_parser("schema", help="输出全工程数据字典与 Schema")
    schema_parser.add_argument("--format", choices=["json", "markdown"], default="json")

    # 2.5 scaffold (对新工程一键生成标准核心表)
    scaffold_parser = subparsers.add_parser("scaffold", help="为新工程一键生成缺失的 UE5 标准数据表")
    scaffold_parser.add_argument("--tables", nargs="*", default=None, help="指定生成的表名 (留空默认生成全部核心表)")

    # 3. slice
    slice_parser = subparsers.add_parser("slice", help="对指定源图片执行网格切片")
    slice_parser.add_argument("--image", required=True, help="源图物理绝对路径")
    slice_parser.add_argument("--rows", type=int, default=2)
    slice_parser.add_argument("--cols", type=int, default=4)

    # 4. remove-black
    rb_parser = subparsers.add_parser("remove-black", help="智能去除黑底生成透明 PNG")
    rb_parser.add_argument("--image", required=True)
    rb_parser.add_argument("--threshold", type=int, default=25)

    # 5. custom-prop
    cp_parser = subparsers.add_parser("custom-prop", help="管理动态自定义属性")
    cp_sub = cp_parser.add_subparsers(dest="cp_action")
    cp_add = cp_sub.add_parser("add")
    cp_add.add_argument("--table", required=True)
    cp_add.add_argument("--key", required=True)
    cp_add.add_argument("--type", required=True)
    cp_add.add_argument("--name", required=True)
    cp_add.add_argument("--default", default=None)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    adapter, dt_engine, prop_engine, asset_engine, hud_engine, schema_engine = get_context(args.project)

    if args.command == "info":
        print(json.dumps(adapter.get_project_summary(), ensure_ascii=False, indent=2))
    elif args.command == "schema":
        if args.format == "json":
            print(json.dumps(schema_engine.dump_project_schema(), ensure_ascii=False, indent=2))
        else:
            print(schema_engine.dump_markdown_codebook())
    elif args.command == "scaffold":
        res = dt_engine.scaffold_missing_tables(args.tables)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    elif args.command == "slice":
        res = asset_engine.slice_grid(args.image, args.rows, args.cols)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    elif args.command == "remove-black":
        target = asset_engine.remove_black_background(args.image, args.threshold)
        print(f"✅ 去黑底完成: {target}")
    elif args.command == "custom-prop" and args.cp_action == "add":
        prop_def = {
            "displayName": args.name,
            "type": args.type,
            "defaultValue": args.default
        }
        res = prop_engine.register_property(args.table, args.key, prop_def)
        print(f"✅ 属性已注入: {res}")

if __name__ == "__main__":
    main()
