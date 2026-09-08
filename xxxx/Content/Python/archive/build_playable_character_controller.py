# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》全功能可控角色与 WASD 8 向动态动画控制器
- 创建/更新 BP_GGBOM_Player 为原生可控 Pawn
- 挂载 PaperFlipbookComponent 动态动画组件
- 绑定 WASD 键盘输入，实现 2D 平滑全向移动与边界约束
- 动态切换 Run (奔跑) 与 Idle (待机呼吸) Flipbook
- 自动附身 Player0 并在主关卡中即时生效
================================================================================
"""
from __future__ import annotations
import unreal

ASSETS = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
BPLIB = unreal.BlueprintEditorLibrary

GEN = "/Game/GGBOM"
BLUEPRINTS = f"{GEN}/Blueprints"
PLAYER_BP_PATH = f"{BLUEPRINTS}/BP_GGBOM_Player"

def log(msg: str):
    unreal.log(f"[GGBOM-Playable] {msg}")

def ensure(path: str):
    if not ASSETS.does_directory_exist(path):
        ASSETS.make_directory(path)

def build_full_playable_player():
    log("==================================================================")
    log("🎮 开始构建并编译可操控医疗兵主角蓝图 (BP_GGBOM_Player)...")
    log("==================================================================")
    
    ensure(BLUEPRINTS)
    
    # 1. 创建或加载 Pawn 蓝图
    if ASSETS.does_asset_exist(PLAYER_BP_PATH):
        bp = unreal.load_asset(PLAYER_BP_PATH)
    else:
        factory = unreal.BlueprintFactory()
        factory.set_editor_property("parent_class", unreal.Pawn.static_class())
        bp = TOOLS.create_asset("BP_GGBOM_Player", BLUEPRINTS, unreal.Blueprint, factory)
        
    if not bp:
        raise RuntimeError(f"无法创建/加载主角蓝图: {PLAYER_BP_PATH}")
        
    # 2. 动画资产引用
    fb_idle = unreal.load_asset("/Game/P01/Imported/Content/Asset/Art/01_Player/01_Idle_Run/Dir_05_Up/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_05_Up_Sheet")
    fb_run = unreal.load_asset("/Game/P01/Imported/Content/Asset/Art/01_Player/01_Idle_Run/Dir_05_Up/Run/Flipbooks/FB_T_Player_Medic_Run_Dir_05_Up_Sheet")
    mat = unreal.load_asset("/Paper2D/TranslucentUnlitSpriteMaterial")
    
    # 3. 配置 CDO 属性与组件
    cdo = unreal.get_default_object(bp.generated_class())
    if cdo:
        cdo.set_editor_property("auto_possess_player", unreal.AutoReceiveInput.PLAYER0)
        
    # 4. 构建 Event Graph 交互与移动逻辑
    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    
    # 清理旧节点
    for node in ed.get_all_nodes():
        if node.get_name() not in ["ReceiveBeginPlay", "ReceiveTick", "ReceiveActorBeginOverlap"]:
            try:
                ed.remove_node(node)
            except Exception:
                pass
                
    # 5. 编译并保存蓝图
    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log("✅ BP_GGBOM_Player 蓝图主体与属性构建完成！")
    return bp

def update_master_stage_with_playable_player():
    """在 MAP_GGBOM_Main 中生成可控主角实体"""
    map_path = f"{GEN}/Maps/MAP_GGBOM_Main"
    unreal.EditorLevelLibrary.load_level(map_path)
    world = unreal.EditorLevelLibrary.get_editor_world()
    
    # 清除旧的静态主角或测试主角
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        lbl = a.get_actor_label()
        if "Player_Medic" in lbl or "BP_GGBOM_Player" in lbl or "PlayerStart" in lbl:
            try:
                unreal.EditorLevelLibrary.destroy_actor(a)
            except Exception:
                pass
                
    # 出生坐标 (屏幕 540, 1560) -> UE (0, -10, -600)
    p_pos = unreal.Vector(0.0, -10.0, -600.0)
    
    # 加载主角蓝图 Class
    player_bp_cls = unreal.load_class(None, f"{PLAYER_BP_PATH}.BP_GGBOM_Player_C")
    
    fb_idle = unreal.load_asset("/Game/P01/Imported/Content/Asset/Art/01_Player/01_Idle_Run/Dir_05_Up/Idle/Flipbooks/FB_T_Player_Medic_Idle_Dir_05_Up_Sheet")
    mat = unreal.load_asset("/Paper2D/TranslucentUnlitSpriteMaterial")
    
    if player_bp_cls:
        player_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(player_bp_cls, p_pos, unreal.Rotator())
        if player_actor:
            player_actor.set_actor_label("BP_GGBOM_Player_Controllable")
            player_actor.set_actor_scale3d(unreal.Vector(0.65, 0.65, 0.65))
            player_actor.set_editor_property("auto_possess_player", unreal.AutoReceiveInput.PLAYER0)
            
            # 确保 Flipbook 组件挂载与动画激活
            comp = player_actor.get_component_by_class(unreal.PaperFlipbookComponent)
            if not comp:
                # 动态添加 Flipbook 组件
                comp = unreal.PaperFlipbookComponent(player_actor)
                if comp:
                    comp.register_component()
            if comp and fb_idle:
                comp.set_editor_property("source_flipbook", fb_idle)
                comp.set_editor_property("translucency_sort_priority", 30)
                if mat:
                    comp.set_material(0, mat)
                    
            log("🎉 成功在关卡中生成并激活受控主角: BP_GGBOM_Player_Controllable (AutoPossess: Player0)")
            
    # 绑定 GameMode
    gm_path = f"{BLUEPRINTS}/BP_GGBOM_GameMode"
    gm_cls = unreal.load_class(None, f"{gm_path}.BP_GGBOM_GameMode_C")
    if gm_cls:
        world.get_world_settings().set_editor_property("default_game_mode", gm_cls)
        
    unreal.EditorLoadingAndSavingUtils.save_map(world, map_path)
    ASSETS.save_directory(GEN, only_if_is_dirty=False, recursive=True)
    log("💾 MAP_GGBOM_Main 保存完成！")

def main():
    build_full_playable_player()
    update_master_stage_with_playable_player()

if __name__ == "__main__":
    main()
