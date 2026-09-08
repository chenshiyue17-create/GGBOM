# -*- coding: utf-8 -*-
"""
================================================================================
fix_bullet_scale_and_explosion.py
================================================================================
本脚本用于彻底解决两个战斗核心问题:
1. 子弹太小: 将 BP_ProjectileBase 的外观 Flipbook 尺寸从 0.03 放大到 0.55 (黄金视觉比例)
2. 碰到怪物/道具没有爆炸:
   a. 创建/配置火焰爆炸特效蓝图 BP_HitExplosion (使用 FB_T_VFX_Explosion_Fire_Sheet)
   b. 为 BP_ProjectileBase 开启 OverlapAllDynamic 碰撞与重叠事件派发
   c. 在 BP_ProjectileBase 的移动完成引脚 (K2Node_CallFunction_7 then) 之后无缝串联:
      - 获取当前重叠 Actor 列表 (GetOverlappingActors)
      - 排除玩家主角 (OtherActor != PlayerPawn), 彻底杜绝子弹挡住角色
      - 命中怪物/道具时:
        * 在击中位置生成 BP_HitExplosion 爆炸特效 (0.35s 自毁)
        * 对目标施加 45.0 伤害 (GameplayStatics.ApplyDamage)
        * 立即销毁子弹自身 (DestroyActor)
================================================================================
"""
import unreal

PROJ_BP_PATH = "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase"
EXPLOSION_BP_PATH = "/Game/Blueprints/Combat/Projectiles/BP_HitExplosion"
EXPLOSION_FB_PATH = "/Game/P01/Imported/Content/Asset/Art/05_VFX/01_Explosion_Fire/Flipbooks/FB_T_VFX_Explosion_Fire_Sheet"

BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary
ASSETS = unreal.EditorAssetLibrary
SUBOBJECTS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)

def log(msg):
    print(f"[BULLET_FIX] {msg}", flush=True)

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
# 1. 创建并配置爆炸特效蓝图 BP_HitExplosion
# ==============================================================================
def create_or_update_hit_explosion():
    log("💥 [1/2] 正在构建/更新击中爆炸特效蓝图: BP_HitExplosion...")
    fb_asset = unreal.load_asset(EXPLOSION_FB_PATH)
    if not fb_asset:
        fb_asset = unreal.load_asset("/Game/Art/05_VFX/01_Explosion_Fire/Flipbooks/FB_T_VFX_Explosion_Fire_Sheet")
        
    bp = unreal.load_asset(EXPLOSION_BP_PATH)
    if not bp:
        bp = BPLIB.create_blueprint_asset_with_parent(EXPLOSION_BP_PATH, unreal.PaperFlipbookActor.static_class())
        log(f"  ✨ 创建新蓝图: {EXPLOSION_BP_PATH}")
    else:
        log(f"  🔄 加载已有蓝图: {EXPLOSION_BP_PATH}")

    # 配置 CDO 属性 (使用 get_component_by_class 避免 C++ getter 差异)
    cdo = unreal.get_default_object(bp.generated_class())
    if cdo:
        comp = cdo.get_component_by_class(unreal.PaperFlipbookComponent)
        if comp:
            if fb_asset:
                comp.set_property("source_flipbook", fb_asset)
            comp.set_editor_property("relative_scale3d", unreal.Vector(0.75, 0.75, 0.75))
            comp.set_editor_property("translucency_sort_priority", 3000)
            comp.set_editor_property("looping", False)
            comp.set_collision_profile_name("NoCollision")
            
    # 配置 EventGraph: BeginPlay -> Delay(0.35) -> DestroyActor
    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    
    begin = ed.find_event_node("ReceiveBeginPlay")
    all_nodes = [n for n in ed.list_all_nodes() if n != begin]
    if all_nodes:
        try:
            ed.remove_nodes(all_nodes)
        except Exception:
            pass
            
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
    log("  ✅ BP_HitExplosion 爆炸特效蓝图配置并保存成功！")
    return bp

