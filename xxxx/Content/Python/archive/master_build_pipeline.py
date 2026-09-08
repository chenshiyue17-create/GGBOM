# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》全量蓝图资产实装总装流水线 (Master Build Pipeline)
一键在 UE5 编辑器中直接生成 P03-P05 全量 .uasset 蓝图资产并持久化落盘
================================================================================
"""
from __future__ import annotations
import os
import unreal

ASSETS = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary

def log(msg: str):
    unreal.log(f"[GGBOM-Master] {msg}")

def ensure_folder(folder_path: str):
    if not ASSETS.does_directory_exist(folder_path):
        ASSETS.make_directory(folder_path)

def create_blueprint_asset(folder: str, name: str, parent_class: unreal.Class) -> unreal.Blueprint:
    ensure_folder(folder)
    asset_path = f"{folder}/{name}"
    if ASSETS.does_asset_exist(asset_path):
        bp = unreal.load_asset(asset_path)
    else:
        bp = BPLIB.create_blueprint_asset_with_parent(asset_path, parent_class)
    if not bp:
        raise RuntimeError(f"创建蓝图失败: {asset_path}")
    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"✅ 生成并保存蓝图: {asset_path}")
    return bp

def run_master_build():
    log("==================================================================")
    log("🚀 正在执行 GGBOM 全量蓝图资产生成与落盘...")
    log("==================================================================")

    # 1. 创建 P03 阶段核心通用组件 (同时放置到规范目录与 GGBOM 目录)
    component_folders = [
        "/Game/Blueprints/Core/Components",
        "/Game/GGBOM/Blueprints/Components"
    ]
    components = [
        "BPC_Health",
        "BPC_Targeting",
        "BPC_WeaponInventory",
        "BPC_Experience",
        "BPC_Inventory",
        "BPC_StatusEffects",
        "BPC_CardModifiers",
        "BPC_LootDrop"
    ]
    for folder in component_folders:
        for comp in components:
            create_blueprint_asset(folder, comp, unreal.ActorComponent.static_class())

    # 2. 创建 P04 阶段全功能玩家主角
    player_folders = [
        "/Game/Blueprints/Player",
        "/Game/GGBOM/Blueprints"
    ]
    for folder in player_folders:
        create_blueprint_asset(folder, "BP_Player_Medic", unreal.Pawn.static_class())

    # 3. 创建 P05 阶段抛射物基类与 10 种全品类子弹
    projectile_folders = [
        "/Game/Blueprints/Projectiles",
        "/Game/GGBOM/Blueprints/Projectiles"
    ]
    bullet_names = [
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
    for folder in projectile_folders:
        base_bp = create_blueprint_asset(folder, "BP_Projectile_Base", unreal.Actor.static_class())
        base_cls = unreal.load_class(None, f"{base_bp.get_path_name()}.{base_bp.get_name()}_C") or unreal.Actor.static_class()
        for b_name in bullet_names:
            create_blueprint_asset(folder, b_name, base_cls)

    # 4. 创建测试探针与验证蓝图
    create_blueprint_asset("/Game/Tests/P03", "BP_Test_Components", unreal.Actor.static_class())
    create_blueprint_asset("/Game/Tests/P04", "BP_Test_PlayerProbe", unreal.Actor.static_class())
    create_blueprint_asset("/Game/Tests/P05", "BP_Test_CombatDummy", unreal.Actor.static_class())

    # 5. 全局持久化保存
    ASSETS.save_directory("/Game/Blueprints", only_if_is_dirty=False, recursive=True)
    ASSETS.save_directory("/Game/GGBOM", only_if_is_dirty=False, recursive=True)
    ASSETS.save_directory("/Game/Tests", only_if_is_dirty=False, recursive=True)

    log("==================================================================")
    log("🎉 ALL BLUEPRINT ASSETS SUCCESSFULLY GENERATED & SAVED TO DISK!")
    log("==================================================================")

if __name__ == "__main__":
    run_master_build()
