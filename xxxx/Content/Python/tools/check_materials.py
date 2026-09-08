# -*- coding: utf-8 -*-
import unreal

sp = unreal.load_asset("/Game/P01/Imported/Content/Asset/Art/02_Enemies/Zombie/01_Zombie_Walker_Basic/Sprites/SP_T_Zombie_WalkerBasic_01")
if sp:
    mat = sp.get_default_material()
    print(f"Sprite Default Material: {mat.get_path_name() if mat else 'None'}")
    if mat:
        print(f"Material BlendMode: {mat.get_editor_property('blend_mode')}")

# 检查主角的材质对比
player_bp = unreal.load_asset("/Game/Blueprints/Player/BP_Player_Medic")
cdo = unreal.get_default_object(player_bp.generated_class())
fb_comp = cdo.get_component_by_class(unreal.PaperFlipbookComponent)
if fb_comp:
    mat = fb_comp.get_material(0)
    print(f"Player FlipbookComp Material(0): {mat.get_path_name() if mat else 'None'}")
    fb = fb_comp.get_editor_property("source_flipbook")
    if fb:
        print(f"Player Flipbook: {fb.get_path_name()}")
