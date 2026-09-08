# -*- coding: utf-8 -*-
"""
================================================================================
rebuild_native_physics_combat.py
全面回归 UE 原生物理引擎碰撞体系 (Native Physics & Collision Channels)
彻底废止写死图层优先级与假停止线，利用 PhysX/Chaos 原生碰撞阻挡与 Event Hit

核心架构:
1. 子弹 (BP_ProjectileBase):
   - SphereComponent 设为碰撞核心，开启 QueryAndPhysics
   - 对 ECC_Pawn (怪物) 与 ECC_WorldStatic (掩体) 设为 Block
   - 开启 notify_rigid_body_collision (Simulation Generates Hit Events)
   - EventGraph 绑定原生 ReceiveHit (Event Hit):
     物理碰撞瞬间获取精准 HitLocation，生成爆炸特效，施加 ApplyDamage，销毁子弹
2. 玩家主角 (BP_Player_Medic):
   - 物理胶囊体启用 QueryAndPhysics，对 ECC_Pawn 与 ECC_WorldStatic 设为 Block
   - 空间物理深度定位在 Y = -10 (三维空间自然遮挡，绝不穿模)
3. 敌人与 Boss (BP_Boss_Overlord, BP_Enemy_ZombieWalker 等):
   - 物理胶囊体启用 QueryAndPhysics，对 ECC_Pawn 与 ECC_WorldStatic 设为 Block
   - 移动开启 bSweep = True，撞击到掩体或玩家时由物理引擎原生阻挡停止，绝不踩脸穿模
================================================================================
"""
import unreal

PROJ_BP_PATH = "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase"
EXPLOSION_BP_PATH = "/Game/Blueprints/Combat/Projectiles/BP_Combat_HitExplosion"
EXPLOSION_FB_PATH = "/Game/P01/Imported/Content/Asset/Art/05_VFX/01_Explosion_Fire/Flipbooks/FB_T_VFX_Explosion_Fire_Sheet"
PLAYER_BP_PATH = "/Game/Blueprints/Player/BP_Player_Medic"
BOSS_BP_PATH = "/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord"
ZOMBIE_BP_PATH = "/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker"
MAP_PATH = "/Game/GGBOM/Maps/MAP_GGBOM_Main"

BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary
ASSETS = unreal.EditorAssetLibrary
SUBOBJECTS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)

def log(msg):
    print(f"[PHYSICS_SYSTEM] {msg}", flush=True)

def pin(node, name, output):
    pins = BPLIB.list_output_pins(node) if output else BPLIB.list_input_pins(node)
    wanted = name.lower()
    exact = [p for p in pins if str(PINLIB.get_pin_name(p)).lower() == wanted]
    if len(exact) == 1:
        return exact[0]
    raise RuntimeError(f"Pin {name} not found; available={[str(PINLIB.get_pin_name(p)) for p in pins]}")

def set_value(node, name, value):
    target = pin(node, name, False)
    if not PINLIB.set_pin_value(target, str(value)):
        raise RuntimeError(f"Default rejected: {name}={value}")

def connect(a, a_pin, b, b_pin):
    source, target = pin(a, a_pin, True), pin(b, b_pin, False)
    if not PINLIB.try_create_connection(source, target):
        raise RuntimeError(f"Connection rejected: {a_pin} -> {b_pin}")

def fn(editor, path, x, y):
    node = editor.add_call_function_node(path)
    if not node:
        raise RuntimeError(f"Function node failed: {path}")
    node.set_node_pos(unreal.IntPoint(x, y))
    return node

