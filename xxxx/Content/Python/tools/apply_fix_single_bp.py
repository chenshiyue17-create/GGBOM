# -*- coding: utf-8 -*-
"""
单蓝图无黑底与硬碰撞阻挡加固脚本
1. 消除黑底: PaperFlipbookComponent 绑定 /Paper2D/TranslucentUnlitSpriteMaterial
2. 刚体阻挡: BoxComponent 设为 RootComponent，开启 BlockAllDynamic 与 ECC_Pawn Hard Block
"""
import sys
import unreal

bplib = unreal.BlueprintEditorLibrary
subsystems = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
mat_trans = unreal.load_asset("/Paper2D/TranslucentUnlitSpriteMaterial")

TARGET_CONFIGS = {
    "BP_Player_Medic": {
        "path": "/Game/Blueprints/Player/BP_Player_Medic",
        "is_player": True,
        "box_extent": unreal.Vector(24.0, 70.0, 36.0),
    },
    "BP_Boss_Overlord": {
        "path": "/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord",
        "is_player": False,
        "box_extent": unreal.Vector(55.0, 90.0, 65.0),
    },
    "BP_Enemy_MutantHound": {
        "path": "/Game/Blueprints/Characters/Enemies/BP_Enemy_MutantHound",
        "is_player": False,
        "box_extent": unreal.Vector(30.0, 70.0, 32.0),
    },
    "BP_Enemy_ZombieWalker": {
        "path": "/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker",
        "is_player": False,
        "box_extent": unreal.Vector(25.0, 60.0, 35.0),
    },
    "BP_Enemy_ZombieRunner": {
        "path": "/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieRunner",
        "is_player": False,
        "box_extent": unreal.Vector(25.0, 60.0, 35.0),
    },
    "BP_Enemy_VenomShooter": {
        "path": "/Game/Blueprints/Characters/Enemies/BP_Enemy_VenomShooter",
        "is_player": False,
        "box_extent": unreal.Vector(25.0, 60.0, 35.0),
    },
    "BP_Enemy_ArmoredGuard": {
        "path": "/Game/Blueprints/Characters/Enemies/BP_Enemy_ArmoredGuard",
        "is_player": False,
        "box_extent": unreal.Vector(30.0, 70.0, 40.0),
    },
    "BP_Enemy_MutantBrute": {
        "path": "/Game/Blueprints/Characters/Enemies/BP_Enemy_MutantBrute",
        "is_player": False,
        "box_extent": unreal.Vector(35.0, 75.0, 45.0),
    },
}

target_key = None
for arg in sys.argv:
    for k in TARGET_CONFIGS:
        if k in arg:
            target_key = k
            break
    if target_key:
        break

if not target_key:
    target_key = "BP_Player_Medic"

cfg = TARGET_CONFIGS[target_key]
print(f"=== [FIX_PHYSICS_AND_VISUALS] Processing: {target_key} ===")

bp = unreal.load_asset(cfg["path"])
if not bp:
    raise RuntimeError(f"Cannot load Blueprint: {cfg['path']}")

handles = subsystems.k2_gather_subobject_data_for_blueprint(bp)
box_handle = None
box_comp = None
fb_handle = None
fb_comp = None

for h in handles:
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
    if isinstance(obj, unreal.BoxComponent):
        box_handle = h
        box_comp = obj
    elif isinstance(obj, unreal.PaperFlipbookComponent):
        fb_handle = h
        fb_comp = obj

# 1. 消除黑底: 设置 TranslucentUnlitSpriteMaterial
if fb_comp and mat_trans:
    fb_comp.set_material(0, mat_trans)
    try:
        fb_comp.set_editor_property("translucency_sort_priority", 100 if not cfg["is_player"] else 300)
    except Exception:
        pass

cdo = unreal.get_default_object(bp.generated_class())
if cdo and mat_trans:
    cdo_fb = cdo.get_component_by_class(unreal.PaperFlipbookComponent)
    if cdo_fb:
        cdo_fb.set_material(0, mat_trans)

# 2. 刚体阻挡: 将 BoxComponent 设为 RootComponent
if box_handle:
    try:
        subsystems.make_new_scene_root(handles[0], box_handle, bp)
        print(f"[{target_key}] BoxComponent successfully set as RootComponent")
    except Exception as e:
        print(f"[{target_key}] make_new_scene_root exception: {e}")

# 3. 强化碰撞通道 (BlockAllDynamic + ECC_Pawn Hard Block)
if box_comp:
    box_comp.set_editor_property("box_extent", cfg["box_extent"])
    box_comp.set_collision_profile_name("BlockAllDynamic")
    box_comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    box_comp.set_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN, unreal.CollisionResponseType.ECR_BLOCK)
    box_comp.set_collision_response_to_channel(unreal.CollisionChannel.ECC_WORLD_STATIC, unreal.CollisionResponseType.ECR_BLOCK)
    box_comp.set_collision_response_to_channel(unreal.CollisionChannel.ECC_WORLD_DYNAMIC, unreal.CollisionResponseType.ECR_BLOCK)
    try:
        box_comp.set_editor_property("generate_overlap_events", True)
    except Exception:
        pass

if cdo and box_comp:
    cdo_box = cdo.get_component_by_class(unreal.BoxComponent)
    if cdo_box:
        cdo_box.set_editor_property("box_extent", cfg["box_extent"])
        cdo_box.set_collision_profile_name("BlockAllDynamic")
        cdo_box.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
        cdo_box.set_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN, unreal.CollisionResponseType.ECR_BLOCK)
        cdo_box.set_collision_response_to_channel(unreal.CollisionChannel.ECC_WORLD_STATIC, unreal.CollisionResponseType.ECR_BLOCK)
        cdo_box.set_collision_response_to_channel(unreal.CollisionChannel.ECC_WORLD_DYNAMIC, unreal.CollisionResponseType.ECR_BLOCK)

compiled = bplib.compile_blueprint(bp)
saved = unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
print(f"=== [FIX_PHYSICS_AND_VISUALS] {target_key} COMPLETE: compiled={compiled}, saved={saved} ===")
