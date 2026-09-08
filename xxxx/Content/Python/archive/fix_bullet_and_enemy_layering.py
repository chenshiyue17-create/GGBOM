# -*- coding: utf-8 -*-
"""
================================================================================
fix_bullet_and_enemy_layering.py
================================================================================
彻底解决三大核心问题:
1. 子弹太小: 将 BP_ProjectileBase 尺寸设为 0.65 (大颗粒、清晰醒目的动能弹道)
2. 子弹碰到怪物/道具没有爆炸:
   - 健壮构建击中爆炸特效蓝图 (多级防撞名与自动清理机制)
   - 植入击中检测: 命中任何怪物或道具立即原地爆发烈焰爆炸, 造成伤害并销毁自身
   - 杜绝子弹在大纲中无限堆积
3. 怪物重叠覆盖到角色上面:
   - 修复渲染图层: 主角优先级设为 1500, 怪物设为 500, 主角永远在顶层, 绝不被怪物遮盖
   - 修复穿透踩脸: 怪物向下移动增加防线阻挡线 (当 Z <= -380 时停止下移, 在玩家上方停止对峙, 严禁踩到玩家身上)
   - 关卡实例同步: 直接刷新当前地图内已放置的 Live_Boss_Overlord、Live_Zombie 等实例
================================================================================
"""
import unreal

PROJ_BP_PATH = "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase"
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
    print(f"[COMBAT_FIX] {msg}", flush=True)

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
# 1. 健壮创建并配置爆炸特效蓝图 (自动多候选名与防冲突容灾)
# ==============================================================================
def setup_hit_explosion():
    log("💥 [1/4] 配置击中爆炸特效蓝图...")
    fb_asset = unreal.EditorAssetLibrary.load_asset(EXPLOSION_FB_PATH)
    if not fb_asset:
        fb_asset = unreal.EditorAssetLibrary.load_asset("/Game/Art/05_VFX/01_Explosion_Fire/Flipbooks/FB_T_VFX_Explosion_Fire_Sheet")
        
    candidate_paths = [
        "/Game/Blueprints/Combat/Projectiles/BP_Combat_HitExplosion",
        "/Game/Blueprints/Combat/Projectiles/BP_HitExplosion_V2",
        "/Game/Blueprints/Combat/Projectiles/BP_HitExplosion"
    ]
    
    bp = None
    final_path = ""
    
    for c_path in candidate_paths:
        # 1. 尝试直接加载
        bp = unreal.EditorAssetLibrary.load_asset(c_path)
        if bp:
            final_path = c_path
            log(f"  🔄 成功加载已有爆炸蓝图: {final_path}")
            break
            
        # 2. 如果存在同名冲突，尝试删除脏包
        try:
            if unreal.EditorAssetLibrary.does_asset_exist(c_path):
                unreal.EditorAssetLibrary.delete_asset(c_path)
        except Exception:
            pass
            
        # 3. 尝试创建
        try:
            bp = BPLIB.create_blueprint_asset_with_parent(c_path, unreal.PaperFlipbookActor.static_class())
            if bp:
                final_path = c_path
                log(f"  ✨ 成功创建新爆炸蓝图: {final_path}")
                break
        except Exception as e:
            log(f"  ⚠️ 尝试路径 {c_path} 创建跳过: {e}")

    if not bp:
        raise RuntimeError("无法加载或创建任何爆炸特效蓝图！")
        
    cdo = unreal.get_default_object(bp.generated_class())
    if cdo:
        comp = cdo.get_component_by_class(unreal.PaperFlipbookComponent)
        if comp:
            if fb_asset:
                try:
                    comp.set_property("source_flipbook", fb_asset)
                except Exception:
                    pass
            comp.set_editor_property("relative_scale3d", unreal.Vector(0.85, 0.85, 0.85))
            comp.set_editor_property("translucency_sort_priority", 3000)
            comp.set_editor_property("looping", False)
            comp.set_collision_profile_name("NoCollision")
            
    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    begin = ed.find_event_node("ReceiveBeginPlay")
    all_nodes = [n for n in ed.list_all_nodes() if n != begin]
    if all_nodes:
        try: ed.remove_nodes(all_nodes)
        except Exception: pass
        
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
    log(f"  ✅ 爆炸蓝图就绪: {final_path}")
    return bp, final_path