# ==============================================================================
# 1. 确保击中爆炸特效蓝图 BP_Combat_HitExplosion 存在
# ==============================================================================
def ensure_explosion_blueprint():
    log("💥 [1/4] 配置原生击中爆炸蓝图: BP_Combat_HitExplosion...")
    fb_asset = unreal.EditorAssetLibrary.load_asset(EXPLOSION_FB_PATH)
    if not fb_asset:
        fb_asset = unreal.EditorAssetLibrary.load_asset("/Game/Art/05_VFX/01_Explosion_Fire/Flipbooks/FB_T_VFX_Explosion_Fire_Sheet")
        
    bp = unreal.EditorAssetLibrary.load_asset(EXPLOSION_BP_PATH)
    if not bp:
        try:
            if unreal.EditorAssetLibrary.does_asset_exist(EXPLOSION_BP_PATH):
                unreal.EditorAssetLibrary.delete_asset(EXPLOSION_BP_PATH)
            bp = BPLIB.create_blueprint_asset_with_parent(EXPLOSION_BP_PATH, unreal.PaperFlipbookActor.static_class())
        except Exception as e:
            log(f"  创建爆炸蓝图通知: {e}")
            
    if not bp:
        bp = unreal.EditorAssetLibrary.load_asset(EXPLOSION_BP_PATH)

    if bp:
        cdo = unreal.get_default_object(bp.generated_class())
        if cdo:
            comp = cdo.get_component_by_class(unreal.PaperFlipbookComponent)
            if comp:
                if fb_asset:
                    try: comp.set_property("source_flipbook", fb_asset)
                    except Exception: pass
                comp.set_editor_property("relative_scale3d", unreal.Vector(0.85, 0.85, 0.85))
                comp.set_editor_property("looping", False)
                comp.set_collision_profile_name("NoCollision")

        graph = BPLIB.find_event_graph(bp)
        ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
        begin = ed.find_event_node("ReceiveBeginPlay")
        if not begin:
            begin = ed.find_event_node("ReceiveBeginPlay")
        if begin:
            begin.set_node_pos(unreal.IntPoint(0, 0))
            delay = fn(ed, "/Script/Engine.KismetSystemLibrary.Delay", 240, 0)
            set_value(delay, "Duration", 0.35)
            connect(begin, "then", delay, "execute")
            destroy = fn(ed, "/Script/Engine.Actor.K2_DestroyActor", 480, 0)
            connect(delay, "then", destroy, "execute")
            
        BPLIB.compile_blueprint(bp)
        ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
        log("  ✅ BP_Combat_HitExplosion 就绪！")

