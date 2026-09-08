# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》全量完整游戏流程系统装配脚本 (健壮闭环版)
1. 配置 BP_Pickup_ExpGem：补给/经验包，碰撞玩家自毁吸收
2. 配置 BP_ProjectileBase：标准子弹，高速直线飞行，2.5s兜底自毁
3. 配置 BP_Enemy_ZombieWalker：4帧单向下压推进行尸，受击扣血，死亡掉落补给，触底越界销毁
4. 配置 BP_Enemy_MutantHound：变异猎犬追逐AI，受击扣血，死亡掉落补给
5. 配置 BP_Boss_Overlord：深渊领主高血量 Boss，缓慢压迫，受击扣血，死亡击杀
6. 配置 BP_StageWaveManager：40秒波次时钟推进，动态刷怪调度，胜利重启
7. 关卡装配：部署 BP_StageWaveManager，保存干净关卡
================================================================================
"""
from __future__ import annotations
from pathlib import Path
import json
import unreal

ASSETS = unreal.EditorAssetLibrary
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()

ROOT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
OUT_DIR = ROOT / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 核心路径
PLAYER_PATH = "/Game/Blueprints/Player/BP_Player_Medic"
PROJ_PATH = "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase"
ZOMBIE_PATH = "/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker"
HOUND_PATH = "/Game/Blueprints/Characters/Enemies/BP_Enemy_MutantHound"
BOSS_PATH = "/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord"
EXPGEM_PATH = "/Game/Blueprints/Pickups/BP_Pickup_ExpGem"
WAVEMGR_PATH = "/Game/Blueprints/Stage/BP_StageWaveManager"
MAP_PATH = "/Game/GGBOM/Maps/MAP_GGBOM_Main"

MEDPOD_SPRITE = "/Game/P01/Imported/Content/Asset/Art/04_Props/05_MedicalSupplyPod/Sprites/SP_T_Prop_MedPod_01_Intact"

def log(msg: str):
    print(f"[GameFlow] {msg}", flush=True)
    unreal.log(f"[GameFlow] {msg}")
    try:
        import sys
        sys.stdout.flush()
    except Exception:
        pass

def pin(node: unreal.K2Node, name: str, output: bool) -> unreal.BlueprintGraphPin:
    values = BPLIB.list_output_pins(node) if output else BPLIB.list_input_pins(node)
    found = [p for p in values if str(PINLIB.get_pin_name(p)).lower() == name.lower()]
    if len(found) != 1:
        available = [str(PINLIB.get_pin_name(p)) for p in values]
        raise RuntimeError(f"Pin {name} missing on {BPLIB.get_node_title(node)}; available={available}")
    return found[0]

def set_value(node: unreal.K2Node, name: str, value) -> None:
    if not PINLIB.set_pin_value(pin(node, name, False), str(value)):
        raise RuntimeError(f"Default rejected: {BPLIB.get_node_title(node)}.{name}={value}")

def connect(a: unreal.K2Node, a_name: str, b: unreal.K2Node, b_name: str) -> None:
    source, target = pin(a, a_name, True), pin(b, b_name, False)
    if not PINLIB.try_create_connection(source, target):
        raise RuntimeError(f"Connection rejected: {BPLIB.get_node_title(a)}.{a_name} -> {BPLIB.get_node_title(b)}.{b_name}")

def fn(editor: unreal.BlueprintGraphEditor, path: str, x: int, y: int) -> unreal.K2Node:
    node = editor.add_call_function_node(path)
    if not node:
        raise RuntimeError(f"Cannot create function node: {path}")
    node.set_node_pos(unreal.IntPoint(x, y))
    return node

def place(node: unreal.K2Node, x: int, y: int) -> unreal.K2Node:
    node.set_node_pos(unreal.IntPoint(x, y))
    return node

def event_editor(bp: unreal.Blueprint) -> unreal.BlueprintGraphEditor:
    return unreal.BlueprintGraphEditor.get_graph_editor(BPLIB.find_event_graph(bp))

def clean_graph_preserve_native_events(bp: unreal.Blueprint) -> tuple[unreal.K2Node, unreal.K2Node]:
    """清空图表但严格保留 ReceiveBeginPlay 与 ReceiveTick 原生事件节点（先断开引脚防止悬空指针）"""
    editor = event_editor(bp)
    begin_node = None
    tick_node = None
    try:
        begin_node = editor.find_event_node("ReceiveBeginPlay")
    except Exception:
        pass
    try:
        tick_node = editor.find_event_node("ReceiveTick")
    except Exception:
        pass

    keep = set()
    if begin_node: keep.add(begin_node.get_path_name())
    if tick_node: keep.add(tick_node.get_path_name())

    all_nodes = editor.list_all_nodes()
    # 1. 彻底断开待删除节点的所有引脚连接，防止残留引脚导致底层拓扑损坏
    for node in all_nodes:
        if node.get_path_name() not in keep:
            for p in BPLIB.list_all_pins(node):
                try:
                    PINLIB.break_pin_links(p)
                except Exception:
                    pass
                    
    # 2. 断开保留节点的连线
    if begin_node:
        for p in BPLIB.list_all_pins(begin_node):
            try:
                PINLIB.break_pin_links(p)
            except Exception:
                pass
    if tick_node:
        for p in BPLIB.list_all_pins(tick_node):
            try:
                PINLIB.break_pin_links(p)
            except Exception:
                pass

    stale = [node for node in all_nodes if node.get_path_name() not in keep]
    if stale:
        editor.remove_nodes(stale)
    return begin_node, tick_node

def reset_variables(bp: unreal.Blueprint, specs: list[tuple[str, unreal.EdGraphPinType, str, str]]) -> None:
    editor = event_editor(bp)
    existing = set(str(name) for name in BPLIB.list_member_variable_names(bp, False))
    for name, pin_type, default, category in specs:
        if name not in existing:
            editor.add_member_variable(name, pin_type, default)
        BPLIB.set_blueprint_variable_category(bp, name, unreal.Text(category))
        BPLIB.set_blueprint_variable_instance_editable(bp, name, True)

# ==============================================================================
# 1. 配置 BP_Pickup_ExpGem (经验/医疗补给包)
# ==============================================================================
def build_exp_gem(real_type):
    log(f"🚀 [1/6] 配置医疗补给/经验包: {EXPGEM_PATH}...")
    bp = unreal.load_asset(EXPGEM_PATH)
    if not bp:
        bp = BPLIB.create_blueprint_asset_with_parent(EXPGEM_PATH, unreal.Actor.static_class())
    
    begin, tick = clean_graph_preserve_native_events(bp)
    reset_variables(bp, [
        ("ExpAmount", real_type, "25.0", "Reward"),
    ])
    
    cdo = unreal.get_default_object(bp.generated_class())
    if cdo:
        sprite_comp = cdo.get_component_by_class(unreal.PaperSpriteComponent)
        if sprite_comp:
            sp = unreal.load_asset(MEDPOD_SPRITE) or unreal.load_asset("/Game/GGBOM/Art/Sprites/SP_RedBarrel.SP_RedBarrel")
            if sp:
                sprite_comp.set_editor_property("source_sprite", sp)
            sprite_comp.set_editor_property("relative_scale3d", unreal.Vector(0.35, 0.35, 0.35))
            sprite_comp.set_editor_property("translucency_sort_priority", 1500)
            sprite_comp.set_collision_profile_name("OverlapAllDynamic")
            sprite_comp.set_editor_property("generate_overlap_events", True)
            
    ed = event_editor(bp)
    if not tick:
        tick = ed.find_event_node("ReceiveTick")
    if not tick:
        raise RuntimeError(f"{EXPGEM_PATH} 缺失 ReceiveTick 事件节点")
    place(tick, 0, 0)
    
    get_overlap = fn(ed, "/Script/Engine.Actor.GetOverlappingActors", 240, 100)
    set_value(get_overlap, "ClassFilter", "Class'/Game/Blueprints/Player/BP_Player_Medic.BP_Player_Medic_C'")
    
    has_player = fn(ed, "/Script/Engine.KismetArrayLibrary.Array_Length", 480, 100)
    connect(get_overlap, "OverlappingActors", has_player, "TargetArray")
    
    is_touched = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_IntInt", 660, 100)
    connect(has_player, "ReturnValue", is_touched, "A")
    set_value(is_touched, "B", 0)
    
    branch = place(ed.add_branch_node(), 840, 0)
    connect(tick, "then", branch, "execute")
    connect(is_touched, "ReturnValue", branch, "Condition")
    
    destroy = fn(ed, "/Script/Engine.Actor.K2_DestroyActor", 1060, -40)
    connect(branch, "then", destroy, "execute")
    
    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"✅ BP_Pickup_ExpGem 补给拾取蓝图构建成功！")
    return bp

# ==============================================================================
# 2. 配置 BP_ProjectileBase (标准子弹高速飞行与自毁)
# ==============================================================================
def build_projectile(vector_type, real_type):
    log(f"🚀 [2/6] 配置标准子弹蓝图: {PROJ_PATH}...")
    bp = unreal.load_asset(PROJ_PATH)
    if not bp:
        bp = BPLIB.create_blueprint_asset_with_parent(PROJ_PATH, unreal.Actor.static_class())
        
    begin, _ = clean_graph_preserve_native_events(bp)
    reset_variables(bp, [
        ("Damage", real_type, "35.0", "Combat"),
    ])
    
    cdo = unreal.get_default_object(bp.generated_class())
    if cdo:
        sprite_comp = cdo.get_component_by_class(unreal.PaperSpriteComponent)
        if sprite_comp:
            sprite_comp.set_collision_profile_name("OverlapAllDynamic")
            sprite_comp.set_editor_property("generate_overlap_events", True)
            sprite_comp.set_editor_property("translucency_sort_priority", 2800)
            
    ed = event_editor(bp)
    if not begin:
        try:
            begin = ed.find_event_node("ReceiveBeginPlay")
        except Exception:
            pass
            
    if begin:
        place(begin, 0, 0)
        # 2.5 秒兜底生命周期自毁
        lifespan = fn(ed, "/Script/Engine.Actor.SetLifeSpan", 240, 0)
        set_value(lifespan, "InLifespan", 2.5)
        connect(begin, "then", lifespan, "execute")
    
    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"✅ BP_ProjectileBase 子弹物理飞行与自毁配置完成！")
    return bp

# ==============================================================================
# 3. 配置 BP_Enemy_ZombieWalker (4帧单向下压推进行尸 + 受击扣血死亡掉落)
# ==============================================================================
def build_zombie_walker(real_type):
    log(f"🚀 [3/6] 配置4帧单向推进行尸: {ZOMBIE_PATH}...")
    bp = unreal.load_asset(ZOMBIE_PATH)
    if not bp:
        bp = BPLIB.create_blueprint_asset_with_parent(ZOMBIE_PATH, unreal.Actor.static_class())
        
    begin, tick = clean_graph_preserve_native_events(bp)
    reset_variables(bp, [
        ("CurrentHealth", real_type, "60.0", "Stats"),
    ])
    
    cdo = unreal.get_default_object(bp.generated_class())
    if cdo:
        sprite_comp = cdo.get_component_by_class(unreal.PaperSpriteComponent) or \
                      cdo.get_component_by_class(unreal.PaperFlipbookComponent)
        if sprite_comp:
            sprite_comp.set_editor_property("relative_scale3d", unreal.Vector(0.55, 0.55, 0.55))
            sprite_comp.set_editor_property("translucency_sort_priority", 350)
            sprite_comp.set_collision_profile_name("OverlapAllDynamic")
            sprite_comp.set_editor_property("generate_overlap_events", True)
            
    ed = event_editor(bp)
    if not tick: tick = ed.find_event_node("ReceiveTick")
    place(tick, 0, 0)
    
    # 1. 30FPS 固定向下 (Z 轴负方向) 推进 2.5 uu/帧
    move = fn(ed, "/Script/Engine.Actor.K2_AddActorWorldOffset", 240, 0)
    set_value(move, "DeltaLocation", "0,0,-2.5")
    set_value(move, "bSweep", "true")
    connect(tick, "then", move, "execute")
    
    # 2. 受击判定: 检测是否重叠 BP_ProjectileBase
    get_overlap_bullet = fn(ed, "/Script/Engine.Actor.GetOverlappingActors", 480, 160)
    set_value(get_overlap_bullet, "ClassFilter", "Class'/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase.BP_ProjectileBase_C'")
    
    bullet_count = fn(ed, "/Script/Engine.KismetArrayLibrary.Array_Length", 700, 160)
    connect(get_overlap_bullet, "OverlappingActors", bullet_count, "TargetArray")
    
    has_bullet = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_IntInt", 880, 160)
    connect(bullet_count, "ReturnValue", has_bullet, "A")
    set_value(has_bullet, "B", 0)
    
    branch_hit = place(ed.add_branch_node(), 1060, 0)
    connect(move, "then", branch_hit, "execute")
    connect(has_bullet, "ReturnValue", branch_hit, "Condition")
    
    # 命中: 销毁子弹
    first_bullet = fn(ed, "/Script/Engine.KismetArrayLibrary.Array_Get", 1260, 140)
    connect(get_overlap_bullet, "OverlappingActors", first_bullet, "TargetArray")
    set_value(first_bullet, "Index", 0)
    
    destroy_bullet = fn(ed, "/Script/Engine.Actor.K2_DestroyActor", 1460, 0)
    connect(branch_hit, "then", destroy_bullet, "execute")
    connect(first_bullet, "ReturnValue", destroy_bullet, "Target")
    
    # 扣减生命值 (每次受击扣 30 HP)
    cur_hp = place(ed.add_get_member_variable_node("CurrentHealth"), 1460, 140)
    sub_hp = fn(ed, "/Script/Engine.KismetMathLibrary.Subtract_DoubleDouble", 1680, 140)
    connect(cur_hp, "CurrentHealth", sub_hp, "A")
    set_value(sub_hp, "B", 30.0)
    
    set_hp = place(ed.add_set_member_variable_node("CurrentHealth"), 1880, 0)
    connect(destroy_bullet, "then", set_hp, "execute")
    connect(sub_hp, "ReturnValue", set_hp, "CurrentHealth")
    
    # 死亡判定 (Health <= 0)
    is_dead = fn(ed, "/Script/Engine.KismetMathLibrary.LessEqual_DoubleDouble", 1880, 140)
    connect(sub_hp, "ReturnValue", is_dead, "A")
    set_value(is_dead, "B", 0.0)
    
    branch_dead = place(ed.add_branch_node(), 2080, 0)
    connect(set_hp, "then", branch_dead, "execute")
    connect(is_dead, "ReturnValue", branch_dead, "Condition")
    
    # 死亡生成医疗补给包
    my_loc = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 2080, 260)
    trans = fn(ed, "/Script/Engine.KismetMathLibrary.MakeTransform", 2300, 240)
    connect(my_loc, "ReturnValue", trans, "Location")
    set_value(trans, "Scale", "1,1,1")
    
    spawn_gem = fn(ed, "/Script/Engine.GameplayStatics.BeginDeferredActorSpawnFromClass", 2520, 0)
    set_value(spawn_gem, "ActorClass", "Class'/Game/Blueprints/Pickups/BP_Pickup_ExpGem.BP_Pickup_ExpGem_C'")
    connect(branch_dead, "then", spawn_gem, "execute")
    connect(trans, "ReturnValue", spawn_gem, "SpawnTransform")
    
    finish_gem = fn(ed, "/Script/Engine.GameplayStatics.FinishSpawningActor", 2780, 0)
    connect(spawn_gem, "then", finish_gem, "execute")
    connect(spawn_gem, "ReturnValue", finish_gem, "Actor")
    connect(trans, "ReturnValue", finish_gem, "SpawnTransform")
    
    destroy_zombie = fn(ed, "/Script/Engine.Actor.K2_DestroyActor", 3020, 0)
    connect(finish_gem, "then", destroy_zombie, "execute")
    
    # 3. 越界触底检查: 当 Z < -550 时销毁自身
    loc_for_bottom = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 480, -160)
    break_vec = fn(ed, "/Script/Engine.KismetMathLibrary.BreakVector", 700, -160)
    connect(loc_for_bottom, "ReturnValue", break_vec, "InVec")
    
    is_bottom = fn(ed, "/Script/Engine.KismetMathLibrary.Less_DoubleDouble", 900, -160)
    connect(break_vec, "Z", is_bottom, "A")
    set_value(is_bottom, "B", -550.0)
    
    branch_bottom = place(ed.add_branch_node(), 1100, -120)
    connect(branch_hit, "else", branch_bottom, "execute")
    connect(branch_dead, "else", branch_bottom, "execute")
    connect(is_bottom, "ReturnValue", branch_bottom, "Condition")
    
    destroy_bottom = fn(ed, "/Script/Engine.Actor.K2_DestroyActor", 1320, -120)
    connect(branch_bottom, "then", destroy_bottom, "execute")
    
    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"✅ BP_Enemy_ZombieWalker 行尸推进行为与受击掉落配置完成！")
    return bp

# ==============================================================================
# 4. 配置 BP_Enemy_MutantHound (变异猎犬追逐AI + 受击掉落)
# ==============================================================================
def build_mutant_hound(real_type):
    log(f"🚀 [4/6] 配置变异猎犬追逐AI: {HOUND_PATH}...")
    bp = unreal.load_asset(HOUND_PATH)
    if not bp:
        bp = BPLIB.create_blueprint_asset_with_parent(HOUND_PATH, unreal.Actor.static_class())
        
    begin, tick = clean_graph_preserve_native_events(bp)
    reset_variables(bp, [
        ("CurrentHealth", real_type, "90.0", "Stats"),
    ])
    
    cdo = unreal.get_default_object(bp.generated_class())
    if cdo:
        sprite_comp = cdo.get_component_by_class(unreal.PaperFlipbookComponent) or \
                      cdo.get_component_by_class(unreal.PaperSpriteComponent)
        if sprite_comp:
            fb = unreal.load_asset("/Game/P01/Imported/Content/Asset/Art/02_Enemies/MutantHound/Run/Dir_01_Down/Flipbooks/FB_T_Hound_Run_Dir_01_Down_Sheet")
            if fb and hasattr(sprite_comp, "set_flipbook"):
                sprite_comp.set_flipbook(fb)
            sprite_comp.set_editor_property("relative_scale3d", unreal.Vector(0.5, 0.5, 0.5))
            sprite_comp.set_editor_property("translucency_sort_priority", 360)
            sprite_comp.set_collision_profile_name("OverlapAllDynamic")
            sprite_comp.set_editor_property("generate_overlap_events", True)
            
    ed = event_editor(bp)
    if not tick: tick = ed.find_event_node("ReceiveTick")
    place(tick, 0, 0)
    
    # 1. 获取玩家位置并追击 (每帧移动 4.5 uu)
    player = fn(ed, "/Script/Engine.GameplayStatics.GetPlayerPawn", 220, -100)
    set_value(player, "PlayerIndex", 0)
    
    player_loc = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 440, -100)
    connect(player, "ReturnValue", player_loc, "Target")
    
    my_loc = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 440, 60)
    
    diff = fn(ed, "/Script/Engine.KismetMathLibrary.Subtract_VectorVector", 660, 0)
    connect(player_loc, "ReturnValue", diff, "A")
    connect(my_loc, "ReturnValue", diff, "B")
    
    dir_norm = fn(ed, "/Script/Engine.KismetMathLibrary.Normal", 880, 0)
    connect(diff, "ReturnValue", dir_norm, "A")
    
    step = fn(ed, "/Script/Engine.KismetMathLibrary.Multiply_VectorFloat", 1100, 0)
    connect(dir_norm, "ReturnValue", step, "A")
    set_value(step, "B", 4.5)
    
    move = fn(ed, "/Script/Engine.Actor.K2_AddActorWorldOffset", 1320, 0)
    set_value(move, "bSweep", "true")
    connect(tick, "then", move, "execute")
    connect(step, "ReturnValue", move, "DeltaLocation")
    
    # 2. 受击检测
    get_overlap_bullet = fn(ed, "/Script/Engine.Actor.GetOverlappingActors", 1540, 160)
    set_value(get_overlap_bullet, "ClassFilter", "Class'/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase.BP_ProjectileBase_C'")
    
    bullet_count = fn(ed, "/Script/Engine.KismetArrayLibrary.Array_Length", 1760, 160)
    connect(get_overlap_bullet, "OverlappingActors", bullet_count, "TargetArray")
    
    has_bullet = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_IntInt", 1940, 160)
    connect(bullet_count, "ReturnValue", has_bullet, "A")
    set_value(has_bullet, "B", 0)
    
    branch_hit = place(ed.add_branch_node(), 2120, 0)
    connect(move, "then", branch_hit, "execute")
    connect(has_bullet, "ReturnValue", branch_hit, "Condition")
    
    # 命中子弹销毁
    first_bullet = fn(ed, "/Script/Engine.KismetArrayLibrary.Array_Get", 2320, 140)
    connect(get_overlap_bullet, "OverlappingActors", first_bullet, "TargetArray")
    set_value(first_bullet, "Index", 0)
    
    destroy_bullet = fn(ed, "/Script/Engine.Actor.K2_DestroyActor", 2520, 0)
    connect(branch_hit, "then", destroy_bullet, "execute")
    connect(first_bullet, "ReturnValue", destroy_bullet, "Target")
    
    # 扣血 30 HP
    cur_hp = place(ed.add_get_member_variable_node("CurrentHealth"), 2520, 140)
    sub_hp = fn(ed, "/Script/Engine.KismetMathLibrary.Subtract_DoubleDouble", 2740, 140)
    connect(cur_hp, "CurrentHealth", sub_hp, "A")
    set_value(sub_hp, "B", 30.0)
    
    set_hp = place(ed.add_set_member_variable_node("CurrentHealth"), 2940, 0)
    connect(destroy_bullet, "then", set_hp, "execute")
    connect(sub_hp, "ReturnValue", set_hp, "CurrentHealth")
    
    is_dead = fn(ed, "/Script/Engine.KismetMathLibrary.LessEqual_DoubleDouble", 2940, 140)
    connect(sub_hp, "ReturnValue", is_dead, "A")
    set_value(is_dead, "B", 0.0)
    
    branch_dead = place(ed.add_branch_node(), 3140, 0)
    connect(set_hp, "then", branch_dead, "execute")
    connect(is_dead, "ReturnValue", branch_dead, "Condition")
    
    hound_loc = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 3140, 260)
    trans = fn(ed, "/Script/Engine.KismetMathLibrary.MakeTransform", 3360, 240)
    connect(hound_loc, "ReturnValue", trans, "Location")
    set_value(trans, "Scale", "1,1,1")
    
    spawn_gem = fn(ed, "/Script/Engine.GameplayStatics.BeginDeferredActorSpawnFromClass", 3580, 0)
    set_value(spawn_gem, "ActorClass", "Class'/Game/Blueprints/Pickups/BP_Pickup_ExpGem.BP_Pickup_ExpGem_C'")
    connect(branch_dead, "then", spawn_gem, "execute")
    connect(trans, "ReturnValue", spawn_gem, "SpawnTransform")
    
    finish_gem = fn(ed, "/Script/Engine.GameplayStatics.FinishSpawningActor", 3840, 0)
    connect(spawn_gem, "then", finish_gem, "execute")
    connect(spawn_gem, "ReturnValue", finish_gem, "Actor")
    connect(trans, "ReturnValue", finish_gem, "SpawnTransform")
    
    destroy_hound = fn(ed, "/Script/Engine.Actor.K2_DestroyActor", 4080, 0)
    connect(finish_gem, "then", destroy_hound, "execute")
    
    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"✅ BP_Enemy_MutantHound 追逐AI与伤害闭环配置完成！")
    return bp

# ==============================================================================
# 5. 配置 BP_Boss_Overlord (深渊领主 Boss)
# ==============================================================================
def build_boss_overlord(real_type):
    log(f"🚀 [5/6] 配置深渊领主 Boss: {BOSS_PATH}...")
    bp = unreal.load_asset(BOSS_PATH)
    if not bp:
        bp = BPLIB.create_blueprint_asset_with_parent(BOSS_PATH, unreal.Actor.static_class())
        
    begin, tick = clean_graph_preserve_native_events(bp)
    reset_variables(bp, [
        ("CurrentHealth", real_type, "300.0", "Boss Stats"),
    ])
    
    cdo = unreal.get_default_object(bp.generated_class())
    if cdo:
        sprite_comp = cdo.get_component_by_class(unreal.PaperSpriteComponent) or \
                      cdo.get_component_by_class(unreal.PaperFlipbookComponent)
        if sprite_comp:
            sprite_comp.set_editor_property("relative_scale3d", unreal.Vector(0.75, 0.75, 0.75))
            sprite_comp.set_editor_property("translucency_sort_priority", 2000)
            sprite_comp.set_collision_profile_name("OverlapAllDynamic")
            sprite_comp.set_editor_property("generate_overlap_events", True)
            
    ed = event_editor(bp)
    if not tick: tick = ed.find_event_node("ReceiveTick")
    place(tick, 0, 0)
    
    # 1. 缓慢向下压迫 (0.8 uu/帧)
    move = fn(ed, "/Script/Engine.Actor.K2_AddActorWorldOffset", 240, 0)
    set_value(move, "DeltaLocation", "0,0,-0.8")
    set_value(move, "bSweep", "true")
    connect(tick, "then", move, "execute")
    
    # 2. 受击检测与扣血
    get_overlap_bullet = fn(ed, "/Script/Engine.Actor.GetOverlappingActors", 480, 160)
    set_value(get_overlap_bullet, "ClassFilter", "Class'/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase.BP_ProjectileBase_C'")
    
    bullet_count = fn(ed, "/Script/Engine.KismetArrayLibrary.Array_Length", 700, 160)
    connect(get_overlap_bullet, "OverlappingActors", bullet_count, "TargetArray")
    
    has_bullet = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_IntInt", 880, 160)
    connect(bullet_count, "ReturnValue", has_bullet, "A")
    set_value(has_bullet, "B", 0)
    
    branch_hit = place(ed.add_branch_node(), 1060, 0)
    connect(move, "then", branch_hit, "execute")
    connect(has_bullet, "ReturnValue", branch_hit, "Condition")
    
    first_bullet = fn(ed, "/Script/Engine.KismetArrayLibrary.Array_Get", 1260, 140)
    connect(get_overlap_bullet, "OverlappingActors", first_bullet, "TargetArray")
    set_value(first_bullet, "Index", 0)
    
    destroy_bullet = fn(ed, "/Script/Engine.Actor.K2_DestroyActor", 1460, 0)
    connect(branch_hit, "then", destroy_bullet, "execute")
    connect(first_bullet, "ReturnValue", destroy_bullet, "Target")
    
    cur_hp = place(ed.add_get_member_variable_node("CurrentHealth"), 1460, 140)
    sub_hp = fn(ed, "/Script/Engine.KismetMathLibrary.Subtract_DoubleDouble", 1680, 140)
    connect(cur_hp, "CurrentHealth", sub_hp, "A")
    set_value(sub_hp, "B", 25.0)
    
    set_hp = place(ed.add_set_member_variable_node("CurrentHealth"), 1880, 0)
    connect(destroy_bullet, "then", set_hp, "execute")
    connect(sub_hp, "ReturnValue", set_hp, "CurrentHealth")
    
    is_dead = fn(ed, "/Script/Engine.KismetMathLibrary.LessEqual_DoubleDouble", 1880, 140)
    connect(sub_hp, "ReturnValue", is_dead, "A")
    set_value(is_dead, "B", 0.0)
    
    branch_dead = place(ed.add_branch_node(), 2080, 0)
    connect(set_hp, "then", branch_dead, "execute")
    connect(is_dead, "ReturnValue", branch_dead, "Condition")
    
    destroy_boss = fn(ed, "/Script/Engine.Actor.K2_DestroyActor", 2300, 0)
    connect(branch_dead, "then", destroy_boss, "execute")
    
    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"✅ BP_Boss_Overlord 领主属性与击杀闭环配置完成！")
    return bp

# ==============================================================================
# 6. 配置 BP_StageWaveManager (40秒动态波次时钟与出怪调度)
# ==============================================================================
def build_stage_wave_manager(real_type):
    log(f"🚀 [6/6] 配置40秒动态波次时钟管理器: {WAVEMGR_PATH}...")
    bp = unreal.load_asset(WAVEMGR_PATH)
    if not bp:
        bp = BPLIB.create_blueprint_asset_with_parent(WAVEMGR_PATH, unreal.Actor.static_class())
        
    begin, tick = clean_graph_preserve_native_events(bp)
    bool_type = BPLIB.get_basic_type_by_name("bool")
    reset_variables(bp, [
        ("ElapsedTime", real_type, "0.0", "Clock"),
        ("SpawnTimer", real_type, "0.0", "Clock"),
        ("BossSpawned", bool_type, "false", "Wave State"),
        ("GameWon", bool_type, "false", "Wave State"),
    ])
    
    ed = event_editor(bp)
    if not tick: tick = ed.find_event_node("ReceiveTick")
    place(tick, 0, 0)
    
    # 1. ElapsedTime = ElapsedTime + DeltaSeconds
    get_elapsed = place(ed.add_get_member_variable_node("ElapsedTime"), 200, -80)
    add_elapsed = fn(ed, "/Script/Engine.KismetMathLibrary.Add_DoubleDouble", 420, -80)
    connect(get_elapsed, "ElapsedTime", add_elapsed, "A")
    connect(tick, "DeltaSeconds", add_elapsed, "B")
    
    set_elapsed = place(ed.add_set_member_variable_node("ElapsedTime"), 640, 0)
    connect(tick, "then", set_elapsed, "execute")
    connect(add_elapsed, "ReturnValue", set_elapsed, "ElapsedTime")
    
    # 2. SpawnTimer = SpawnTimer + DeltaSeconds
    get_sp_timer = place(ed.add_get_member_variable_node("SpawnTimer"), 640, 160)
    add_sp_timer = fn(ed, "/Script/Engine.KismetMathLibrary.Add_DoubleDouble", 860, 160)
    connect(get_sp_timer, "SpawnTimer", add_sp_timer, "A")
    connect(tick, "DeltaSeconds", add_sp_timer, "B")
    
    set_sp_timer = place(ed.add_set_member_variable_node("SpawnTimer"), 1080, 0)
    connect(set_elapsed, "then", set_sp_timer, "execute")
    connect(add_sp_timer, "ReturnValue", set_sp_timer, "SpawnTimer")
    
    # 3. 动态刷行尸 (当 ElapsedTime < 38.0 且 SpawnTimer >= 2.0)
    time_valid = fn(ed, "/Script/Engine.KismetMathLibrary.Less_DoubleDouble", 1080, 140)
    connect(add_elapsed, "ReturnValue", time_valid, "A")
    set_value(time_valid, "B", 38.0)
    
    timer_ready = fn(ed, "/Script/Engine.KismetMathLibrary.GreaterEqual_DoubleDouble", 1080, 220)
    connect(add_sp_timer, "ReturnValue", timer_ready, "A")
    set_value(timer_ready, "B", 2.0)
    
    can_spawn = fn(ed, "/Script/Engine.KismetMathLibrary.BooleanAND", 1280, 180)
    connect(time_valid, "ReturnValue", can_spawn, "A")
    connect(timer_ready, "ReturnValue", can_spawn, "B")
    
    branch_spawn = place(ed.add_branch_node(), 1480, 0)
    connect(set_sp_timer, "then", branch_spawn, "execute")
    connect(can_spawn, "ReturnValue", branch_spawn, "Condition")
    
    reset_st = place(ed.add_set_member_variable_node("SpawnTimer"), 1700, -60)
    set_value(reset_st, "SpawnTimer", 0.0)
    connect(branch_spawn, "then", reset_st, "execute")
    
    trans_zombie = fn(ed, "/Script/Engine.KismetMathLibrary.MakeTransform", 1700, 120)
    set_value(trans_zombie, "Location", "0,0,580")
    set_value(trans_zombie, "Scale", "1,1,1")
    
    spawn_zombie = fn(ed, "/Script/Engine.GameplayStatics.BeginDeferredActorSpawnFromClass", 1940, -60)
    set_value(spawn_zombie, "ActorClass", "Class'/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker.BP_Enemy_ZombieWalker_C'")
    connect(reset_st, "then", spawn_zombie, "execute")
    connect(trans_zombie, "ReturnValue", spawn_zombie, "SpawnTransform")
    
    finish_zombie = fn(ed, "/Script/Engine.GameplayStatics.FinishSpawningActor", 2200, -60)
    connect(spawn_zombie, "then", finish_zombie, "execute")
    connect(spawn_zombie, "ReturnValue", finish_zombie, "Actor")
    connect(trans_zombie, "ReturnValue", finish_zombie, "SpawnTransform")
    
    # 4. Boss 降临 (ElapsedTime >= 26.0 且 not BossSpawned)
    reach_boss_time = fn(ed, "/Script/Engine.KismetMathLibrary.GreaterEqual_DoubleDouble", 1080, 360)
    connect(add_elapsed, "ReturnValue", reach_boss_time, "A")
    set_value(reach_boss_time, "B", 26.0)
    
    get_boss_spawned = place(ed.add_get_member_variable_node("BossSpawned"), 1080, 440)
    not_boss_spawned = fn(ed, "/Script/Engine.KismetMathLibrary.Not_PreBool", 1280, 440)
    connect(get_boss_spawned, "BossSpawned", not_boss_spawned, "A")
    
    should_boss = fn(ed, "/Script/Engine.KismetMathLibrary.BooleanAND", 1480, 400)
    connect(reach_boss_time, "ReturnValue", should_boss, "A")
    connect(not_boss_spawned, "ReturnValue", should_boss, "B")
    
    branch_boss = place(ed.add_branch_node(), 1700, 320)
    connect(branch_spawn, "else", branch_boss, "execute")
    connect(finish_zombie, "then", branch_boss, "execute")
    connect(should_boss, "ReturnValue", branch_boss, "Condition")
    
    set_boss_spawned = place(ed.add_set_member_variable_node("BossSpawned"), 1920, 320)
    set_value(set_boss_spawned, "BossSpawned", "true")
    connect(branch_boss, "then", set_boss_spawned, "execute")
    
    trans_boss = fn(ed, "/Script/Engine.KismetMathLibrary.MakeTransform", 1920, 480)
    set_value(trans_boss, "Location", "0,0,580")
    set_value(trans_boss, "Scale", "1,1,1")
    
    spawn_boss = fn(ed, "/Script/Engine.GameplayStatics.BeginDeferredActorSpawnFromClass", 2160, 320)
    set_value(spawn_boss, "ActorClass", "Class'/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord.BP_Boss_Overlord_C'")
    connect(set_boss_spawned, "then", spawn_boss, "execute")
    connect(trans_boss, "ReturnValue", spawn_boss, "SpawnTransform")
    
    finish_boss = fn(ed, "/Script/Engine.GameplayStatics.FinishSpawningActor", 2420, 320)
    connect(spawn_boss, "then", finish_boss, "execute")
    connect(spawn_boss, "ReturnValue", finish_boss, "Actor")
    connect(trans_boss, "ReturnValue", finish_boss, "SpawnTransform")
    
    # 5. 40秒防线大捷通关重启
    reach_end_time = fn(ed, "/Script/Engine.KismetMathLibrary.GreaterEqual_DoubleDouble", 1080, 620)
    connect(add_elapsed, "ReturnValue", reach_end_time, "A")
    set_value(reach_end_time, "B", 40.0)
    
    get_won = place(ed.add_get_member_variable_node("GameWon"), 1080, 700)
    not_won = fn(ed, "/Script/Engine.KismetMathLibrary.Not_PreBool", 1280, 700)
    connect(get_won, "GameWon", not_won, "A")
    
    should_win = fn(ed, "/Script/Engine.KismetMathLibrary.BooleanAND", 1480, 660)
    connect(reach_end_time, "ReturnValue", should_win, "A")
    connect(not_won, "ReturnValue", should_win, "B")
    
    branch_win = place(ed.add_branch_node(), 1700, 600)
    connect(branch_boss, "else", branch_win, "execute")
    connect(finish_boss, "then", branch_win, "execute")
    connect(should_win, "ReturnValue", branch_win, "Condition")
    
    set_won = place(ed.add_set_member_variable_node("GameWon"), 1920, 600)
    set_value(set_won, "GameWon", "true")
    connect(branch_win, "then", set_won, "execute")
    
    delay_restart = fn(ed, "/Script/Engine.KismetSystemLibrary.Delay", 2160, 600)
    set_value(delay_restart, "Duration", 3.0)
    connect(set_won, "then", delay_restart, "execute")
    
    restart_map = fn(ed, "/Script/Engine.GameplayStatics.OpenLevel", 2420, 600)
    set_value(restart_map, "LevelName", "MAP_GGBOM_Main")
    connect(delay_restart, "then", restart_map, "execute")
    
    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"✅ BP_StageWaveManager 40秒波次时钟与重开机制配置完成！")
    return bp

# ==============================================================================
# 7. 部署关卡 MAP_GGBOM_Main
# ==============================================================================
def deploy_map_wave_manager():
    log(f"🚀 [7/7] 在关卡中部署波次时钟管理器: {MAP_PATH}...")
    world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
    if not world:
        raise RuntimeError(f"无法加载地图: {MAP_PATH}")
        
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    has_wave_mgr = False
    for a in actors:
        if a.get_class().get_name().startswith("BP_StageWaveManager"):
            has_wave_mgr = True
            break
            
    if not has_wave_mgr:
        mgr_cls = unreal.load_asset(WAVEMGR_PATH).generated_class()
        spawned = unreal.EditorLevelLibrary.spawn_actor_from_class(mgr_cls, unreal.Vector(0, 0, 700))
        if spawned:
            spawned.set_actor_label("BP_StageWaveManager_Live")
            log("  - 已将 BP_StageWaveManager_Live 放置在关卡顶部调度区")
            
    unreal.EditorLoadingAndSavingUtils.save_map(world, MAP_PATH)
    log("✅ MAP_GGBOM_Main 关卡装配保存完毕！")

# ==============================================================================
# 主入口
# ==============================================================================
def main():
    log("================================================================================")
    log("开始执行《GGBOM: 终末医疗兵》全量完整游戏流程系统装配 (闭环版)...")
    log("================================================================================")
    
    report = {
        "status": "FAIL",
        "exp_gem": False,
        "projectile": False,
        "zombie": False,
        "hound": False,
        "boss": False,
        "wave_manager": False,
        "map_deployed": False
    }
    
    try:
        real_type = BPLIB.get_basic_type_by_name("real")
        vector_type = BPLIB.get_struct_type(unreal.Vector.static_struct())
        
        build_exp_gem(real_type)
        report["exp_gem"] = True
        
        build_projectile(vector_type, real_type)
        report["projectile"] = True
        
        build_zombie_walker(real_type)
        report["zombie"] = True
        
        build_mutant_hound(real_type)
        report["hound"] = True
        
        build_boss_overlord(real_type)
        report["boss"] = True
        
        build_stage_wave_manager(real_type)
        report["wave_manager"] = True
        
        deploy_map_wave_manager()
        report["map_deployed"] = True
        
        report["status"] = "PASS"
        log("🎉 全量完整游戏流程系统装配全部成功！")
    except Exception as e:
        log(f"❌ 流程装配失败: {e}")
        report["error"] = str(e)
        import traceback
        traceback.print_exc()
        
    out_file = OUT_DIR / "full_game_flow_integration_report.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"Report written to {out_file}")

if __name__ == "__main__":
    main()