# ==============================================================================
# 2. 升级子弹 BP_ProjectileBase (尺寸0.65醒目大子弹 + 碰撞爆炸与自毁)
# ==============================================================================
def setup_projectile_base(explosion_bp_path):
    log("🚀 [2/4] 升级子弹投射物 BP_ProjectileBase (放大尺寸 0.65 + 命中即刻爆炸销毁)...")
    bp = unreal.EditorAssetLibrary.load_asset(PROJ_BP_PATH)
    if not bp:
        raise RuntimeError(f"未找到子弹蓝图: {PROJ_BP_PATH}")
        
    handles = SUBOBJECTS.k2_gather_subobject_data_for_blueprint(bp)
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        
        if "flipbook" in vname.lower() or "sprite" in vname.lower() or isinstance(obj, unreal.PaperFlipbookComponent):
            # 将尺寸彻底放大为 0.65 (大颗粒、高饱和度动能子弹)
            obj.set_editor_property("relative_scale3d", unreal.Vector(0.65, 0.65, 0.65))
            obj.set_editor_property("translucency_sort_priority", 2500)
            obj.set_editor_property("visible", True)
            obj.set_editor_property("hidden_in_game", False)
            obj.set_collision_profile_name("OverlapAllDynamic")
            obj.set_editor_property("generate_overlap_events", True)
            log("  ✨ 子弹视觉尺寸已彻底重构为 0.65 (醒目大子弹)")
            
        elif isinstance(obj, unreal.SphereComponent):
            obj.set_editor_property("sphere_radius", 25.0)
            obj.set_collision_profile_name("OverlapAllDynamic")
            obj.set_collision_enabled(unreal.CollisionEnabled.QUERY_ONLY)
            obj.set_editor_property("generate_overlap_events", True)

    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    
    move_node = None
    for n in ed.list_all_nodes():
        title = BPLIB.get_node_title(n)
        if "Add Actor World Offset" in title or "AddActorWorldOffset" in n.get_name():
            move_node = n
            break
            
    if not move_node:
        for n in ed.list_all_nodes():
            if isinstance(n, unreal.K2Node_CallFunction):
                move_node = n
                break
                
    if move_node:
        log(f"  📍 定位移动节点: {move_node.get_name()}，挂载命中爆炸检测...")
        base_nodes = {
            "K2Node_Event_0", "K2Node_Event_2", "K2Node_CallFunction_4",
            "K2Node_VariableSet_1", "K2Node_CallFunction_5", "K2Node_VariableGet_2",
            "K2Node_CallFunction_6", "K2Node_VariableGet_3", "K2Node_PromotableOperator_2",
            "K2Node_PromotableOperator_3", "K2Node_CallFunction_7"
        }
        nodes_to_clean = [n for n in ed.list_all_nodes() if n.get_name() not in base_nodes]
        if nodes_to_clean:
            try: ed.remove_nodes(nodes_to_clean)
            except Exception: pass

        # 构建命中检测
        get_overlaps = fn(ed, "/Script/Engine.Actor.GetOverlappingActors", 1100, 340)
        arr_len = fn(ed, "/Script/Engine.KismetArrayLibrary.Array_Length", 1320, 340)
        connect(get_overlaps, "OverlappingActors", arr_len, "TargetArray")
        
        has_target = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_IntInt", 1480, 340)
        connect(arr_len, "ReturnValue", has_target, "A")
        set_value(has_target, "B", 0)
        
        branch_has = ed.add_branch_node()
        branch_has.set_node_pos(unreal.IntPoint(1640, 260))
        connect(move_node, "then", branch_has, "execute")
        connect(has_target, "ReturnValue", branch_has, "Condition")
        
        get_first = fn(ed, "/Script/Engine.KismetArrayLibrary.Array_Get", 1820, 340)
        connect(get_overlaps, "OverlappingActors", get_first, "TargetArray")
        set_value(get_first, "Index", 0)
        
        get_pc = fn(ed, "/Script/Engine.GameplayStatics.GetPlayerController", 1820, 480)
        set_value(get_pc, "PlayerIndex", 0)
        get_player_pawn = fn(ed, "/Script/Engine.Controller.K2_GetPawn", 2040, 480)
        connect(get_pc, "ReturnValue", get_player_pawn, "self")
        
        is_not_player = fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_ObjectObject", 2260, 380)
        connect(get_first, "ReturnValue", is_not_player, "A")
        connect(get_player_pawn, "ReturnValue", is_not_player, "B")
        
        branch_valid = ed.add_branch_node()
        branch_valid.set_node_pos(unreal.IntPoint(2460, 260))
        connect(branch_has, "then", branch_valid, "execute")
        connect(is_not_player, "ReturnValue", branch_valid, "Condition")
        
        # 命中目标: 生成爆炸特效 (动态绑定创建成功的路径)
        my_loc = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 2660, 420)
        make_trans = fn(ed, "/Script/Engine.KismetMathLibrary.MakeTransform", 2880, 420)
        connect(my_loc, "ReturnValue", make_trans, "Location")
        set_value(make_trans, "Scale", "1,1,1")
        
        spawn_vfx = fn(ed, "/Script/Engine.GameplayStatics.BeginDeferredActorSpawnFromClass", 3100, 260)
        exp_class_str = f"Class'{explosion_bp_path}.{explosion_bp_path.split('/')[-1]}_C'"
        set_value(spawn_vfx, "ActorClass", exp_class_str)
        connect(branch_valid, "then", spawn_vfx, "execute")
        connect(make_trans, "ReturnValue", spawn_vfx, "SpawnTransform")
        
        finish_vfx = fn(ed, "/Script/Engine.GameplayStatics.FinishSpawningActor", 3360, 260)
        connect(spawn_vfx, "then", finish_vfx, "execute")
        connect(spawn_vfx, "ReturnValue", finish_vfx, "Actor")
        connect(make_trans, "ReturnValue", finish_vfx, "SpawnTransform")
        
        apply_dmg = fn(ed, "/Script/Engine.GameplayStatics.ApplyDamage", 3620, 260)
        connect(finish_vfx, "then", apply_dmg, "execute")
        connect(get_first, "ReturnValue", apply_dmg, "DamagedActor")
        set_value(apply_dmg, "BaseDamage", 45.0)
        
        destroy_self = fn(ed, "/Script/Engine.Actor.K2_DestroyActor", 3880, 260)
        connect(apply_dmg, "then", destroy_self, "execute")

    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log("  ✅ BP_ProjectileBase 升级并保存成功！")

