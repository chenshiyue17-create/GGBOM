# -*- coding: utf-8 -*-
import unreal

GEN = "/Game/GGBOM"
MAP_PATH = f"{GEN}/Maps/MAP_GGBOM_Main"

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
if world:
    unreal.EditorLoadingAndSavingUtils.save_map(world, MAP_PATH)
    unreal.EditorAssetLibrary.save_directory(GEN, only_if_is_dirty=False, recursive=True)
    unreal.EditorAssetLibrary.save_directory("/Game/Blueprints", only_if_is_dirty=False, recursive=True)
    print("ALL_MAP_AND_ASSETS_SAVED_SUCCESS")
