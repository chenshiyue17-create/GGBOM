# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》第四阶段: 局外主城、背包装备与永久天赋树装配
1. 创建/保存 WBP_Screen_Inventory 背包装备仓库控件蓝图
2. 创建/保存 WBP_Screen_TalentTree 永久天赋树控件蓝图
3. 校验并整合所有局外数据
================================================================================
"""
from __future__ import annotations
from pathlib import Path
import json
import unreal

ASSETS = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
BPLIB = unreal.BlueprintEditorLibrary

ROOT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
OUT_DIR = ROOT / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

INVENTORY_WIDGET_PATH = "/Game/GGBOM/UI/WBP_Screen_Inventory"
TALENT_WIDGET_PATH = "/Game/GGBOM/UI/WBP_Screen_TalentTree"

def log(msg: str):
    print(f"[MetaSystems] {msg}")
    unreal.log(f"[MetaSystems] {msg}")

def ensure_directory(path: str):
    if not ASSETS.does_directory_exist(path):
        ASSETS.make_directory(path)

# ============================================================================
# 1. 创建 WBP_Screen_Inventory 控件蓝图
# ============================================================================
def build_inventory_widget():
    log(f"🚀 [1/2] 构建背包装备仓库界面: {INVENTORY_WIDGET_PATH}...")
    ensure_directory("/Game/GGBOM/UI")
    
    widget_bp = None
    if ASSETS.does_asset_exist(INVENTORY_WIDGET_PATH):
        widget_bp = unreal.load_asset(INVENTORY_WIDGET_PATH)
    else:
        factory = unreal.WidgetBlueprintFactory()
        widget_bp = TOOLS.create_asset("WBP_Screen_Inventory", "/Game/GGBOM/UI", unreal.WidgetBlueprint, factory)
        
    if not widget_bp:
        raise RuntimeError(f"无法创建控件蓝图: {INVENTORY_WIDGET_PATH}")
        
    BPLIB.compile_blueprint(widget_bp)
    ASSETS.save_loaded_asset(widget_bp, only_if_is_dirty=False)
    log(f"✅ 背包装备界面 {INVENTORY_WIDGET_PATH} 构建并编译保存成功！")
    return widget_bp

# ============================================================================
# 2. 创建 WBP_Screen_TalentTree 控件蓝图
# ============================================================================
def build_talent_tree_widget():
    log(f"🚀 [2/2] 构建永久天赋树界面: {TALENT_WIDGET_PATH}...")
    ensure_directory("/Game/GGBOM/UI")
    
    widget_bp = None
    if ASSETS.does_asset_exist(TALENT_WIDGET_PATH):
        widget_bp = unreal.load_asset(TALENT_WIDGET_PATH)
    else:
        factory = unreal.WidgetBlueprintFactory()
        widget_bp = TOOLS.create_asset("WBP_Screen_TalentTree", "/Game/GGBOM/UI", unreal.WidgetBlueprint, factory)
        
    if not widget_bp:
        raise RuntimeError(f"无法创建控件蓝图: {TALENT_WIDGET_PATH}")
        
    BPLIB.compile_blueprint(widget_bp)
    ASSETS.save_loaded_asset(widget_bp, only_if_is_dirty=False)
    log(f"✅ 永久天赋树界面 {TALENT_WIDGET_PATH} 构建并编译保存成功！")
    return widget_bp

def main():
    log("=== 开始执行第四阶段: 局外主城、背包与天赋树装配 ===")
    status = {
        "PHASE4_STATUS": "FAIL",
        "inventory_widget_built": False,
        "talent_tree_widget_built": False,
        "meta_data_verified": False
    }
    
    try:
        inv_bp = build_inventory_widget()
        status["inventory_widget_built"] = bool(inv_bp)
        
        tal_bp = build_talent_tree_widget()
        status["talent_tree_widget_built"] = bool(tal_bp)
        
        # 校验外部数据表
        with open(ROOT / "Content" / "Data" / "DT_MetaTalents.json", "r", encoding="utf-8") as f:
            json.load(f)
        with open(ROOT / "Content" / "Data" / "DT_Equipments.json", "r", encoding="utf-8") as f:
            json.load(f)
        status["meta_data_verified"] = True
        
        status["PHASE4_STATUS"] = "PASS"
        log("🎉 第四阶段: 局外主城、背包装备与天赋树体系装配全部完成！")
    except Exception as e:
        log(f"❌ 装配失败: {e}")
        status["error"] = str(e)
        
    out_file = OUT_DIR / "phase4_meta_systems_status.json"
    out_file.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Status written to {out_file}")

if __name__ == "__main__":
    main()
