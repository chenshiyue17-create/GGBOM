# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》01_KineticPistol 3帧动能子弹贴图导入与 Flipbook 投射物实装
1. 导入 Content/美术/Art/03_Weapons/01_KineticPistol 下的 3 帧贴图:
   - T_Bullet_KineticPistol_01_Muzzle.png
   - T_Bullet_KineticPistol_02_Flight.png
   - T_Bullet_KineticPistol_03_Impact.png
2. 生成 3 个标准 PaperSprite (SP_Bullet_KP_01_Muzzle, SP_Bullet_KP_02_Flight, SP_Bullet_KP_03_Impact)
3. 组合生成 3 帧连贯的 PaperFlipbook: FB_Bullet_KineticPistol_Loop
4. 更新 BP_ProjectileBase，挂载该真实 3 帧 Flipbook 动画与透明无光照材质
================================================================================
"""
from __future__ import annotations
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
SRC_DIR = ROOT / "Content" / "美术" / "Art" / "03_Weapons" / "01_KineticPistol"

DEST_TEX_DIR = "/Game/GGBOM/Art/Textures/Weapons"
DEST_SP_DIR = "/Game/GGBOM/Art/Sprites/Weapons"
DEST_FB_DIR = "/Game/GGBOM/Art/Flipbooks/Weapons"
PROJ_BP_PATH = "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase"

ASSETS = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
BPLIB = unreal.BlueprintEditorLibrary
SUBOBJECTS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)

def ensure_dir(path: str):
    if not ASSETS.does_directory_exist(path):
        ASSETS.make_directory(path)

def import_texture(file_name: str) -> unreal.Texture2D:
    ensure_dir(DEST_TEX_DIR)
    tex_name = file_name.replace(".png", "")
    dest_path = f"{DEST_TEX_DIR}/{tex_name}"
    
    if ASSETS.does_asset_exist(dest_path):
        tex = unreal.load_asset(dest_path)
    else:
        src_file = str(SRC_DIR / file_name)
        task = unreal.AssetImportTask()
        task.set_editor_property("filename", src_file)
        task.set_editor_property("destination_path", DEST_TEX_DIR)
        task.set_editor_property("destination_name", tex_name)
        task.set_editor_property("automated", True)
        task.set_editor_property("replace_existing", True)
        task.set_editor_property("save", True)
        TOOLS.import_asset_tasks([task])
        tex = unreal.load_asset(dest_path)
        
    if tex:
        tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_EDITOR_ICON)
        tex.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
        tex.set_editor_property("filter", unreal.TextureFilter.TF_NEAREST)
        tex.set_editor_property("srgb", True)
        ASSETS.save_loaded_asset(tex, only_if_is_dirty=False)
    return tex

def create_sprite(sp_name: str, texture: unreal.Texture2D) -> unreal.PaperSprite:
    ensure_dir(DEST_SP_DIR)
    path = f"{DEST_SP_DIR}/{sp_name}"
    sprite = unreal.load_asset(path) if ASSETS.does_asset_exist(path) else None
    if not sprite:
        sprite = TOOLS.create_asset(sp_name, DEST_SP_DIR, unreal.PaperSprite, unreal.PaperSpriteFactory())
        
    sx = float(texture.blueprint_get_size_x())
    sy = float(texture.blueprint_get_size_y())
    sprite.set_editor_property("source_texture", texture)
    sprite.set_editor_property("source_uv", unreal.Vector2D(0.0, 0.0))
    sprite.set_editor_property("source_dimension", unreal.Vector2D(sx, sy))
    sprite.set_editor_property("pixels_per_unreal_unit", 1.0)
    
    pivot = getattr(unreal, "SpritePivotMode", getattr(unreal, "PaperSpritePivotMode", None))
    if pivot:
        sprite.set_editor_property("pivot_mode", pivot.CENTER_CENTER)
        
    mat = unreal.load_asset("/Paper2D/TranslucentUnlitSpriteMaterial")
    if mat:
        sprite.set_editor_property("default_material", mat)
        
    ASSETS.save_loaded_asset(sprite, only_if_is_dirty=False)
    return sprite

def create_flipbook(fb_name: str, sprites: list[unreal.PaperSprite], fps: float = 12.0) -> unreal.PaperFlipbook:
    ensure_dir(DEST_FB_DIR)
    path = f"{DEST_FB_DIR}/{fb_name}"
    fb = unreal.load_asset(path) if ASSETS.does_asset_exist(path) else None
    if not fb:
        factory = unreal.PaperFlipbookFactory()
        fb = TOOLS.create_asset(fb_name, DEST_FB_DIR, unreal.PaperFlipbook, factory)
        
    fb.set_editor_property("frames_per_second", fps)
    
    # 构造关键帧列表
    key_frames = []
    for sp in sprites:
        kf = unreal.PaperFlipbookKeyFrame()
        kf.set_editor_property("sprite", sp)
        kf.set_editor_property("frame_run", 1)
        key_frames.append(kf)
        
    fb.set_editor_property("key_frames", key_frames)
    mat = unreal.load_asset("/Paper2D/TranslucentUnlitSpriteMaterial")
    if mat:
        fb.set_editor_property("default_material", mat)
        
    ASSETS.save_loaded_asset(fb, only_if_is_dirty=False)
    return fb

def update_projectile_with_flipbook(fb: unreal.PaperFlipbook):
    print("🔫 更新 BP_ProjectileBase 挂载 3 帧动能子弹 Flipbook...")
    bp = unreal.load_asset(PROJ_BP_PATH)
    if not bp:
        raise RuntimeError(f"BP_ProjectileBase 缺失: {PROJ_BP_PATH}")
        
    handles = SUBOBJECTS.k2_gather_subobject_data_for_blueprint(bp)
    root_handle = handles[0]
    
    existing_vars = {}
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
        existing_vars[vname] = (h, unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp))

    mat = unreal.load_asset("/Paper2D/TranslucentUnlitSpriteMaterial")

    # 挂载或更新 Flipbook 组件
    if "BulletFlipbook" not in existing_vars:
        params = unreal.AddNewSubobjectParams()
        params.set_editor_property("parent_handle", root_handle)
        params.set_editor_property("new_class", unreal.PaperFlipbookComponent.static_class())
        params.set_editor_property("blueprint_context", bp)
        h, _ = SUBOBJECTS.add_new_subobject(params)
        SUBOBJECTS.rename_subobject(h, unreal.Text("BulletFlipbook"))
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        fb_comp = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
    else:
        fb_comp = existing_vars["BulletFlipbook"][1]

    fb_comp.set_editor_property("source_flipbook", fb)
    if mat:
        fb_comp.set_material(0, mat)
    fb_comp.set_editor_property("translucency_sort_priority", 2600)
    fb_comp.set_editor_property("relative_scale3d", unreal.Vector(0.7, 0.7, 0.7))

    # 如果存在旧的静态 BulletSprite，隐藏它或设为空
    if "BulletSprite" in existing_vars:
        sp_old = existing_vars["BulletSprite"][1]
        sp_old.set_editor_property("visible", False)
        sp_old.set_editor_property("hidden_in_game", True)

    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    print("✅ BP_ProjectileBase 已成功换装 3 帧动能手枪子弹动画！")

def main():
    print("================================================================")
    print("🚀 开始导入 01_KineticPistol 3 帧动能子弹贴图与实装...")
    print("================================================================")
    
    t1 = import_texture("T_Bullet_KineticPistol_01_Muzzle.png")
    t2 = import_texture("T_Bullet_KineticPistol_02_Flight.png")
    t3 = import_texture("T_Bullet_KineticPistol_03_Impact.png")
    
    sp1 = create_sprite("SP_Bullet_KP_01_Muzzle", t1)
    sp2 = create_sprite("SP_Bullet_KP_02_Flight", t2)
    sp3 = create_sprite("SP_Bullet_KP_03_Impact", t3)
    
    # 创建 3 帧连贯飞行动画 (出膛 -> 飞行 -> 动能波动 -> 飞行)
    fb = create_flipbook("FB_Bullet_KineticPistol_Flight", [sp1, sp2, sp3], fps=15.0)
    
    update_projectile_with_flipbook(fb)
    
    ASSETS.save_directory("/Game/GGBOM", only_if_is_dirty=False, recursive=True)
    ASSETS.save_directory("/Game/Blueprints", only_if_is_dirty=False, recursive=True)
    print("🎉 3 帧动能子弹贴图与 Flipbook 投射物实装全部完成！")

if __name__ == "__main__":
    main()
