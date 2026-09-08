# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》恢复 UE5 原生默认贴图滤波 (TF_DEFAULT)
- 不做任何人为锐化或额外平滑强制干预，100% 遵从 UE5 默认贴图设置与渲染呈现
================================================================================
"""
from __future__ import annotations
import unreal

ASSETS = unreal.EditorAssetLibrary

def log(msg: str):
    unreal.log(f"[GGBOM-DefaultFilter] {msg}")

def restore_default_texture(tex: unreal.Texture2D):
    if not tex:
        return
    tex.set_editor_property("filter", unreal.TextureFilter.TF_DEFAULT)  # 恢复原生默认过滤
    tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    tex.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    tex.set_editor_property("address_x", unreal.TextureAddress.TA_CLAMP)
    tex.set_editor_property("address_y", unreal.TextureAddress.TA_CLAMP)
    tex.set_editor_property("srgb", True)
    ASSETS.save_loaded_asset(tex, only_if_is_dirty=False)

def run_restore():
    log("🎨 开始全量恢复贴图为 UE5 原生默认滤波 (TF_DEFAULT)...")
    folders = ["/Game/GGBOM", "/Game/P01/Imported"]
    count = 0
    for folder in folders:
        for asset_path in ASSETS.list_assets(folder, recursive=True):
            asset_data = ASSETS.find_asset_data(asset_path)
            if asset_data.asset_class_path.asset_name == "Texture2D":
                tex = unreal.load_asset(asset_path)
                if isinstance(tex, unreal.Texture2D):
                    restore_default_texture(tex)
                    count += 1
    log(f"✅ 已完成 {count} 张贴图的 TF_DEFAULT 原生默认设置！")
    ASSETS.save_directory("/Game/GGBOM", only_if_is_dirty=False, recursive=True)

if __name__ == "__main__":
    run_restore()
