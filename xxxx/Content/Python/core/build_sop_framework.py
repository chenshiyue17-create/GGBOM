# -*- coding: utf-8 -*-
"""
UE5.8 2D 竖屏游戏 SOP 标准 Framework & Definition 构建模块
构建标准蓝图父类、组件体系与 Data-Only 配置，符合 SOP 4层架构。
"""
from __future__ import annotations
import os
import sys

try:
    import unreal
    IN_UNREAL = True
except ImportError:
    IN_UNREAL = False

if IN_UNREAL:
    ASSETS = unreal.EditorAssetLibrary
    TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
    BPLIB = unreal.BlueprintEditorLibrary
    PINLIB = unreal.BlueprintGraphPinLibrary

def log(msg: str):
    if IN_UNREAL:
        unreal.log(f"[SOP-FRAMEWORK] {msg}")
    else:
        print(f"[SOP-FRAMEWORK] {msg}")

def ensure_dir(path: str):
    if IN_UNREAL:
        if not ASSETS.does_directory_exist(path):
            ASSETS.make_directory(path)

def create_or_get_blueprint(path: str, parent_class, is_actor=True):
    if not IN_UNREAL:
        return None
    directory = os.path.dirname(path)
    ensure_dir(directory)
    
    if ASSETS.does_asset_exist(path):
        bp = unreal.load_asset(path)
        log(f"找到既有蓝图资产 (UPDATE 模式): {path}")
    else:
        bp = BPLIB.create_blueprint_asset_with_parent(path, parent_class)
        log(f"创建新蓝图资产: {path}")
        
    if bp:
        BPLIB.compile_blueprint(bp)
        ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    return bp

def build_core_hierarchy():
    if not IN_UNREAL:
        log("不在 Unreal Engine 运行环境中，跳过蓝图二进制生成。")
        return
        
    log("=== 1. 建立 Framework 核心基类与组件 ===")
    
    # 1. 通用组件
    components = [
        ("BP_CMP_Stats", unreal.ActorComponent.static_class()),
        ("BP_CMP_Animation2D", unreal.ActorComponent.static_class()),
        ("BP_CMP_WeaponHost", unreal.ActorComponent.static_class()),
        ("BP_CMP_AutoAim", unreal.ActorComponent.static_class()),
        ("BP_CMP_AI", unreal.ActorComponent.static_class())
    ]
    
    for name, p_cls in components:
        bp_path = f"/Game/Blueprints/Core/Components/{name}"
        create_or_get_blueprint(bp_path, p_cls)
        
    # 2. 角色基类体系
    # Character Base
    bp_chr_base = create_or_get_blueprint("/Game/Blueprints/Characters/BP_CHR_Base", unreal.Pawn.static_class())
    
    # Player Base
    if bp_chr_base:
        bp_player_base = create_or_get_blueprint("/Game/Blueprints/Characters/BP_CHR_PlayerBase", bp_chr_base.generated_class())
    else:
        bp_player_base = create_or_get_blueprint("/Game/Blueprints/Characters/BP_CHR_PlayerBase", unreal.Pawn.static_class())
        
    # Enemy Base
    if bp_chr_base:
        bp_enemy_base = create_or_get_blueprint("/Game/Blueprints/Characters/BP_CHR_EnemyBase", bp_chr_base.generated_class())
    else:
        bp_enemy_base = create_or_get_blueprint("/Game/Blueprints/Characters/BP_CHR_EnemyBase", unreal.Pawn.static_class())
        
    # 3. 战斗与投射物基类
    create_or_get_blueprint("/Game/Blueprints/Combat/BP_WPN_Base", unreal.Actor.static_class())
    create_or_get_blueprint("/Game/Blueprints/Projectiles/BP_PRJ_Base", unreal.Actor.static_class())
    
    log("=== Framework 基础架构构建完成 ===")

def main():
    log("启动 SOP Framework 标准化构建...")
    build_core_hierarchy()
    log("SOP Framework 构建成功。")

if __name__ == "__main__":
    main()