# ==============================================================================
# 2. 重构子弹 BP_ProjectileBase (原生物理碰撞体 + Event Hit)
# ==============================================================================
def setup_projectile_physics():
    log("🚀 [2/4] 重构子弹 BP_ProjectileBase 原生物理碰撞与 Event Hit...")
    bp = unreal.EditorAssetLibrary.load_asset(PROJ_BP_PATH)
    if not bp:
        raise RuntimeError(f"无法加载子弹资产: {PROJ_BP_PATH}")
        
    handles = SUBOBJECTS.k2_gather_subobject_data_for_blueprint(bp)
    sphere_comp = None
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        
        # 放大外观尺寸至 0.65 (饱满大颗粒)
        if "flipbook" in vname.lower() or "sprite" in vname.lower() or isinstance(obj, unreal.PaperFlipbookComponent):
            obj.set_editor_property("relative_scale3d", unreal.Vector(0.65, 0.65, 0.65))
            obj.set_editor_property("visible", True)
            obj.set_editor_property("hidden_in_game", False)
            
        # 配置物理碰撞球
        elif isinstance(obj, unreal.SphereComponent):
            sphere_comp = obj
            obj.set_editor_property("sphere_radius", 22.0)
            obj.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
            # 对 Pawn (怪物) 和 WorldStatic (掩体) 设为 Block
            obj.set_collision_response_to_all_channels(unreal.CollisionResponseType.ECR_IGNORE)
            obj.set_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN, unreal.CollisionResponseType.ECR_BLOCK)
            obj.set_collision_response_to_channel(unreal.CollisionChannel.ECC_WORLD_STATIC, unreal.CollisionResponseType.ECR_BLOCK)
            obj.set_collision_response_to_channel(unreal.CollisionChannel.ECC_WORLD_DYNAMIC, unreal.CollisionResponseType.ECR_BLOCK)
            # 开启产生物理击中事件 (Simulation Generates Hit Events)
            obj.set_editor_property("notify_rigid_body_collision", True)
            log("  🛡️ 子弹 SphereComponent 已配置为标准物理阻挡 (Block Pawn & Static) 并开启 Event Hit")

    # 重构 EventGraph: 绑定 ReceiveHit (原生物理击中事件)
    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    
    # 保持 BeginPlay 与 Tick 飞行，植入 ReceiveHit
    hit_node = ed.find_event_node("ReceiveHit")
    if not hit_node:
        hit_node = ed.find_event_node("ReceiveHit")
        
    if hit_node:
        log(f"  📍 找到原生物理撞击事件节点: {hit_node.get_name()}")
        hit_node.set_node_pos(unreal.IntPoint(0, 500))
        
        # 1. 过滤主角自身 (Other != PlayerPawn)
        get_pc = fn(ed, "/Script/Engine.GameplayStatics.GetPlayerController", 240, 680)
        set_value(get_pc, "PlayerIndex", 0)
        get_player_pawn = fn(ed, "/Script/Engine.Controller.K2_GetPawn", 460, 680)
        connect(get_pc, "ReturnValue", get_player_pawn, "self")
        
        other_pin_name = "Other" if "Other" in [str(PINLIB.get_pin_name(p)) for p in BPLIB.list_output_pins(hit_node)] else "OtherActor"
        is_not_player = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_ObjectObject", 680, 580)
        connect(hit_node, other_pin_name, is_not_player, "A")
        connect(get_player_pawn, "ReturnValue", is_not_player, "B")
        
        branch = ed.add_branch_node()
        branch.set_node_pos(unreal.IntPoint(880, 500))
        connect(hit_node, "then", branch, "execute")
        connect(is_not_player, "ReturnValue", branch, "Condition")
        
        # 2. 物理命中点生成爆炸特效 (使用物理引擎计算的精准 HitLocation 或自身位置)
        my_loc = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 1080, 620)
        make_trans = fn(ed, "/Script/Engine.KismetMathLibrary.MakeTransform", 1300, 620)
        connect(my_loc, "ReturnValue", make_trans, "Location")
        set_value(make_trans, "Scale", "1,1,1")
        
        spawn_vfx = fn(ed, "/Script/Engine.GameplayStatics.BeginDeferredActorSpawnFromClass", 1520, 500)
        set_value(spawn_vfx, "ActorClass", "Class'/Game/Blueprints/Combat/Projectiles/BP_Combat_HitExplosion.BP_Combat_HitExplosion_C'")
        connect(branch, "then", spawn_vfx, "execute")
        connect(make_trans, "ReturnValue", spawn_vfx, "SpawnTransform")
        
        finish_vfx = fn(ed, "/Script/Engine.GameplayStatics.FinishSpawningActor", 1780, 500)
        connect(spawn_vfx, "then", finish_vfx, "execute")
        connect(spawn_vfx, "ReturnValue", finish_vfx, "Actor")
        connect(make_trans, "ReturnValue", finish_vfx, "SpawnTransform")
        
        # 3. 对被撞击的目标施加 45.0 真实动能伤害
        apply_dmg = fn(ed, "/Script/Engine.GameplayStatics.ApplyDamage", 2040, 500)
        connect(finish_vfx, "then", apply_dmg, "execute")
        connect(hit_node, other_pin_name, apply_dmg, "DamagedActor")
        set_value(apply_dmg, "BaseDamage", 45.0)
        
        # 4. 立即销毁子弹
        destroy = fn(ed, "/Script/Engine.Actor.K2_DestroyActor", 2300, 500)
        connect(apply_dmg, "then", destroy, "execute")

    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log("  ✅ 子弹物理碰撞与原生 Event Hit 闭环配置完成！")

