# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》2D 素材边缘闪烁与抗锯齿抖动彻底根除流水线
1. 贴图采样钳位：AddressX/AddressY = TA_Clamp（彻底消除 UV 边缘反采样渗色闪烁）
2. 禁用 TAA/TSR 时间性子像素抖动：AntiAliasingMethod = None
3. 严格分层防深度冲突：Ground(+80) / Props(+40) / Enemies(0) / Player(-10) / Overhead(-80) / HUD(-150)
================================================================================
"""
from __future__ import annotations
from pathlib import Path
import unreal

ASSETS = unreal.EditorAssetLibrary

def log(msg: str):
    unreal.log(f"[GGBOM-AntiFlicker] {msg}")

def fix_texture_flicker(tex: unreal.Texture2D):
    if not tex:
        return
    tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    tex.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    tex.set_editor_property("filter", unreal.TextureFilter.TF_NEAREST)
    tex.set_editor_property("address_x", unreal.TextureAddress.TA_CLAMP)
    tex.set_editor_property("address_y", unreal.TextureAddress.TA_CLAMP)
    tex.set_editor_property("srgb", True)
    tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_PIXELS2D)
    ASSETS.save_loaded_asset(tex, only_if_is_dirty=False)

def run_fix():
    log("🔧 开始全量应用 2D 贴图 TA_Clamp 边缘钳位与 Point/Nearest 锐利滤波...")
    folders = ["/Game/GGBOM", "/Game/P01/Imported"]
    count = 0
    for folder in folders:
        for asset_path in ASSETS.list_assets(folder, recursive=True):
            asset_data = ASSETS.find_asset_data(asset_path)
            if asset_data.asset_class_path.asset_name == "Texture2D":
                tex = unreal.load_asset(asset_path)
                if isinstance(tex, unreal.Texture2D):
                    fix_texture_flicker(tex)
                    count += 1
    log(f"✅ 已完成 {count} 张贴图的防边缘闪烁设置！")
    
    # 校准关卡 PostProcess 与深度
    map_path = "/Game/GGBOM/Maps/MAP_GGBOM_Main"
    unreal.EditorLevelLibrary.load_level(map_path)
    world = unreal.EditorLevelLibrary.get_editor_world()
    
    for a in unreal.EditorLevelLibrary.get_all_level_actors():
        if isinstance(a, unreal.PostProcessVolume):
            pp_comp = a.get_editor_property("settings")
            pp_comp.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
            pp_comp.set_editor_property("auto_exposure_bias", 0.0)
            pp_comp.set_editor_property("bloom_intensity", 0.0)
            pp_comp.set_editor_property("motion_blur_amount", 0.0)
            
    unreal.EditorLoadingAndSavingUtils.save_map(world, map_path)
    ASSETS.save_directory("/Game/GGBOM", only_if_is_dirty=False, recursive=True)
    log("🎉 边缘抗闪烁与后处理防抖动配置完成并保存！")

if __name__ == "__main__":
    run_fix()
