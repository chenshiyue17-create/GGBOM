# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》UE5 2D 美术素材无损色彩保真与后处理处理规范流水线
================================================================================
"""
from __future__ import annotations
from pathlib import Path
import unreal

ASSETS = unreal.EditorAssetLibrary

def log(msg: str):
    unreal.log(f"[GGBOM-2D-ColorSpec] {msg}")

def calibrate_texture(tex: unreal.Texture2D):
    if not tex:
        return
    tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    tex.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    tex.set_editor_property("filter", unreal.TextureFilter.TF_BILINEAR)
    tex.set_editor_property("srgb", True)
    tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_PIXELS2D)
    ASSETS.save_loaded_asset(tex, only_if_is_dirty=False)

def apply_2d_color_pipeline():
    log("🎨 开始全量校准 2D 贴图色彩空间与无损压缩设置...")
    
    folders = ["/Game/GGBOM", "/Game/P01/Imported"]
    count = 0
    for folder in folders:
        for asset_path in ASSETS.list_assets(folder, recursive=True):
            asset_data = ASSETS.find_asset_data(asset_path)
            if asset_data.asset_class_path.asset_name == "Texture2D":
                tex = unreal.load_asset(asset_path)
                if isinstance(tex, unreal.Texture2D):
                    calibrate_texture(tex)
                    count += 1
    log(f"✅ 已完成 {count} 张 2D 贴图的无损色彩与像素规范校准！")

    # 配置主关卡 PostProcessVolume 消除色调泛白与曝光失真
    map_path = "/Game/GGBOM/Maps/MAP_GGBOM_Main"
    unreal.EditorLevelLibrary.load_level(map_path)
    world = unreal.EditorLevelLibrary.get_editor_world()
    
    # 查找或生成 PostProcessVolume
    pp_vol = None
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        if isinstance(a, unreal.PostProcessVolume):
            pp_vol = a
            break
            
    if not pp_vol:
        pp_vol = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0, 0, 0), unreal.Rotator())
        pp_vol.set_actor_label("PP_2D_Color_Accuracy")
        
    pp_vol.set_editor_property("unbound", True)
    pp_comp = pp_vol.get_editor_property("settings")
    
    # 手动固定 1:1 线性曝光与禁用泛光与色调曲线
    pp_comp.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
    pp_comp.set_editor_property("auto_exposure_bias", 0.0)
    pp_comp.set_editor_property("auto_exposure_min_brightness", 1.0)
    pp_comp.set_editor_property("auto_exposure_max_brightness", 1.0)
    pp_comp.set_editor_property("bloom_intensity", 0.0)
    pp_comp.set_editor_property("motion_blur_amount", 0.0)
    pp_comp.set_editor_property("ambient_occlusion_intensity", 0.0)
    
    unreal.EditorLoadingAndSavingUtils.save_map(world, map_path)
    log("🎉 关卡 2D 色彩保真 PostProcessVolume 配置并保存完成！")

if __name__ == "__main__":
    apply_2d_color_pipeline()