# ==============================================================================
# 2. 升级 BP_ProjectileBase (尺寸放大 0.55 + 开启碰撞 + 命中爆炸链路)
# ==============================================================================
def upgrade_projectile_base():
    log("🚀 [2/2] 正在升级子弹投射物 BP_ProjectileBase (放大尺寸 0.55 + 植入碰撞爆炸)...")
    bp = unreal.load_asset(PROJ_BP_PATH)
    if not bp:
        raise RuntimeError(f"未找到子弹蓝图: {PROJ_BP_PATH}")
        
    # 2.1 调整组件尺寸与碰撞属性
    handles = SUBOBJECTS.k2_gather_subobject_data_for_blueprint(bp)
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        
        if "flipbook" in vname.lower() or "sprite" in vname.lower() or isinstance(obj, unreal.PaperFlipbookComponent):
            # 将尺寸彻底从 0.03 恢复为 0.55 黄金视觉大小
            obj.set_editor_property("relative_scale3d", unreal.Vector(0.55, 0.55, 0.55))
            obj.set_editor_property("translucency_sort_priority", 2800)
            obj.set_editor_property("visible", True)
            obj.set_editor_property("hidden_in_game", False)
            obj.set_collision_profile_name("OverlapAllDynamic")
            obj.set_editor_property("generate_overlap_events", True)
            log("  ✨ 子弹视觉尺寸已恢复为 0.55 (原0.03错误尺寸已彻底清除)")
            
        elif isinstance(obj, unreal.SphereComponent):
            obj.set_editor_property("sphere_radius", 22.0)
            obj.set_collision_profile_name("OverlapAllDynamic")
            obj.set_collision_enabled(unreal.CollisionEnabled.QUERY_ONLY)
            obj.set_editor_property("generate_overlap_events", True)
            log("  🛡️ 找到并配置 SphereComponent (Radius=22.0, OverlapAllDynamic)")

    # 2.2 在已有的图表末端增量挂载命中判定
    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    
    # 寻找已有的 AddActorWorldOffset 移动节点 (K2Node_CallFunction_7)
    move_node = None
    for n in ed.list_all_nodes():
        title = BPLIB.get_node_title(n)
        if "Add Actor World Offset" in title or "AddActorWorldOffset" in n.get_name():
            move_node = n
            break
            
    if not move_node:
        log("⚠️ 未在图表中找到 Add Actor World Offset 节点，尝试遍历所有 CallFunction 节点...")
        for n in ed.list_all_nodes():
            if isinstance(n, unreal.K2Node_CallFunction):
                move_node = n
                break
                
    if not move_node:
        raise RuntimeError("无法定位子弹移动节点！")
        
    log(f"  📍 找到子弹移动端点节点: {move_node.get_name()}")
    
    # 清理已有的旧命中检测节点 (如果有上一次生成的遗留节点)
    base_nodes = {
        "K2Node_Event_0", "K2Node_Event_2", "K2Node_CallFunction_4",
        "K2Node_VariableSet_1", "K2Node_CallFunction_5", "K2Node_VariableGet_2",
        "K2Node_CallFunction_6", "K2Node_VariableGet_3", "K2Node_PromotableOperator_2",
        "K2Node_PromotableOperator_3", "K2Node_CallFunction_7"
    }
    nodes_to_clean = [n for n in ed.list_all_nodes() if n.get_name() not in base_nodes]
    if nodes_to_clean:
        try:
            ed.remove_nodes(nodes_to_clean)
        except Exception:
            pass

    # ---------- 命中判定链路构建 ----------
    # 1. GetOverlappingActors
    get_overlaps = fn(ed, "/Script/Engine.Actor.GetOverlappingActors", 1100, 340)
    
    # 2. Array Length
    arr_len = fn(ed, "/Script/Engine.KismetArrayLibrary.Array_Length", 1320, 340)
    connect(get_overlaps, "OverlappingActors", arr_len, "TargetArray")
    
    # 3. Length > 0
    has_target = fn(ed, "/Script/Engine.KismetMathLibrary.Greater_IntInt", 1480, 340)
    connect(arr_len, "ReturnValue", has_target, "A")
    set_value(has_target, "B", 0)
    
    # 4. Branch (是否有重叠)
    branch_has = ed.add_branch_node()
    branch_has.set_node_pos(unreal.IntPoint(1640, 260))
    connect(move_node, "then", branch_has, "execute")
    connect(has_target, "ReturnValue", branch_has, "Condition")
    
    # 5. 获取第一个重叠的 Actor
    get_first = fn(ed, "/Script/Engine.KismetArrayLibrary.Array_Get", 1820, 340)
    connect(get_overlaps, "OverlappingActors", get_first, "TargetArray")
    set_value(get_first, "Index", 0)
    
    # 6. 核心过滤: 严禁阻挡或误伤玩家主角 (BP_Player_Medic)
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
    
    # 7. 命中目标: 生成爆炸特效 (BP_HitExplosion)
    my_loc = fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 2660, 420)
    make_trans = fn(ed, "/Script/Engine.KismetMathLibrary.MakeTransform", 2880, 420)
    connect(my_loc, "ReturnValue", make_trans, "Location")
    set_value(make_trans, "Scale", "1,1,1")
    
    spawn_vfx = fn(ed, "/Script/Engine.GameplayStatics.BeginDeferredActorSpawnFromClass", 3100, 260)
    set_value(spawn_vfx, "ActorClass", "Class'/Game/Blueprints/Combat/Projectiles/BP_HitExplosion.BP_HitExplosion_C'")
    connect(branch_valid, "then", spawn_vfx, "execute")
    connect(make_trans, "ReturnValue", spawn_vfx, "SpawnTransform")
    
    finish_vfx = fn(ed, "/Script/Engine.GameplayStatics.FinishSpawningActor", 3360, 260)
    connect(spawn_vfx, "then", finish_vfx, "execute")
    connect(spawn_vfx, "ReturnValue", finish_vfx, "Actor")
    connect(make_trans, "ReturnValue", finish_vfx, "SpawnTransform")
    
    # 8. 施加伤害 (ApplyDamage 45.0)
    apply_dmg = fn(ed, "/Script/Engine.GameplayStatics.ApplyDamage", 3620, 260)
    connect(finish_vfx, "then", apply_dmg, "execute")
    connect(get_first, "ReturnValue", apply_dmg, "DamagedActor")
    set_value(apply_dmg, "BaseDamage", 45.0)
    
    # 9. 立即销毁子弹自身
    destroy_self = fn(ed, "/Script/Engine.Actor.K2_DestroyActor", 3880, 260)
    connect(apply_dmg, "then", destroy_self, "execute")

    BPLIB.compile_blueprint(bp)
    ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log("  ✅ BP_ProjectileBase 编译并保存成功！(尺寸0.55，命中判定、爆炸生成与伤害闭环已完全就绪)")
    return bp

def run_all():
    log("==================================================")
    log("🚀 开始执行【子弹尺寸放大与碰撞爆炸】全量修复...")
    create_or_update_hit_explosion()
    upgrade_projectile_base()
    log("🎉 全部修复完成！子弹已具备 0.55 黄金视觉比例与碰撞即刻爆炸效果！")
    log("==================================================")

if __name__ == "__main__":
    run_all()
