# -*- coding: utf-8 -*-
"""
综合诊断三大问题:
1. 怪物黑底 (Sprite, Material, Texture Alpha)
2. 人物怪物碰撞 (RootComponent, BoxExtent, CollisionProfile, ResponseToPawn)
3. 射击无反馈 (BP_ProjectileBase 组件与碰撞设置)
"""
import unreal

print("==================================================")
print(">>> 1. 怪物黑底诊断")
print("==================================================")
enemies = [
    ("Boss", "/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord"),
    ("Hound", "/Game/Blueprints/Characters/Enemies/BP_Enemy_MutantHound"),
    ("Walker", "/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker"),
]

for label, bp_path in enemies:
    bp = unreal.load_asset(bp_path)
    if not bp:
        continue
    cdo = unreal.get_default_object(bp.generated_class())
    if not cdo:
        continue
    fb_comp = cdo.get_component_by_class(unreal.PaperFlipbookComponent)
    if not fb_comp:
        print(f"[{label}] No FlipbookComponent")
        continue
    fb = fb_comp.get_editor_property("source_flipbook")
    if not fb:
        print(f"[{label}] No source_flipbook")
        continue
    
    num_keyframes = fb.get_num_keyframes()
    print(f"[{label}] Flipbook: {fb.get_path_name()}, Keyframes: {num_keyframes}")
    
    if num_keyframes > 0:
        sp = fb.get_sprite_at_frame(0)
        if sp:
            mat = sp.get_default_material()
            mat_name = mat.get_path_name() if mat else "None"
            tex = sp.get_source_texture()
            tex_name = tex.get_path_name() if tex else "None"
            has_alpha = tex.has_alpha_channel() if tex else "Unknown"
            comp_settings = tex.get_editor_property("compression_settings") if tex else "Unknown"
            print(f"[{label}] Sprite: {sp.get_name()}")
            print(f"   Material: {mat_name}")
            print(f"   Texture: {tex_name}, HasAlpha: {has_alpha}, Comp: {comp_settings}")
            if mat:
                blend_mode = mat.get_editor_property("blend_mode")
                print(f"   Mat BlendMode: {blend_mode}")

print("==================================================")
print(">>> 2. 碰撞层级与响应诊断")
print("==================================================")
subsystems = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)

def check_bp_collision(name, path):
    bp = unreal.load_asset(path)
    if not bp:
        print(f"[{name}] Cannot load {path}")
        return
    handles = subsystems.k2_gather_subobject_data_for_blueprint(bp)
    print(f"[{name}] Total subobjects: {len(handles)}")
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        is_root = unreal.SubobjectDataBlueprintFunctionLibrary.is_root_component(data)
        vname = unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data)
        print(f"   Comp: {vname} ({obj.get_class().get_name()}), IsRoot: {is_root}")
        if isinstance(obj, unreal.PrimitiveComponent):
            c_name = obj.get_collision_profile_name()
            c_enabled = obj.get_collision_enabled()
            print(f"      CollisionProfile: {c_name}, Enabled: {c_enabled}")
            # 检查对 Pawn 的响应
            resp_pawn = obj.get_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN)
            print(f"      Response to ECC_Pawn: {resp_pawn}")

check_bp_collision("Player", "/Game/Blueprints/Player/BP_Player_Medic")
check_bp_collision("Walker", "/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker")
check_bp_collision("Boss", "/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord")

print("==================================================")
print(">>> 3. 子弹投射物 BP_ProjectileBase 诊断")
print("==================================================")
check_bp_collision("Projectile", "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase")
