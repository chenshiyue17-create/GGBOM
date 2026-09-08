# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》全量贴图平滑双线性滤波 (TF_Bilinear + TA_Clamp)
- 移除硬点锐化/马赛克感，还原原画高质量柔和圆润质感
- 保留 TA_Clamp 边缘采样钳位，确保边缘平滑且绝对不闪烁
================================================================================
"""
from __future__ import annotations
import unreal

ASSETS = unreal.EditorAssetLibrary

def log(msg: str):
    unreal.log(f"[GGBOM-SmoothFilter] {msg}")

def set_smooth_texture(tex: unreal.Texture2D):
    if not tex:
        return
    tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    tex.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    tex.set_editor_property("filter", unreal.TextureFilter.TF_BILINEAR)  # 高清柔和平滑双线性滤波
    tex.set_editor_property("address_x", unreal.TextureAddress.TA_CLAMP)  # 防边缘闪烁
    tex.set_editor_property("address_y", unreal.TextureAddress.TA_CLAMP)  # 防边缘闪烁
    tex.set_editor_property("srgb", True)
    tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_PIXELS2D)
    ASSETS.save_loaded_asset(tex, only_if_is_dirty=False)

def run_smooth():
    log("🎨 开始全量恢复 2D 贴图高品质平滑滤波 (TF_Bilinear)...")
    folders = ["/Game/GGBOM", "/Game/P01/Imported"]
    count = 0
    for folder in folders:
        for asset_path in ASSETS.list_assets(folder, recursive=True):
            asset_data = ASSETS.find_asset_data(asset_path)
            if asset_data.asset_class_path.asset_name == "Texture2D":
                tex = unreal.load_asset(asset_path)
                if isinstance(tex, unreal.Texture2D):
                    set_smooth_texture(tex)
                    count += 1
    log(f"✅ 已完成 {count} 张贴图的高清平滑双线性滤波校准！")
    ASSETS.save_directory("/Game/GGBOM", only_if_is_dirty=False, recursive=True)

if __name__ == "__main__":
    run_smooth()