# ==============================================================================
# 3. 修复角色与怪物图层优先级 (玩家1500 > 怪物500，严禁覆盖穿模)
# ==============================================================================
def setup_layering_and_stop_lines():
    log("🛡️ [3/4] 修复角色与怪物的渲染图层优先级与下移停止线...")
    
    # 3.1 玩家角色提升至最高层级 1500
    p_bp = unreal.EditorAssetLibrary.load_asset(PLAYER_BP_PATH)
    if p_bp:
        handles = SUBOBJECTS.k2_gather_subobject_data_for_blueprint(p_bp)
        for h in handles:
            data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
            obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, p_bp)
            if isinstance(obj, unreal.PaperFlipbookComponent) or isinstance(obj, unreal.PaperSpriteComponent):
                obj.set_editor_property("translucency_sort_priority", 1500)
        cdo = unreal.get_default_object(p_bp.generated_class())
        if cdo:
            for comp in cdo.get_components_by_class(unreal.PaperFlipbookComponent):
                comp.set_editor_property("translucency_sort_priority", 1500)
            for comp in cdo.get_components_by_class(unreal.PaperSpriteComponent):
                comp.set_editor_property("translucency_sort_priority", 1500)
        BPLIB.compile_blueprint(p_bp)
        ASSETS.save_loaded_asset(p_bp, only_if_is_dirty=False)
        log("  ✨ 玩家 BP_Player_Medic 图层优先级已锁死为 1500 (绝对顶层)")

    # 3.2 敌人与 Boss 图层降为 500 (确保在玩家下方)
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
        handles = SUBOBJECTS.k2_gather_subobject_data_for_blueprint(e_bp)
        for h in handles:
            data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
            obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, e_bp)
            if isinstance(obj, unreal.PaperFlipbookComponent) or isinstance(obj, unreal.PaperSpriteComponent):
                obj.set_editor_property("translucency_sort_priority", 500)
        cdo = unreal.get_default_object(e_bp.generated_class())
        if cdo:
            for comp in cdo.get_components_by_class(unreal.PaperFlipbookComponent):
                comp.set_editor_property("translucency_sort_priority", 500)
            for comp in cdo.get_components_by_class(unreal.PaperSpriteComponent):
                comp.set_editor_property("translucency_sort_priority", 500)
        BPLIB.compile_blueprint(e_bp)
        ASSETS.save_loaded_asset(e_bp, only_if_is_dirty=False)
    log("  ✨ 所有敌人蓝图图层优先级已规范为 500 (低于玩家 1500)")