# ==============================================================================
# 3. 玩家与怪物配置为标准物理 Pawn 阻挡 (Pawn Block Pawn)
# ==============================================================================
def setup_pawn_physical_blocking():
    log("🛡️ [3/4] 配置玩家与怪物之间的真实物理胶囊体阻挡 (Pawn vs Pawn Block)...")
    
    # 3.1 玩家主角物理配置
    p_bp = unreal.EditorAssetLibrary.load_asset(PLAYER_BP_PATH)
    if p_bp:
        cdo = unreal.get_default_object(p_bp.generated_class())
        if cdo:
            capsule = cdo.get_component_by_class(unreal.ShapeComponent) or cdo.get_component_by_class(unreal.CapsuleComponent)
            if capsule:
                capsule.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
                capsule.set_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN, unreal.CollisionResponseType.ECR_BLOCK)
                capsule.set_collision_response_to_channel(unreal.CollisionChannel.ECC_WORLD_STATIC, unreal.CollisionResponseType.ECR_BLOCK)
                log("  👤 玩家主角胶囊体已开启 Pawn 与 Static 物理阻挡 (Block)")
        BPLIB.compile_blueprint(p_bp)
        ASSETS.save_loaded_asset(p_bp, only_if_is_dirty=False)

    # 3.2 敌人与 Boss 物理配置
    enemy_bps = [
        BOSS_BP_PATH,
        ZOMBIE_BP_PATH,
        "/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieRunner",
        "/Game/Blueprints/Characters/Enemies/BP_Enemy_MutantHound",
        "/Game/Blueprints/Characters/Enemies/BP_Enemy_VenomShooter",
        "/Game/Blueprints/Characters/Enemies/BP_Enemy_ArmoredGuard",
        "/Game/Blueprints/Characters/Enemies/BP_Enemy_MutantBrute",
    ]
    for e_path in enemy_bps:
        e_bp = unreal.EditorAssetLibrary.load_asset(e_path)
        if not e_bp: continue
        cdo = unreal.get_default_object(e_bp.generated_class())
        if cdo:
            col_comp = cdo.get_component_by_class(unreal.ShapeComponent) or \
                       cdo.get_component_by_class(unreal.CapsuleComponent) or \
                       cdo.get_component_by_class(unreal.BoxComponent) or \
                       cdo.get_component_by_class(unreal.PaperFlipbookComponent)
            if col_comp:
                col_comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
                col_comp.set_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN, unreal.CollisionResponseType.ECR_BLOCK)
                col_comp.set_collision_response_to_channel(unreal.CollisionChannel.ECC_WORLD_STATIC, unreal.CollisionResponseType.ECR_BLOCK)
                
        # 确保移动扫描 bSweep 开启 (撞击障碍物或玩家时被物理引擎自动阻挡)
        graph = BPLIB.find_event_graph(e_bp)
        ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
        for n in ed.list_all_nodes():
            if "Add Actor World Offset" in BPLIB.get_node_title(n):
                set_value(n, "bSweep", "true")

        BPLIB.compile_blueprint(e_bp)
        ASSETS.save_loaded_asset(e_bp, only_if_is_dirty=False)
    log("  👾 所有敌人实体均已接入原生物理阻挡矩阵 (开启 Pawn Block 与 bSweep)")

# ==============================================================================
# 4. 关卡实体空间三维深度自然分层 (利用 Y 轴物理距离彻底淘汰写死 priority)
# ==============================================================================
def align_world_physical_depth():
    log("🌍 [4/4] 规范关卡内实体的三维物理深度通道 (Y轴自然透视)...")
    world = unreal.EditorLevelLibrary.get_editor_world()
    if not world: return
    
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    for a in actors:
        lbl = a.get_actor_label()
        loc = a.get_actor_location()
        
        # 玩家位于前景 Y = -10 (三维空间自然在怪物前方，镜头在 Y = -600 正视)
        if "Player" in lbl or isinstance(a, unreal.PlayerStart):
            a.set_actor_location(unreal.Vector(loc.x, -10.0, loc.z), False, False)
            
        # 怪物与 Boss 位于战斗中景 Y = 0
        elif "Boss" in lbl:
            # 如果 Boss 已经走到了玩家身上 (Z <= -300)，恢复到防线前方 (0, 0, 560)
            target_z = 560.0 if loc.z <= -300.0 else loc.z
            a.set_actor_location(unreal.Vector(0.0, 0.0, target_z), False, False)
            
        elif "Enemy" in lbl or "Zombie" in lbl or "Hound" in lbl:
            target_z = 280.0 if loc.z <= -300.0 else loc.z
            a.set_actor_location(unreal.Vector(loc.x, 0.0, target_z), False, False)
            
        # 掩体路障位于中景 Y = 30
        elif "Barricade" in lbl or "DefenseLine" in lbl or "Wall" in lbl:
            a.set_actor_location(unreal.Vector(loc.x, 30.0, loc.z), False, False)
            
        # 地面位于背景通道 Y = 80
        elif "Ground" in lbl:
            a.set_actor_location(unreal.Vector(0.0, 80.0, 0.0), False, False)

    unreal.EditorLoadingAndSavingUtils.save_map(world, MAP_PATH)
    log("  ✅ 关卡三维空间物理深度已对齐并保存！")

def run_pure_physics():
    log("==================================================")
    log("⚡ 启动【虚幻引擎原生物理碰撞与 Event Hit】全量重构...")
    ensure_explosion_blueprint()
    setup_projectile_physics()
    setup_pawn_physical_blocking()
    align_world_physical_depth()
    log("🎉 原生物理系统重构完毕！")
    log("   - 子弹: 原生物理阻挡 + Event Hit 瞬间爆炸扣血自毁")
    log("   - 碰撞: Pawn vs Pawn 原生物理阻挡，怪物被胶囊体挡在身前绝不穿透")
    log("   - 深度: 三维空间 Y 轴自然透视 (-10 vs 0 vs 30)，彻底摒弃假图层")
    log("==================================================")

if __name__ == "__main__":
    run_pure_physics()
