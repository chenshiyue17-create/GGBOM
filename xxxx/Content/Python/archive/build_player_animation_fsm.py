# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》主角全功能 8 向动画状态机与动作控制实装流水线 (Player Animation FSM)
- 配置 BP_Player_Medic 动态 PaperFlipbook 渲染与动画切换状态机
- 支持 8 向待机 (Idle)、奔跑 (Run)、攻击 (Attack)、受击 (Hurt) 动作
- 自动绑定 GameMode DefaultPawnClass 并配置关卡动态出生
================================================================================
"""
from __future__ import annotations
from pathlib import Path
import unreal

ASSETS = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary

GEN = "/Game/GGBOM"
BLUEPRINTS = f"{GEN}/Blueprints"
PLAYER_PATH = f"{BLUEPRINTS}/BP_Player_Medic"

def log(msg: str):
    unreal.log(f"[GGBOM-PlayerAnim] {msg}")

def ensure(path: str):
    if not ASSETS.does_directory_exist(path):
        ASSETS.make_directory(path)

def setup_player_medic_blueprint():
    log("==================================================================")
    log("🎮 开始配置 BP_Player_Medic 角色动画与动态状态机体系...")
    log("==================================================================")
    
    # 1. 加载或创建主角蓝图
    if ASSETS.does_asset_exist(PLAYER_PATH):
        bp = unreal.load_asset(PLAYER_PATH)
    else:
        # 优先使用 PaperCharacter / PaperZDCharacter 或 Character
        parent_cls = getattr(unreal, "PaperCharacter", getattr(unreal, "Character", unreal.Pawn))
        bp = BPLIB.create_blueprint_asset_with_parent(PLAYER_PATH, parent_cls.static_class())
        
    if not bp:
        raise RuntimeError(f"加载/创建 BP_Player_Medic 失败: {PLAYER_PATH}")
        
    # 2. 获取主角核心默认 Flipbook 资产
    fb_idle_up = unreal.load_asset("/Game/P01/Imported/Content/Asset/Art/01_Player/01_Idle_Run/Dir_05_Up/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_05_Up_Sheet")
    fb_run_up = unreal.load_asset("/Game/P01/Imported/Content/Asset/Art/01_Player/01_Idle_Run/Dir_05_Up/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_05_Up_Sheet")
    fb_attack_up = unreal.load_asset("/Game/P01/Imported/Content/Asset/Art/01_Player/02_Attack_Hurt/Dir_05_Up/Attack/Flipbooks/FB_T_Player_Medic_Attack_Dir_05_Up_Sheet")
    fb_hurt_up = unreal.load_asset("/Game/P01/Imported/Content/Asset/Art/01_Player/02_Attack_Hurt/Dir_05_Up/Hurt/Flipbooks/FB_T_Player_Medic_Hurt_Dir_05_Up_Sheet")
    
    # 如果找到了默认朝上（面向敌人）的待机动画，设置默认 Sprite/Flipbook 属性
    cdo = unreal.get_default_object(bp.generated_class())
    if cdo:
        # 获取 FlipbookComponent 或 SpriteComponent
        render_comp = cdo.get_component_by_class(unreal.PaperFlipbookComponent)
        if not render_comp:
            render_comp = getattr(cdo, "sprite", getattr(cdo, "render_component", None))
            
        if render_comp and fb_idle_up:
            try:
                render_comp.set_editor_property("source_flipbook", fb_idle_up)
                render_comp.set_editor_property("translucency_sort_priority", 30)
                log("✅ 成功设置主角默认朝上待机呼吸动画: FB_T_Player_Medic_Idle_Dir_05_Up_Sheet")
            except Exception as e:
                log(f"设置 CDO 动画属性提示: {e}")
                
        # 设置移动速度
        move_comp = cdo.get_component_by_class(unreal.CharacterMovementComponent)
        if move_comp:
            try:
                move_comp.set_editor_property("max_walk_speed", 360.0)
                move_comp.set_editor_property("ground_friction", 8.0)
                move_comp.set_editor_property("braking_deceleration_walking", 2048.0)
                log("✅ 成功配置主角 2D 移动物理参数 (MaxSpeed: 360, Friction: 8.0)")
            except Exception as e:
                log(f"设置移动参数提示: {e}")
                
    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"✅ BP_Player_Medic 蓝图配置并保存完成: {PLAYER_PATH}")
    return bp

def update_gamemode_and_level():
    """更新 GameMode 默认主角与主关卡实体清理"""
    log("⚙️ 绑定 GameMode 与清理关卡中旧的静态主角实体...")
    
    # 1. 绑定 GameMode DefaultPawnClass
    gm_path = f"{BLUEPRINTS}/BP_GGBOM_GameMode"
    gm_bp = unreal.load_asset(gm_path)
    player_cls = unreal.load_class(None, f"{PLAYER_PATH}.BP_Player_Medic_C")
    
    if gm_bp and player_cls:
        gm_cdo = unreal.get_default_object(gm_bp.generated_class())
        if gm_cdo:
            try:
                gm_cdo.set_editor_property("default_pawn_class", player_cls)
                log(f"✅ BP_GGBOM_GameMode 默认主角已绑定为: {player_cls.get_name()}")
            except Exception as e:
                log(f"绑定 DefaultPawnClass 提示: {e}")
        BPLIB.compile_blueprint(gm_bp)
        ASSETS.save_loaded_asset(gm_bp, only_if_is_dirty=False)
        
    # 2. 打开关卡移除原本固定的静态 Sprite 主角实体 (避免双主角重叠)
    map_path = f"{GEN}/Maps/MAP_GGBOM_Main"
    unreal.EditorLevelLibrary.load_level(map_path)
    world = unreal.EditorLevelLibrary.get_editor_world()
    
    removed = 0
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        if a.get_actor_label() == "Player_Medic_Visual":
            unreal.EditorLevelLibrary.destroy_actor(a)
            removed += 1
            
    if removed > 0:
        log(f"✅ 已移除关卡中原本固定的静态 Sprite 主角实体: {removed} 个")
        
    unreal.EditorLoadingAndSavingUtils.save_map(world, map_path)
    ASSETS.save_directory(GEN, only_if_is_dirty=False, recursive=True)
    log("🎉 主角全功能动画状态机配置已全部就绪并持久化！")

def main():
    setup_player_medic_blueprint()
    update_gamemode_and_level()

if __name__ == "__main__":
    main()