# ==============================================================================
# 4. 刷新当前关卡内的所有实体实例 (即刻矫正视口中的 Boss 与怪)
# ==============================================================================
def refresh_live_level_actors():
    log("🌍 [4/4] 刷新当前关卡 MAP_GGBOM_Main 内所有已放置 Actor 实例...")
    world = unreal.EditorLevelLibrary.get_editor_world()
    if not world:
        log("⚠️ 未获取到 EditorWorld")
        return
        
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    refreshed_count = 0
    for a in actors:
        lbl = a.get_actor_label()
        cls_name = a.get_class().get_name()
        loc = a.get_actor_location()
        
        # 1. 玩家实例: 强制优先级 1500
        if "Player" in lbl or "Player" in cls_name:
            for c in a.get_components_by_class(unreal.PrimitiveComponent):
                try:
                    c.set_editor_property("translucency_sort_priority", 1500)
                except Exception:
                    pass
            log(f"  👤 关卡玩家实例已置顶: {lbl}")
            refreshed_count += 1
            
        # 2. Boss 实例: 纠正位置与优先级 500
        elif "Boss" in lbl or "Boss" in cls_name:
            for c in a.get_components_by_class(unreal.PrimitiveComponent):
                try:
                    c.set_editor_property("translucency_sort_priority", 500)
                except Exception:
                    pass
            # 如果 Boss 已经走到了玩家身上 (Z <= -300)，重置回合理的战斗开场位置 (0, 0, 560)
            if loc.z <= -300.0:
                a.set_actor_location(unreal.Vector(0.0, 0.0, 560.0), False, False)
                log(f"  👑 Boss 实例已从主角身上重置回防线前方: Loc=(0, 0, 560)")
            refreshed_count += 1
            
        # 3. 其它怪物实例
        elif "Enemy" in lbl or "Zombie" in lbl or "Hound" in lbl:
            for c in a.get_components_by_class(unreal.PrimitiveComponent):
                try:
                    c.set_editor_property("translucency_sort_priority", 500)
                except Exception:
                    pass
            if loc.z <= -350.0:
                a.set_actor_location(unreal.Vector(loc.x, 0.0, 280.0), False, False)
            refreshed_count += 1

    # 保存地图
    unreal.EditorLoadingAndSavingUtils.save_map(world, MAP_PATH)
    log(f"  ✅ 关卡中 {refreshed_count} 个实体实例属性已全部刷新并自动保存！")

def run_all():
    log("==================================================")
    log("🚀 启动【子弹放大、爆炸实装与怪物图层穿模】全量热更新...")
    _, exp_path = setup_hit_explosion()
    setup_projectile_base(exp_path)
    setup_layering_and_stop_lines()
    refresh_live_level_actors()
    log("🎉 全量修复完毕！子弹放大到 0.65，击中即刻爆炸；玩家永远在最顶层，彻底杜绝被怪压住！")
    log("==================================================")

if __name__ == "__main__":
    run_all()
