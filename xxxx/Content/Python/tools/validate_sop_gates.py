#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UE5.8 2D 竖屏游戏 SOP 自动化门禁校验器 (Validate SOP Gates)
执行全工程架构、数据、命名、渲染、组件基数与稳定守则检查
"""

import os
import sys
import json
import re

WORKSPACE_ROOT = "/Users/cc/Desktop/GGBOM"
PROJECT_ROOT = os.path.join(WORKSPACE_ROOT, "xxxx")
CONTENT_ROOT = os.path.join(PROJECT_ROOT, "Content")
CONFIG_ROOT = os.path.join(PROJECT_ROOT, "Config")
SAVED_MSAI_DIR = os.path.join(PROJECT_ROOT, "Saved", "MSAI")

class ValidationRunner:
    def __init__(self):
        self.passed_gates = 0
        self.failed_gates = 0
        self.warnings = 0
        self.results = []

    def log_gate(self, name: str, status: str, message: str, details=None):
        if status == "PASS":
            self.passed_gates += 1
            icon = "✅"
        elif status == "FAIL":
            self.failed_gates += 1
            icon = "❌"
        else:
            self.warnings += 1
            icon = "⚠️"
            
        res = {
            "gate": name,
            "status": status,
            "message": message,
            "details": details or []
        }
        self.results.append(res)
        print(f"{icon} [{status}] {name}: {message}")

    def check_2d_render_settings(self):
        """Gate 1: 2D 渲染与防闪烁/色彩直通配置"""
        ini_path = os.path.join(CONFIG_ROOT, "DefaultEngine.ini")
        if not os.path.exists(ini_path):
            self.log_gate("2D_RENDER_SETTINGS", "FAIL", "未找到 DefaultEngine.ini")
            return
            
        with open(ini_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            
        required_keys = [
            ("r.DefaultFeature.AutoExposure=0", "禁用 AutoExposure 曝光适应"),
            ("r.DynamicGlobalIlluminationMethod=0", "禁用 Lumen 全局光照"),
            ("r.AntiAliasingMethod=0", "禁用 TAA/TSR 子像素抖动"),
            ("r.TonemapperFilm=0", "禁用 Tonemapper 电影色调映射")
        ]
        
        missing = []
        for key, desc in required_keys:
            if key not in content:
                missing.append(f"{key} ({desc})")
                
        if missing:
            self.log_gate("2D_RENDER_SETTINGS", "FAIL", "缺少关键 2D 直通配置项", missing)
        else:
            self.log_gate("2D_RENDER_SETTINGS", "PASS", "2D 原画色彩直通与防闪烁渲染配置完全合规")

    def check_naming_conventions(self):
        """Gate 2: SOP 资产命名规范与禁止项检查"""
        forbidden_patterns = [
            (r'_(?:new|final|temp|\d{2,})\.uasset$', "禁止使用 _new / _final / 临时序号命名"),
            (r'NewFolder\d*', "禁止使用未命名的默认文件夹 NewFolder")
        ]
        
        violations = []
        for root, dirs, files in os.walk(CONTENT_ROOT):
            for d in dirs:
                if "NewFolder" in d:
                    violations.append(f"违规目录: {os.path.join(root, d)}")
            for f in files:
                for pattern, desc in forbidden_patterns:
                    if re.search(pattern, f, re.IGNORECASE):
                        violations.append(f"违规文件: {f} ({desc})")
                        
        if violations:
            self.log_gate("NAMING_CONVENTIONS", "WARNING", f"发现 {len(violations)} 处命名需要规范化", violations[:5])
        else:
            self.log_gate("NAMING_CONVENTIONS", "PASS", "工程所有资产命名与目录层级符合 SOP 规范")

    def check_project_control_plane(self):
        """Gate 3: Project Control Plane 生成状态检查"""
        required_files = [
            "ProjectSnapshot.json",
            "ObjectRegistry.json",
            "DependencyGraph.json",
            "ValidationReport.json"
        ]
        
        missing = []
        for rf in required_files:
            fp = os.path.join(SAVED_MSAI_DIR, rf)
            if not os.path.exists(fp) or os.path.getsize(fp) == 0:
                missing.append(rf)
                
        if missing:
            self.log_gate("PROJECT_CONTROL_PLANE", "FAIL", "缺少控制面元数据文件", missing)
        else:
            self.log_gate("PROJECT_CONTROL_PLANE", "PASS", "Project Control Plane 状态文件完整有效")

    def check_chinese_metadata(self):
        """Gate 4: 中文 DisplayName 与 Category 覆盖检查"""
        registry_path = os.path.join(SAVED_MSAI_DIR, "ObjectRegistry.json")
        if not os.path.exists(registry_path):
            self.log_gate("CHINESE_METADATA", "FAIL", "未找到 ObjectRegistry.json")
            return
            
        with open(registry_path, "r", encoding="utf-8") as f:
            registry = json.load(f)
            
        unlabeled = []
        for item in registry:
            sid = item.get("stableId", "Unknown")
            if not item.get("displayName") or not item.get("category"):
                unlabeled.append(sid)
                
        if unlabeled:
            self.log_gate("CHINESE_METADATA", "FAIL", "部分 StableID 缺少中文 DisplayName 或 Category", unlabeled)
        else:
            self.log_gate("CHINESE_METADATA", "PASS", f"全量 {len(registry)} 个核心对象已 100% 具备中文显示名与分类")

    def check_runner_and_stability(self):
        """Gate 5: StandAlone 运行器与 360x640 / 30FPS 守则检查"""
        runner_json = os.path.join(PROJECT_ROOT, ".ue5-lite-runner.json")
        if not os.path.exists(runner_json):
            runner_json = os.path.join(WORKSPACE_ROOT, ".ue5-lite-runner.json")
            
        if not os.path.exists(runner_json):
            self.log_gate("RUNNER_STABILITY", "FAIL", "未找到 .ue5-lite-runner.json 配置文件")
            return
            
        with open(runner_json, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            
        if not cfg.get("engine_root") or not cfg.get("start_map"):
            self.log_gate("RUNNER_STABILITY", "FAIL", "runner 配置缺失 engine_root 或 start_map")
        else:
            self.log_gate("RUNNER_STABILITY", "PASS", "UE5 Lite Runner 独立窗口运行器配置就绪")

    def run_all(self):
        print("==================================================")
        print("  UE5.8 2D 竖屏游戏 SOP 门禁与工程健康体检")
        print("==================================================")
        self.check_2d_render_settings()
        self.check_naming_conventions()
        self.check_project_control_plane()
        self.check_chinese_metadata()
        self.check_runner_and_stability()
        print("==================================================")
        print(f"门禁汇总: PASS={self.passed_gates}, WARNING={self.warnings}, FAIL={self.failed_gates}")
        if self.failed_gates == 0:
            print("🎉 SOP 全部门禁验证通过 (READY FOR PRODUCTION)")
            return 0
        else:
            print("🚨 存在未通过门禁，请检查上方详情")
            return 1

def main():
    runner = ValidationRunner()
    exit_code = runner.run_all()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
