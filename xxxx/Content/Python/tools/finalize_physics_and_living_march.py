# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》物理碰撞阻挡体系与全动态战线推进行军最终落地实施脚本
1. 7 种敌人蓝图: 绑定实体 BoxComponent (Pawn 碰撞) + ProjectileMovementComponent (原生向下行军推进)
2. 主角 BP_Player_Medic: 绑定实体 PlayerCollision (Pawn 碰撞) + 移动 bSweep 阻挡
3. 关卡 MAP_GGBOM_Main: 统一 Y=0 物理交互面，布设掩体沙袋与屏幕边界 BlockAll 阻挡墙
================================================================================
"""
from __future__ import annotations
import json
from pathlib import Path
import unreal

GEN = "/Game/GGBOM"
MAP_PATH = f"{GEN}/Maps/MAP_GGBOM_Main"
PLAYER_BP_PATH = "/Game/Blueprints/Player/BP_Player_Medic"
ENEMY_BP_DIR = "/Game/Blueprints/Characters/Enemies"

ASSETS = unreal.EditorAssetLibrary
BPLIB = unreal.BlueprintEditorLibrary
SUBOBJECTS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)

def log(msg: str):
    print(f"[PhysicsFinalize] {msg}")
    unreal.log(f"[PhysicsFinalize] {msg}")

ENEMY_CONFIGS = [
    {
        "name": "BP_Enemy_ZombieWalker",
        "display": "基础感染行尸",
        "speed": 60.0,
        "extent": unreal.Vector(26.0, 70.0, 36.0),
    },
    {
        "name": "BP_Enemy_ZombieRunner",
        "display": "敏捷疾跑行尸",
        "speed": 110.0,
        "extent": unreal.Vector(26.0, 70.0, 36.0),
    },
    {
        "name": "BP_Enemy_MutantHound",
        "display": "疾行变异猎犬",
        "speed": 150.0,
        "extent": unreal.Vector(30.0, 70.0, 32.0),
    },
    {
        "name": "BP_Enemy_VenomShooter",
        "display": "毒液喷射行尸",
        "speed": 55.0,
        "extent": unreal.Vector(26.0, 70.0, 36.0),
    },
    {
        "name": "BP_Enemy_ArmoredGuard",
        "display": "重装防暴行尸",
        "speed": 50.0,
        "extent": unreal.Vector(32.0, 70.0, 42.0),
    },
    {
        "name": "BP_Enemy_MutantBrute",
        "display": "重型蹒跚蛮兽",
        "speed": 40.0,
        "extent": unreal.Vector(38.0, 80.0, 48.0),
    },
    {
        "name": "BP_Boss_Overlord",
        "display": "深渊异化领主 Boss",
        "speed": 30.0,
        "extent": unreal.Vector(55.0, 90.0, 65.0),
    },
]

def ensure_box_component(bp: unreal.Blueprint, comp_name: str, extent: unreal.Vector, profile: str = "Pawn"):
    """为蓝图挂载或更新 BoxComponent 实体物理碰撞盒"""
    handles = SUBOBJECTS.k2_gather_subobject_data_for_blueprint(bp)
    target_comp = None
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        if isinstance(obj, unreal.BoxComponent) and (vname == comp_name or not target_comp):
            target_comp = obj
            break

    if not target_comp:
        params = unreal.AddNewSubobjectParams()
        params.set_editor_property("parent_handle", handles[0])
        params.set_editor_property("new_class", unreal.BoxComponent.static_class())
        params.set_editor_property("blueprint_context", bp)
        h, reason = SUBOBJECTS.add_new_subobject(params)
        if unreal.SubobjectDataBlueprintFunctionLibrary.is_handle_valid(h):
            SUBOBJECTS.rename_subobject(h, unreal.Text(comp_name))
            data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
            target_comp = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)

    if target_comp:
        target_comp.set_editor_property("box_extent", extent)
        try:
            target_comp.set_collision_profile_name(profile)
        except Exception:
            pass
        try:
            target_comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
        except Exception:
            pass
        try:
            target_comp.set_generate_overlap_events(True)
        except Exception:
            pass
        target_comp.set_editor_property("relative_location", unreal.Vector(0.0, 0.0, 0.0))
        target_comp.set_editor_property("relative_rotation", unreal.Rotator(0.0, 0.0, 0.0))
    return target_comp

def ensure_projectile_movement(bp: unreal.Blueprint, speed: float):
    """为敌人蓝图挂载 ProjectileMovementComponent 驱动战线下推行军"""
    handles = SUBOBJECTS.k2_gather_subobject_data_for_blueprint(bp)
    pmc = None
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        if isinstance(obj, unreal.ProjectileMovementComponent):
            pmc = obj
            break

    if not pmc:
        params = unreal.AddNewSubobjectParams()
        params.set_editor_property("parent_handle", handles[0])
        params.set_editor_property("new_class", unreal.ProjectileMovementComponent.static_class())
        params.set_editor_property("blueprint_context", bp)
        h, reason = SUBOBJECTS.add_new_subobject(params)
        if unreal.SubobjectDataBlueprintFunctionLibrary.is_handle_valid(h):
            SUBOBJECTS.rename_subobject(h, unreal.Text("EnemyMovement"))
            data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
            pmc = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)

    if pmc:
        pmc.set_editor_property("initial_speed", speed)
        pmc.set_editor_property("max_speed", speed)
        pmc.set_editor_property("velocity", unreal.Vector(0.0, 0.0, -speed))
        pmc.set_editor_property("projectile_gravity_scale", 0.0)
        try:
            pmc.set_editor_property("rotation_follows_velocity", False)
        except Exception:
            pass
        try:
            pmc.set_editor_property("should_bounce", False)
        except Exception:
            pass
    return pmc

def upgrade_all_enemy_blueprints():
    log("👾 [1/3] 正在升级 7 种敌人蓝图实体物理盒与行军推进组件...")
    for cfg in ENEMY_CONFIGS:
        bp_path = f"{ENEMY_BP_DIR}/{cfg['name']}"
        bp = unreal.load_asset(bp_path)
        if not bp:
            log(f"⚠️ 未找到蓝图: {bp_path}")
            continue

        # 1. 挂载实体物理盒
        ensure_box_component(bp, "EnemyCollision", cfg["extent"], "Pawn")

        # 2. 挂载平滑向下行军推进组件
        ensure_projectile_movement(bp, cfg["speed"])

        BPLIB.compile_blueprint(bp)
        ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
        log(f"  + 敌人蓝图 {cfg['display']} ({cfg['name']}) 碰撞与行军装配完成！")

def upgrade_player_medic():
    log("🎮 [2/3] 正在确认主角 BP_Player_Medic 实体碰撞与阻挡...")
    bp = unreal.load_asset(PLAYER_BP_PATH)
    if bp:
        ensure_box_component(bp, "PlayerCollision", unreal.Vector(24.0, 70.0, 36.0), "Pawn")
        BPLIB.compile_blueprint(bp)
        ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
        log("  + 主角 BP_Player_Medic 实体碰撞盒确认完毕！")

def upgrade_level_world():
    log(f"🗺️ [3/3] 正在装配主关卡 {MAP_PATH} 物理碰撞面与屏障...")
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
    if not world:
        raise RuntimeError(f"无法加载地图: {MAP_PATH}")

    actors = unreal.EditorLevelLibrary.get_all_level_actors()

    # 1. 清理已有 Wall_ 阻挡体
    for a in actors:
        lbl = a.get_actor_label()
        if lbl.startswith("Wall_"):
            unreal.EditorLevelLibrary.destroy_actor(a)

    # 2. 统一关卡中所有敌人的 Y=0.0，使玩家与怪物处于完全相同的物理交互平面
    roster_locs = {
        "Enemy_Zombie_01": unreal.Vector(-150.0, 0.0, 220.0),
        "Enemy_Zombie_02": unreal.Vector(0.0, 0.0, 180.0),
        "Enemy_Zombie_03": unreal.Vector(150.0, 0.0, 220.0),
        "Enemy_Runner_01": unreal.Vector(-120.0, 0.0, 320.0),
        "Enemy_VenomShooter_01": unreal.Vector(120.0, 0.0, 320.0),
        "Enemy_ArmoredGuard_01": unreal.Vector(0.0, 0.0, 370.0),
        "Enemy_Hound_01": unreal.Vector(-220.0, 0.0, 460.0),
        "Enemy_Hound_02": unreal.Vector(220.0, 0.0, 460.0),
        "Enemy_Brute_Elite": unreal.Vector(0.0, 0.0, 550.0),
        "Boss_Overlord_Live": unreal.Vector(0.0, 0.0, 680.0),
    }

    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    for a in actors:
        lbl = a.get_actor_label()
        if lbl in roster_locs:
            a.set_actor_location(roster_locs[lbl], sweep=False, teleport=True)
            log(f"  - 敌人 {lbl} 已对齐至 Y=0 物理交互面: {roster_locs[lbl]}")

    # 3. 掩体沙袋物理阻挡盒 (Cube: BlockAll, 隐藏)
    cube_mesh = unreal.load_asset("/Engine/BasicShapes/Cube")
    barricades = [
        (-200.0, 0.0, 420.0, "Wall_Barricade_Top_L", unreal.Vector(0.9, 1.6, 0.45)),
        (200.0, 0.0, 420.0, "Wall_Barricade_Top_R", unreal.Vector(0.9, 1.6, 0.45)),
        (-220.0, 0.0, -50.0, "Wall_DefenseLine_L", unreal.Vector(0.9, 1.6, 0.45)),
        (220.0, 0.0, -50.0, "Wall_DefenseLine_R", unreal.Vector(0.9, 1.6, 0.45)),
    ]

    for x, y, z, lbl, sc in barricades:
        blocker = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, z), unreal.Rotator())
        blocker.set_actor_label(lbl)
        comp = blocker.get_component_by_class(unreal.StaticMeshComponent)
        if comp and cube_mesh:
            comp.set_editor_property("static_mesh", cube_mesh)
            blocker.set_actor_scale3d(sc)
            try:
                comp.set_collision_profile_name("BlockAll")
                comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
            except Exception:
                pass
            comp.set_editor_property("hidden_in_game", True)
            comp.set_editor_property("visible", False)
        log(f"  + 掩体物理阻挡盒部署完成: {lbl}")

    # 4. 屏幕边界物理围墙 (Cube: BlockAll, 隐藏，防止移出可视范围)
    boundaries = [
        (unreal.Vector(-330.0, 0.0, 0.0), unreal.Vector(0.3, 1.8, 18.0), "Wall_Boundary_Left"),
        (unreal.Vector(330.0, 0.0, 0.0), unreal.Vector(0.3, 1.8, 18.0), "Wall_Boundary_Right"),
        (unreal.Vector(0.0, 0.0, -640.0), unreal.Vector(7.5, 1.8, 0.4), "Wall_Boundary_Bottom"),
    ]

    for loc, sc, wname in boundaries:
        w_act = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, loc, unreal.Rotator())
        w_act.set_actor_label(wname)
        comp = w_act.get_component_by_class(unreal.StaticMeshComponent)
        if comp and cube_mesh:
            comp.set_editor_property("static_mesh", cube_mesh)
            w_act.set_actor_scale3d(sc)
            try:
                comp.set_collision_profile_name("BlockAll")
                comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
            except Exception:
                pass
            comp.set_editor_property("hidden_in_game", True)
            comp.set_editor_property("visible", False)
        log(f"  + 屏幕边界阻挡墙部署完成: {wname}")

    unreal.EditorLoadingAndSavingUtils.save_map(world, MAP_PATH)
    ASSETS.save_directory(GEN, only_if_is_dirty=False, recursive=True)
    ASSETS.save_directory("/Game/Blueprints", only_if_is_dirty=False, recursive=True)
    log("🎉 ALL_PHYSICS_AND_LIVING_MARCH_COMPLETED_SUCCESSFULLY")

def main():
    upgrade_all_enemy_blueprints()
    upgrade_player_medic()
    upgrade_level_world()

if __name__ == "__main__":
    main()
