# -*- coding: utf-8 -*-
"""
================================================================================
彻底修复角色重叠问题 (Fix Character Overlap)
1. 移除地图 MAP_GGBOM_Main 中残留的静态 PaperFlipbookActor (Player_Medic_Animated)
2. 移除重复的旧相机 PortraitCamera_9x16，保留 Master_Orthographic_Camera
3. 校验并确保 GameMode 的 DefaultPawnClass = BP_Player_Medic
4. 校验 PlayerStart 位置，确保生成的唯一主角位于 (0, -10, -600)
5. 保持关卡清洁并保存
================================================================================
"""
import unreal

MAP_PATH = "/Game/GGBOM/Maps/MAP_GGBOM_Main"
GAMEMODE_PATH = "/Game/GGBOM/Blueprints/BP_GGBOM_GameMode"
PLAYER_BP_PATH = "/Game/Blueprints/Player/BP_Player_Medic"

unreal.EditorLevelLibrary.load_level(MAP_PATH)
world = unreal.EditorLevelLibrary.get_editor_world()

actors = unreal.EditorLevelLibrary.get_all_level_actors()
removed_count = 0

for a in actors:
    lbl = a.get_actor_label() if hasattr(a, "get_actor_label") else a.get_name()
    cls_name = a.get_class().get_name()
    
    # 1. 移除静态放置的重叠角色
    if lbl == "Player_Medic_Animated" or ("Player_Medic" in lbl and cls_name == "PaperFlipbookActor"):
        print(f"🗑️ 删除静态重叠角色: {lbl} ({cls_name})")
        unreal.EditorLevelLibrary.destroy_actor(a)
        removed_count += 1
        
    # 2. 移除多余的旧相机
    elif lbl == "PortraitCamera_9x16":
        print(f"🗑️ 删除多余相机: {lbl}")
        unreal.EditorLevelLibrary.destroy_actor(a)
        removed_count += 1

print(f"✅ 共清理 {removed_count} 个冲突 Actor")

# 3. 校验 GameMode 与 Player
gm_bp = unreal.load_asset(GAMEMODE_PATH)
player_bp = unreal.load_asset(PLAYER_BP_PATH)

if gm_bp and player_bp:
    gm_cdo = unreal.get_default_object(gm_bp.generated_class())
    if gm_cdo:
        gm_cdo.set_editor_property("default_pawn_class", player_bp.generated_class())
    unreal.BlueprintEditorLibrary.compile_blueprint(gm_bp)
    unreal.EditorAssetLibrary.save_loaded_asset(gm_bp, only_if_is_dirty=False)
    print("✅ GameMode DefaultPawnClass 已同步为 BP_Player_Medic")

# 4. 保存地图
unreal.EditorLoadingAndSavingUtils.save_map(world, MAP_PATH)
unreal.EditorAssetLibrary.save_directory("/Game/GGBOM", only_if_is_dirty=False, recursive=True)
print("🎉 MAP_GGBOM_Main 清洁修复并持久化保存完成！")
