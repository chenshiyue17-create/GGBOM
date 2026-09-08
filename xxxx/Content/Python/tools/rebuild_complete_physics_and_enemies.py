# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》物理碰撞体系与全动态战术推进行军重构总脚本
1. 主角 BP_Player_Medic: 绑定实体 Box 碰撞盒，开启移动 bSweep=True (物理阻挡)
2. 敌人蓝图全家族 (7种): 绑定实体 Box 碰撞盒，写入 Tick 向下单向推进逻辑 (bSweep=True)
3. 关卡 MAP_GGBOM_Main: 部署真敌人蓝图实例，加固掩体与边界物理阻挡盒，统一 Y=0 交互面
================================================================================
"""
from __future__ import annotations
import unreal

GEN = "/Game/GGBOM"
MAP_PATH = f"{GEN}/Maps/MAP_GGBOM_Main"
PLAYER_BP_PATH = "/Game/Blueprints/Player/BP_Player_Medic"
ENEMY_BP_DIR = "/Game/Blueprints/Characters/Enemies"

ASSETS = unreal.EditorAssetLibrary
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary
SUBOBJECTS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)

def log(msg: str):
    print(f"[PhysicsRebuild] {msg}")
    unreal.log(f"[PhysicsRebuild] {msg}")

def pin(node: unreal.K2Node, name: str, output: bool) -> unreal.BlueprintGraphPin:
    values = BPLIB.list_output_pins(node) if output else BPLIB.list_input_pins(node)
    wanted = name.lower()
    exact = [p for p in values if str(PINLIB.get_pin_name(p)).lower() == wanted]
    if len(exact) == 1:
        return exact[0]
    raise RuntimeError(f"Pin {name} not found; available={[str(PINLIB.get_pin_name(p)) for p in values]}")

def set_value(node: unreal.K2Node, name: str, value) -> None:
    target = pin(node, name, False)
    if not PINLIB.set_pin_value(target, str(value)):
        raise RuntimeError(f"Default rejected: {name}={value}")

def connect(a: unreal.K2Node, a_pin: str, b: unreal.K2Node, b_pin: str) -> None:
    source, target = pin(a, a_pin, True), pin(b, b_pin, False)
    if not PINLIB.try_create_connection(source, target):
        raise RuntimeError(f"Connection rejected: {a_pin} -> {b_pin}")

def fn(editor: unreal.BlueprintGraphEditor, path: str, x: int, y: int) -> unreal.K2Node:
    node = editor.add_call_function_node(path)
    if not node:
        raise RuntimeError(f"Function node failed: {path}")
    node.set_node_pos(unreal.IntPoint(x, y))
    return node

def ensure_box_component(bp: unreal.Blueprint, comp_name: str, extent: unreal.Vector, profile: str = "Pawn"):
    """安全获取或新增实体 BoxComponent，避免重复套娃"""
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
        if not unreal.SubobjectDataBlueprintFunctionLibrary.is_handle_valid(h):
            raise RuntimeError(f"添加 BoxComponent 失败: {reason}")
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
        target_comp.set_editor_property("visible", True)
        target_comp.set_editor_property("hidden_in_game", False)
        
    return target_comp

# ==============================================================================
# 1. 重构主角 BP_Player_Medic (启用移动物理阻挡 Sweep=True)
# ==============================================================================
def upgrade_player_medic():
    log("🎮 [1/3] 正在升级主角 BP_Player_Medic 碰撞与物理阻挡...")
    import implement_bullet_direction_fullfix
    implement_bullet_direction_fullfix.rewrite_player_medic()
    log("✅ 主角 BP_Player_Medic 物理升级完成！")

# ==============================================================================
# 2. 重构 7 类敌人蓝图 (实体碰撞盒 + 战术向下推进行军逻辑)
# ==============================================================================
ENEMY_DEFS = [
    {
        "name": "BP_Enemy_ZombieWalker",
        "display": "基础感染行尸",
        "flipbook": "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Zombie/01_Zombie_Walker_Basic/Flipbooks/FB_T_Zombie_WalkerBasic_Sheet.FB_T_Zombie_WalkerBasic_Sheet",
        "scale": 0.45,
        "speed": 65.0,
        "extent": unreal.Vector(26.0, 60.0, 36.0),
        "hp": 60.0
    },
    {
        "name": "BP_Enemy_ZombieRunner",
        "display": "敏捷疾跑行尸",
        "flipbook": "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Zombie/05_Zombie_Runner_Agile/Flipbooks/FB_T_Zombie_RunnerAgile_Sheet.FB_T_Zombie_RunnerAgile_Sheet",
        "scale": 0.45,
        "speed": 115.0,
        "extent": unreal.Vector(26.0, 60.0, 36.0),
        "hp": 45.0
    },
    {
        "name": "BP_Enemy_MutantHound",
        "display": "疾行变异猎犬",
        "flipbook": "/Game/P01/Imported/Content/Asset/Art/02_Enemies/MutantHound/Run/Dir_01_Down/Flipbooks/FB_T_Hound_Run_Dir_01_Down_Sheet.FB_T_Hound_Run_Dir_01_Down_Sheet",
        "scale": 0.48,
        "speed": 160.0,
        "extent": unreal.Vector(30.0, 60.0, 32.0),
        "hp": 90.0
    },
    {
        "name": "BP_Enemy_VenomShooter",
        "display": "毒液喷射行尸",
        "flipbook": "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Zombie/04_Zombie_Spitter_Minor/Flipbooks/FB_T_Zombie_SpitterMinor_Sheet.FB_T_Zombie_SpitterMinor_Sheet",
        "scale": 0.45,
        "speed": 55.0,
        "extent": unreal.Vector(26.0, 60.0, 36.0),
        "hp": 75.0
    },
    {
        "name": "BP_Enemy_ArmoredGuard",
        "display": "重装防暴行尸",
        "flipbook": "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Zombie/07_Zombie_Armored_Guard/Flipbooks/FB_T_Zombie_ArmoredGuard_Sheet.FB_T_Zombie_ArmoredGuard_Sheet",
        "scale": 0.50,
        "speed": 50.0,
        "extent": unreal.Vector(32.0, 60.0, 42.0),
        "hp": 160.0
    },
    {
        "name": "BP_Enemy_MutantBrute",
        "display": "重型蹒跚蛮兽",
        "flipbook": "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Zombie/11_Zombie_Shambler_Heavy/Flipbooks/FB_T_Zombie_ShamblerHeavy_Sheet.FB_T_Zombie_ShamblerHeavy_Sheet",
        "scale": 0.58,
        "speed": 40.0,
        "extent": unreal.Vector(38.0, 70.0, 48.0),
        "hp": 380.0
    },
    {
        "name": "BP_Boss_Overlord",
        "display": "深渊异化领主 Boss",
        "flipbook": "/Game/P01/Imported/Content/Asset/Art/02_Enemies/Boss_Overlord/Actions/Walk/Dir_01_Down/Flipbooks/FB_T_Boss_Walk_Dir_01_Down_Sheet.FB_T_Boss_Walk_Dir_01_Down_Sheet",
        "scale": 0.68,
        "speed": 30.0,
        "extent": unreal.Vector(55.0, 80.0, 65.0),
        "hp": 3000.0
    },
]

def build_living_enemy_bp(edef: dict) -> unreal.Blueprint:
    bp_path = f"{ENEMY_BP_DIR}/{edef['name']}"
    log(f"👾 [2/3] 重构实体敌人蓝图: {edef['display']} ({bp_path})...")
    
    if ASSETS.does_asset_exist(bp_path):
        ASSETS.delete_asset(bp_path)
    bp = BPLIB.create_blueprint_asset_with_parent(bp_path, unreal.PaperFlipbookActor.static_class())
    if not bp:
        raise RuntimeError(f"无法创建敌人蓝图: {bp_path}")

    # 1. 挂载实体 BoxComponent 物理碰撞盒 (Pawn 碰撞)
    ensure_box_component(bp, "EnemyCollision", edef["extent"], "Pawn")

    # 2. 写入变量
    graph = BPLIB.find_event_graph(bp)
    editor = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    real_type = BPLIB.get_basic_type_by_name("real")
    editor.add_member_variable("MaxHealth", real_type, str(edef["hp"]))
    editor.add_member_variable("CurrentHealth", real_type, str(edef["hp"]))
    editor.add_member_variable("MoveSpeed", real_type, str(edef["speed"]))

    # 3. 构建单链路平滑向下推进行走逻辑 (bSweep = True)
    step = edef.get("step", 2.0)
    tick_node = editor.find_event_node("ReceiveTick")
    move_node = editor.add_call_function_node("/Script/Engine.Actor.K2_AddActorWorldOffset")
    set_value(move_node, "bSweep", "true")
    set_value(move_node, "DeltaLocation", f"0,0,-{step}")
    connect(tick_node, "then", move_node, "execute")

    BPLIB.compile_blueprint(bp)

    # 4. CDO 绑定专属 4 帧 Flipbook
    cdo = unreal.get_default_object(bp.generated_class())
    if cdo:
        fb_comp = cdo.get_component_by_class(unreal.PaperFlipbookComponent)
        if fb_comp:
            fb = unreal.load_asset(edef["flipbook"])
            if fb:
                fb_comp.set_editor_property("source_flipbook", fb)
            sc = edef["scale"]
            fb_comp.set_editor_property("relative_scale3d", unreal.Vector(sc, sc, sc))
            fb_comp.set_editor_property("translucency_sort_priority", 150)
            try:
                fb_comp.set_collision_profile_name("NoCollision")
                fb_comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            except Exception:
                pass
            fb_comp.set_editor_property("visible", True)
            fb_comp.set_editor_property("hidden_in_game", False)

    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"  + {edef['name']} 实体化与推进行军逻辑已就绪！")
    return bp

# ==============================================================================
# 3. 重构关卡 MAP_GGBOM_Main (部署真怪、加固掩体与边界阻挡盒)
# ==============================================================================
def deploy_living_world():
    log(f"🗺️ [3/3] 正在装配主关卡 {MAP_PATH} (真怪部署 + 掩体/边界物理阻挡)...")
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
    if not world:
        raise RuntimeError(f"无法加载主地图: {MAP_PATH}")

    # 1. 清除旧有的怪物与旧阻挡体
    level_actors = unreal.EditorLevelLibrary.get_all_level_actors()
    destroyed = 0
    for a in level_actors:
        lbl = a.get_actor_label()
        if any(lbl.startswith(k) for k in ["Enemy_", "Boss_", "Live_", "Wall_"]):
            unreal.EditorLevelLibrary.destroy_actor(a)
            destroyed += 1
    log(f"  - 已清理历史旧怪及旧阻挡器: {destroyed} 个")

    # 2. 掩体阻挡加固 (为已有 Barricade 与 DefenseLine 附加实体 Box 碰撞体)
    sp_barricade = unreal.load_asset(f"{GEN}/Art/Sprites/SP_Barricade")
    barricades = [
        (-200.0, 30.0, 420.0, "Barricade_Top_L"),
        (200.0, 30.0, 420.0, "Barricade_Top_R"),
        (-220.0, 30.0, -50.0, "DefenseLine_L"),
        (220.0, 30.0, -50.0, "DefenseLine_R"),
    ]
    
    # 查找并确保掩体实体阻挡盒存在
    for x, y, z, lbl in barricades:
        # 寻找已有 actor 或新建
        cand = [a for a in unreal.EditorLevelLibrary.get_all_level_actors() if a.get_actor_label() == lbl]
        act = cand[0] if cand else None
        if not act and sp_barricade:
            act = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.PaperSpriteActor, unreal.Vector(x, y, z), unreal.Rotator())
            comp = act.get_component_by_class(unreal.PaperSpriteComponent)
            comp.set_editor_property("source_sprite", sp_barricade)
            comp.set_editor_property("translucency_sort_priority", 50)
            act.set_actor_scale3d(unreal.Vector(0.55, 0.55, 0.55))
            act.set_actor_label(lbl)

        # 放置专用物理阻挡盒 (覆盖 X=65, Y=80深度, Z=25)
        blocker = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, 0.0, z), unreal.Rotator())
        blocker.set_actor_label(f"Wall_{lbl}")
        # 使用 BoxComponent 或隐藏 Cube
        sm_comp = blocker.get_component_by_class(unreal.StaticMeshComponent)
        cube_mesh = unreal.load_asset("/Engine/BasicShapes/Cube")
        if cube_mesh:
            sm_comp.set_editor_property("static_mesh", cube_mesh)
            # 缩放: Cube默认 100x100x100 -> 0.9 x 1.2 x 0.4 => 90 x 120 x 40
            blocker.set_actor_scale3d(unreal.Vector(0.9, 1.2, 0.4))
            try:
                sm_comp.set_collision_profile_name("BlockAll")
            except Exception:
                pass
            try:
                sm_comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
            except Exception:
                pass
            sm_comp.set_editor_property("hidden_in_game", True)
            sm_comp.set_editor_property("visible", False)

    # 3. 屏幕边界围墙 (左、右、下阻挡，防止角色移出可视区域)
    boundaries = [
        # 左边界 (X=-330, 垂直高覆盖)
        (unreal.Vector(-330.0, 0.0, 0.0), unreal.Vector(0.3, 1.5, 18.0), "Wall_Boundary_Left"),
        # 右边界 (X=+330)
        (unreal.Vector(330.0, 0.0, 0.0), unreal.Vector(0.3, 1.5, 18.0), "Wall_Boundary_Right"),
        # 底部边界 (Z=-650)
        (unreal.Vector(0.0, 0.0, -650.0), unreal.Vector(7.5, 1.5, 0.4), "Wall_Boundary_Bottom"),
    ]
    cube_mesh = unreal.load_asset("/Engine/BasicShapes/Cube")
    for loc, scale, wname in boundaries:
        w_act = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, loc, unreal.Rotator())
        w_act.set_actor_label(wname)
        comp = w_act.get_component_by_class(unreal.StaticMeshComponent)
        if cube_mesh:
            comp.set_editor_property("static_mesh", cube_mesh)
        w_act.set_actor_scale3d(scale)
        try:
            comp.set_collision_profile_name("BlockAll")
        except Exception:
            pass
        try:
            comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
        except Exception:
            pass
        comp.set_editor_property("hidden_in_game", True)
        comp.set_editor_property("visible", False)

    # 4. 部署真实动态敌人军团 (Y=0.0，与玩家处于同一交互空间)
    spawn_roster = [
        # 前锋波次 (Z = +220~260, 基础行尸推进)
        ("BP_Enemy_ZombieWalker", unreal.Vector(-140.0, 0.0, 240.0), "Enemy_Zombie_01"),
        ("BP_Enemy_ZombieWalker", unreal.Vector(0.0, 0.0, 200.0), "Enemy_Zombie_02"),
        ("BP_Enemy_ZombieWalker", unreal.Vector(140.0, 0.0, 240.0), "Enemy_Zombie_03"),
        
        # 特种突变波次 (Z = +360~400, 疾跑者与毒液喷射)
        ("BP_Enemy_ZombieRunner", unreal.Vector(-100.0, 0.0, 360.0), "Enemy_Runner_01"),
        ("BP_Enemy_VenomShooter", unreal.Vector(100.0, 0.0, 360.0), "Enemy_VenomShooter_01"),
        
        # 侧翼疾行猎犬 (Z = +460)
        ("BP_Enemy_MutantHound", unreal.Vector(-200.0, 0.0, 460.0), "Enemy_Hound_01"),
        ("BP_Enemy_MutantHound", unreal.Vector(200.0, 0.0, 460.0), "Enemy_Hound_02"),
        
        # 重装蛮兽 (Z = +540)
        ("BP_Enemy_MutantBrute", unreal.Vector(0.0, 0.0, 540.0), "Enemy_Brute_01"),
        
        # 终极领主 Boss (Z = +660)
        ("BP_Boss_Overlord", unreal.Vector(0.0, 0.0, 660.0), "Boss_Overlord_Live"),
    ]

    for bp_name, loc, lbl in spawn_roster:
        bp_path = f"{ENEMY_BP_DIR}/{bp_name}"
        bp = unreal.load_asset(bp_path)
        if not bp:
            log(f"⚠️ 未找到蓝图: {bp_path}")
            continue
        gen_cls = bp.generated_class()
        act = unreal.EditorLevelLibrary.spawn_actor_from_class(gen_cls, loc, unreal.Rotator())
        if act:
            act.set_actor_label(lbl)
            log(f"  + 成功实装动态推进行军实体: {lbl} ({bp_name}) @ {loc}")

    unreal.EditorLoadingAndSavingUtils.save_map(world, MAP_PATH)
    ASSETS.save_directory(GEN, only_if_is_dirty=False, recursive=True)
    ASSETS.save_directory("/Game/Blueprints", only_if_is_dirty=False, recursive=True)
    log("ALL_PHYSICS_AND_LIVING_ENEMIES_DEPLOYED_SUCCESSFULLY")

def main():
    upgrade_player_medic()
    for edef in ENEMY_DEFS:
        build_living_enemy_bp(edef)
    deploy_living_world()

if __name__ == "__main__":
    main()
