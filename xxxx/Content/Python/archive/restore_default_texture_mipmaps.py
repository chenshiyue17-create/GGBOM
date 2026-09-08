# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》恢复 UE5 原生默认 Mipmap 与贴图分辨率处理
- 移除强行锁定的 TMGS_NO_MIPMAPS 高清锁定
- 恢复为 UE5 官方原生默认纹理组与 Mipmap 策略 (TMGS_FROM_TEXTURE_GROUP)
================================================================================
"""
from __future__ import annotations
import unreal

ASSETS = unreal.EditorAssetLibrary

def log(msg: str):
    unreal.log(f"[GGBOM-DefaultMipmaps] {msg}")

def restore_default_mipmaps(tex: unreal.Texture2D):
    if not tex:
        return
    tex.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP)  # 恢复默认 Mipmap
    tex.set_editor_property("filter", unreal.TextureFilter.TF_DEFAULT)                                  # 默认滤波
    tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_DEFAULT)     # 默认压缩
    tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_WORLD)                      # 恢复默认组
    tex.set_editor_property("address_x", unreal.TextureAddress.TA_CLAMP)
    tex.set_editor_property("address_y", unreal.TextureAddress.TA_CLAMP)
    tex.set_editor_property("srgb", True)
    ASSETS.save_loaded_asset(tex, only_if_is_dirty=False)

def run():
    log("🎨 开始全量恢复贴图为 UE5 默认原生 Mipmap 与标准分辨率策略...")
    folders = ["/Game/GGBOM", "/Game/P01/Imported"]
    count = 0
    for folder in folders:
        for asset_path in ASSETS.list_assets(folder, recursive=True):
            asset_data = ASSETS.find_asset_data(asset_path)
            if asset_data.asset_class_path.asset_name == "Texture2D":
                tex = unreal.load_asset(asset_path)
                if isinstance(tex, unreal.Texture2D):
                    restore_default_mipmaps(tex)
                    count += 1
    log(f"✅ 已完成 {count} 张贴图的 UE5 默认原生 Mipmap 与分辨率恢复！")
    ASSETS.save_directory("/Game/GGBOM", only_if_is_dirty=False, recursive=True)

if __name__ == "__main__":
    run()
