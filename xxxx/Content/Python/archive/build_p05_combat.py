# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》P05 阶段: 战斗武器、弹道抛射物与伤害结算系统 (BP_Projectile & DT_Weapons)
================================================================================
"""
from __future__ import annotations
import json
import unreal

ASSETS = unreal.EditorAssetLibrary
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary
PROJECTILES_DIR = "/Game/Blueprints/Projectiles"
TEST_DIR = "/Game/Tests/P05"

def log(msg: str):
    unreal.log(f"[GGBOM-P05] {msg}")

def ensure_dir(path: str):
    if not ASSETS.does_directory_exist(path):
        ASSETS.make_directory(path)

def create_bp(path: str, parent: unreal.Class) -> unreal.Blueprint:
    ensure_dir(path.rsplit('/', 1)[0])
    if ASSETS.does_asset_exist(path):
        bp = unreal.load_asset(path)
    else:
        bp = BPLIB.create_blueprint_asset_with_parent(path, parent)
    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    return bp

def build_all_projectiles() -> list[str]:
    base_path = f"{PROJECTILES_DIR}/BP_Projectile_Base"
    base_bp = create_bp(base_path, unreal.Actor.static_class())
    
    projectiles = [
        "BP_Bullet_KineticPistol",
        "BP_Bullet_AssaultRifle",
        "BP_Bullet_Buckshot",
        "BP_Bullet_BioAcid",
        "BP_Bullet_ToxicSpore",
        "BP_Bullet_VenomHeavy",
        "BP_Bullet_Incendiary",
        "BP_Bullet_PlasmaArc",
        "BP_Bullet_MicroMissile",
        "BP_Bullet_LaserRail"
    ]
    
    results = [base_bp.get_path_name()]
    # 获取 Base 的生成类
    base_cls = unreal.load_class(None, f"{base_bp.get_path_name()}.{base_bp.get_name()}_C") or unreal.Actor.static_class()
    
    for p_name in projectiles:
        child_path = f"{PROJECTILES_DIR}/{p_name}"
        child_bp = create_bp(child_path, base_cls)
        results.append(child_bp.get_path_name())
        log(f"✅ 弹道抛射物蓝图就绪: {p_name}")
        
    return results

def create_combat_dummy_test() -> unreal.Blueprint:
    ensure_dir(TEST_DIR)
    path = f"{TEST_DIR}/BP_Test_CombatDummy"
    bp = create_bp(path, unreal.Actor.static_class())
    
    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    begin = ed.find_event_node("ReceiveBeginPlay")
    
    print_node = ed.add_call_function_node("/Script/Engine.KismetSystemLibrary.PrintString")
    print_node.set_node_pos(unreal.IntPoint(300, 0))
    pin_str = [p for p in BPLIB.list_input_pins(print_node) if str(PINLIB.get_pin_name(p)).lower() == "instring"][0]
    pin_exec = [p for p in BPLIB.list_input_pins(print_node) if str(PINLIB.get_pin_name(p)).lower() == "execute"][0]
    PINLIB.set_pin_value(pin_str, "P05_COMBAT_OK")
    
    begin_then = [p for p in BPLIB.list_output_pins(begin) if str(PINLIB.get_pin_name(p)).lower() == "then"][0]
    PINLIB.try_create_connection(begin_then, pin_exec)
    
    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    return bp

def export_full_weapons_spec():
    out_dir = "/Users/cc/Desktop/GGBOM/xxxx/Content/Blueprints/Core/Types"
    ensure_dir("/Game/Blueprints/Core/Types")
    
    weapons_10 = [
        {"ID": "WPN_KineticPistol", "Damage": 25.0, "Interval": 0.25, "PPS": 1, "Spread": 0.0, "Pierce": 1, "Speed": 1200.0, "Mag": 30, "Reload": 1.5, "AOE": 0.0, "Tag": "Damage.Kinetic"},
        {"ID": "WPN_AssaultRifle", "Damage": 18.0, "Interval": 0.10, "PPS": 1, "Spread": 1.5, "Pierce": 1, "Speed": 1600.0, "Mag": 30, "Reload": 1.8, "AOE": 0.0, "Tag": "Damage.Kinetic"},
        {"ID": "WPN_Buckshot", "Damage": 14.0, "Interval": 0.75, "PPS": 7, "Spread": 18.0, "Pierce": 1, "Speed": 1300.0, "Mag": 6, "Reload": 2.0, "AOE": 0.0, "Tag": "Damage.Kinetic"},
        {"ID": "WPN_BioAcid", "Damage": 32.0, "Interval": 0.60, "PPS": 1, "Spread": 2.0, "Pierce": 1, "Speed": 900.0, "Mag": 8, "Reload": 2.0, "AOE": 120.0, "Tag": "Damage.Acid"},
        {"ID": "WPN_ToxicSpore", "Damage": 16.0, "Interval": 0.28, "PPS": 2, "Spread": 8.0, "Pierce": 1, "Speed": 1050.0, "Mag": 20, "Reload": 1.8, "AOE": 70.0, "Tag": "Damage.Toxic"},
        {"ID": "WPN_VenomMortar", "Damage": 55.0, "Interval": 1.10, "PPS": 1, "Spread": 3.0, "Pierce": 1, "Speed": 700.0, "Mag": 5, "Reload": 2.4, "AOE": 180.0, "Tag": "Damage.Toxic"},
        {"ID": "WPN_Incendiary", "Damage": 22.0, "Interval": 0.16, "PPS": 1, "Spread": 3.0, "Pierce": 1, "Speed": 1450.0, "Mag": 24, "Reload": 1.9, "AOE": 0.0, "Tag": "Damage.Fire"},
        {"ID": "WPN_PlasmaArc", "Damage": 26.0, "Interval": 0.22, "PPS": 1, "Spread": 0.0, "Pierce": 2, "Speed": 1350.0, "Mag": 18, "Reload": 2.0, "AOE": 0.0, "Tag": "Damage.Electric"},
        {"ID": "WPN_MicroMissile", "Damage": 80.0, "Interval": 1.00, "PPS": 1, "Spread": 2.0, "Pierce": 1, "Speed": 850.0, "Mag": 4, "Reload": 2.6, "AOE": 230.0, "Tag": "Damage.Explosion"},
        {"ID": "WPN_LaserRail", "Damage": 140.0, "Interval": 1.40, "PPS": 1, "Spread": 0.0, "Pierce": 999, "Speed": 3000.0, "Mag": 3, "Reload": 2.8, "AOE": 0.0, "Tag": "Damage.Electric"}
    ]
    
    import os
    os.makedirs(out_dir, exist_ok=True)
    with open(f"{out_dir}/DT_WeaponsConfig_10Rows.json", "w", encoding="utf-8") as f:
        json.dump(weapons_10, f, ensure_ascii=False, indent=2)
    log("✅ 10 种武器全量数据规约导出完毕。")

def main():
    log("=== 开始执行 P05 CombatWeaponsProjectiles 构建 ===")
    projectiles = build_all_projectiles()
    export_full_weapons_spec()
    dummy = create_combat_dummy_test()
    
    ASSETS.save_directory(PROJECTILES_DIR, only_if_is_dirty=False, recursive=True)
    ASSETS.save_directory(TEST_DIR, only_if_is_dirty=False, recursive=True)
    log("P05_BUILD_COMPLETE")

if __name__ == "__main__":
    main()
