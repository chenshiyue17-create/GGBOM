# -*- coding: utf-8 -*-
"""
================================================================================
apply_bullet_hit_and_destroy_closure.py
权威重构 BP_ProjectileBase 核心图表逻辑：
1. ReceiveBeginPlay -> Delay(1.8) -> K2_DestroyActor (飞出屏幕主动自毁)
2. ReceiveActorBeginOverlap & ReceiveHit -> 过滤主角 -> 生成爆炸特效 -> ApplyDamage -> K2_DestroyActor
3. 锁定 CollisionSphere 物理参数，双通道阻挡/重叠
================================================================================
"""
import json
import os
import unreal

PROJ_BP_PATH = "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase"
EXP_BP_PATH = "/Game/Blueprints/Combat/Projectiles/BP_Combat_HitExplosion"
EXP_CLASS_STR = "Class'/Game/Blueprints/Combat/Projectiles/BP_Combat_HitExplosion.BP_Combat_HitExplosion_C'"

BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary

def log(msg):
    unreal.log(f"[BULLET_CLOSURE] {msg}")
    print(f"[BULLET_CLOSURE] {msg}")

def get_pin(node, name, is_input=None):
    if not node:
        return None
    pins = []
    if is_input is True:
        pins = BPLIB.list_input_pins(node)
    elif is_input is False:
        pins = BPLIB.list_output_pins(node)
    else:
        pins = list(BPLIB.list_input_pins(node)) + list(BPLIB.list_output_pins(node))
        
    for p in pins:
        p_name = str(PINLIB.get_pin_name(p))
        if p_name.lower() == name.lower():
            return p
    return None

def connect_pins(source_node, source_pin, target_node, target_pin):
    sp = get_pin(source_node, source_pin, is_input=False)
    tp = get_pin(target_node, target_pin, is_input=True)
    if sp and tp:
        ok = PINLIB.try_create_connection(sp, tp)
        if not ok:
            log(f"  ⚠️ 连接失败: {BPLIB.get_node_title(source_node)}.{source_pin} -> {BPLIB.get_node_title(target_node)}.{target_pin}")
        return ok
    else:
        log(f"  ❌ 引脚缺失: sp={'OK' if sp else source_pin} -> tp={'OK' if tp else target_pin}")
        return False

def set_pin_val(node, pin_name, value):
    p = get_pin(node, pin_name, is_input=True)
    if p:
        try:
            PINLIB.set_pin_value(p, str(value))
            return True
        except Exception as e:
            log(f"  ⚠️ 设置引脚值失败 {pin_name}={value}: {e}")
    return False

def add_fn(ed, fn_path, x, y):
    node = ed.add_call_function_node(fn_path)
    if node:
        node.set_node_pos(unreal.IntPoint(x, y))
    else:
        log(f"  ❌ 无法添加函数节点: {fn_path}")
    return node

def build_projectile_logic():
    log("==================================================")
    log("🚀 开始权威重塑 BP_ProjectileBase 图表与物理配置...")
    
    bp = unreal.EditorAssetLibrary.load_asset(PROJ_BP_PATH)
    if not bp:
        raise RuntimeError(f"无法加载蓝图: {PROJ_BP_PATH}")
        
    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    
    # 1. 彻底清空所有旧节点，斩断任何脏引用
    all_nodes = ed.list_all_nodes()
    if all_nodes:
        log(f"  🧹 正在清除旧节点: {len(all_nodes)} 个")
        for n in all_nodes:
            for p in BPLIB.list_all_pins(n):
                try:
                    PINLIB.break_pin_links(p)
                except Exception:
                    pass
        ed.remove_nodes(all_nodes)
        
    # 2. 构建生命周期超时兜底：ReceiveBeginPlay -> Delay(1.8s) -> K2_DestroyActor
    log("  ⏱️ 构建超时保底自毁链条...")
    begin_play = BPLIB.add_event_override(bp, "ReceiveBeginPlay", unreal.IntPoint(-400, -350))
    delay_node = add_fn(ed, "/Script/Engine.KismetSystemLibrary.Delay", -150, -350)
    set_pin_val(delay_node, "Duration", 1.8)
    destroy_timeout = add_fn(ed, "/Script/Engine.Actor.K2_DestroyActor", 120, -350)
    
    if begin_play and delay_node and destroy_timeout:
        connect_pins(begin_play, "then", delay_node, "execute")
        connect_pins(delay_node, "then", destroy_timeout, "execute")
        log("    ✅ BeginPlay -> Delay(1.8s) -> DestroyActor 连线就绪")

    # 3. 构建命中触发器：同时挂接 ReceiveActorBeginOverlap 和 ReceiveHit
    log("  💥 构建核心命中触发与爆炸销毁闭环...")
    overlap_event = BPLIB.add_event_override(bp, "ReceiveActorBeginOverlap", unreal.IntPoint(-400, 0))
    hit_event = BPLIB.add_event_override(bp, "ReceiveHit", unreal.IntPoint(-400, 350))

    # 4. 主角过滤模块 (排除自身)
    get_pc = add_fn(ed, "/Script/Engine.GameplayStatics.GetPlayerController", -150, 150)
    set_pin_val(get_pc, "PlayerIndex", 0)
    get_player = add_fn(ed, "/Script/Engine.Controller.K2_GetPawn", 80, 150)
    if get_pc and get_player:
        connect_pins(get_pc, "ReturnValue", get_player, "self")
        
    # Overlap 过滤判断
    not_player_overlap = add_fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_ObjectObject", 300, 50)
    if overlap_event and not_player_overlap and get_player:
        connect_pins(overlap_event, "OtherActor", not_player_overlap, "A")
        connect_pins(get_player, "ReturnValue", not_player_overlap, "B")
        
    branch_overlap = ed.add_branch_node()
    branch_overlap.set_node_pos(unreal.IntPoint(520, 0))
    if overlap_event and branch_overlap and not_player_overlap:
        connect_pins(overlap_event, "then", branch_overlap, "execute")
        connect_pins(not_player_overlap, "ReturnValue", branch_overlap, "Condition")

    # 5. 命中爆炸特效生成: GetActorLocation -> MakeTransform -> Spawn BP_Combat_HitExplosion
    loc_node = add_fn(ed, "/Script/Engine.Actor.K2_GetActorLocation", 720, 180)
    trans_node = add_fn(ed, "/Script/Engine.KismetMathLibrary.MakeTransform", 940, 180)
    set_pin_val(trans_node, "Scale", "1,1,1")
    if loc_node and trans_node:
        connect_pins(loc_node, "ReturnValue", trans_node, "Location")

    spawn_exp = add_fn(ed, "/Script/Engine.GameplayStatics.BeginDeferredActorSpawnFromClass", 1180, 0)
    if spawn_exp:
        set_pin_val(spawn_exp, "ActorClass", EXP_CLASS_STR)
        if trans_node:
            connect_pins(trans_node, "ReturnValue", spawn_exp, "SpawnTransform")
            
    finish_exp = add_fn(ed, "/Script/Engine.GameplayStatics.FinishSpawningActor", 1460, 0)
    if finish_exp and spawn_exp:
        connect_pins(spawn_exp, "then", finish_exp, "execute")
        connect_pins(spawn_exp, "ReturnValue", finish_exp, "Actor")
        if trans_node:
            connect_pins(trans_node, "ReturnValue", finish_exp, "SpawnTransform")

    # 6. 伤害施加: ApplyDamage(45.0) -> OtherActor
    apply_dmg = add_fn(ed, "/Script/Engine.GameplayStatics.ApplyDamage", 1720, 0)
    set_pin_val(apply_dmg, "BaseDamage", 45.0)
    if overlap_event and apply_dmg:
        connect_pins(overlap_event, "OtherActor", apply_dmg, "DamagedActor")

    # 7. 即刻销毁自身: K2_DestroyActor (杜绝残留)
    destroy_hit = add_fn(ed, "/Script/Engine.Actor.K2_DestroyActor", 1980, 0)

    # 连线执行流：Branch.True -> SpawnExp -> FinishExp -> ApplyDamage -> DestroyActor
    if branch_overlap and spawn_exp:
        connect_pins(branch_overlap, "then", spawn_exp, "execute")
    if finish_exp and apply_dmg:
        connect_pins(finish_exp, "then", apply_dmg, "execute")
    if apply_dmg and destroy_hit:
        connect_pins(apply_dmg, "then", destroy_hit, "execute")

    # 8. 同时将 ReceiveHit 也挂接到该链条（实现 Overlap + Hit 双保险）
    not_player_hit = add_fn(ed, "/Script/Engine.KismetMathLibrary.NotEqual_ObjectObject", 300, 400)
    if hit_event and not_player_hit and get_player:
        connect_pins(hit_event, "Other", not_player_hit, "A")
        connect_pins(get_player, "ReturnValue", not_player_hit, "B")
        
    branch_hit = ed.add_branch_node()
    branch_hit.set_node_pos(unreal.IntPoint(520, 350))
    if hit_event and branch_hit and not_player_hit:
        connect_pins(hit_event, "then", branch_hit, "execute")
        connect_pins(not_player_hit, "ReturnValue", branch_hit, "Condition")
        
    # Hit 分支也同样导向生成爆炸与销毁
    spawn_exp_hit = add_fn(ed, "/Script/Engine.GameplayStatics.BeginDeferredActorSpawnFromClass", 1180, 350)
    if spawn_exp_hit:
        set_pin_val(spawn_exp_hit, "ActorClass", EXP_CLASS_STR)
        if trans_node:
            connect_pins(trans_node, "ReturnValue", spawn_exp_hit, "SpawnTransform")
    finish_exp_hit = add_fn(ed, "/Script/Engine.GameplayStatics.FinishSpawningActor", 1460, 350)
    if finish_exp_hit and spawn_exp_hit:
        connect_pins(spawn_exp_hit, "then", finish_exp_hit, "execute")
        connect_pins(spawn_exp_hit, "ReturnValue", finish_exp_hit, "Actor")
        if trans_node:
            connect_pins(trans_node, "ReturnValue", finish_exp_hit, "SpawnTransform")
    apply_dmg_hit = add_fn(ed, "/Script/Engine.GameplayStatics.ApplyDamage", 1720, 350)
    set_pin_val(apply_dmg_hit, "BaseDamage", 45.0)
    if hit_event and apply_dmg_hit:
        connect_pins(hit_event, "Other", apply_dmg_hit, "DamagedActor")
    destroy_hit_2 = add_fn(ed, "/Script/Engine.Actor.K2_DestroyActor", 1980, 350)
    if branch_hit and spawn_exp_hit:
        connect_pins(branch_hit, "then", spawn_exp_hit, "execute")
    if finish_exp_hit and apply_dmg_hit:
        connect_pins(finish_exp_hit, "then", apply_dmg_hit, "execute")
    if apply_dmg_hit and destroy_hit_2:
        connect_pins(apply_dmg_hit, "then", destroy_hit_2, "execute")

    log("  ✅ 双通道命中逻辑编排完毕 (Overlap 与 Hit 均支持爆炸与即刻自毁)")

    # 9. 物理碰撞与组件配置
    subsys = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = subsys.k2_gather_subobject_data_for_blueprint(bp)
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data)).lower()
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
        if not obj: continue
        
        if isinstance(obj, unreal.SphereComponent) or "sphere" in vname or "collision" in vname:
            obj.set_editor_property("sphere_radius", 24.0)
            obj.set_editor_property("relative_scale3d", unreal.Vector(1.0, 1.0, 1.0))
            obj.set_collision_profile_name("Custom")
            obj.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
            try:
                obj.set_editor_property("generate_overlap_events", True)
            except Exception:
                pass
            try:
                obj.set_editor_property("notify_rigid_body_collision", True)
            except Exception:
                pass
            
            # 基础配置：地面穿透，敌人 Pawn 与 WorldDynamic 双通道同时阻挡并重叠
            obj.set_collision_response_to_all_channels(unreal.CollisionResponseType.ECR_IGNORE)
            obj.set_collision_response_to_channel(unreal.CollisionChannel.ECC_WORLD_STATIC, unreal.CollisionResponseType.ECR_IGNORE)
            obj.set_collision_response_to_channel(unreal.CollisionChannel.ECC_WORLD_DYNAMIC, unreal.CollisionResponseType.ECR_BLOCK)
            obj.set_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN, unreal.CollisionResponseType.ECR_BLOCK)
            obj.set_collision_response_to_channel(unreal.CollisionChannel.ECC_VISIBILITY, unreal.CollisionResponseType.ECR_BLOCK)
            log("  🎯 CollisionSphere 已配置: Radius=24.0, ECC_Pawn=BLOCK, ECC_WorldDynamic=BLOCK, Static=IGNORE")
            
        elif isinstance(obj, unreal.ProjectileMovementComponent) or "move" in vname:
            obj.set_editor_property("initial_speed", 1200.0)
            obj.set_editor_property("max_speed", 1200.0)
            obj.set_editor_property("projectile_gravity_scale", 0.0)
            obj.set_editor_property("velocity", unreal.Vector(1200.0, 0.0, 0.0))
            for prop in ["initial_velocity_in_local_space", "rotation_follows_velocity", "b_initial_velocity_in_local_space", "b_rotation_follows_velocity"]:
                try: obj.set_editor_property(prop, True)
                except Exception: pass
            log("  🎯 ProjectileMovement 已锁定 1200 速度")

    # CDO 参数锁定
    cdo = unreal.get_default_object(bp.generated_class())
    if cdo:
        cdo.set_editor_property("initial_life_span", 1.8)
        
    # 10. 编译并持久化写盘
    BPLIB.compile_blueprint(bp)
    saved = unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"💾 BP_ProjectileBase 编译并持久化写盘: {'成功' if saved else '未变动'}")
    
    # 验证节点总数
    final_nodes = ed.list_all_nodes()
    log(f"🎉 最终图表节点总数: {len(final_nodes)}")
    for fn in final_nodes:
        log(f"    - {BPLIB.get_node_title(fn)} ({fn.get_class().get_name()})")
        
    report = {
        "BP_ProjectileBase_Saved": saved,
        "Final_Node_Count": len(final_nodes),
        "Nodes": [str(BPLIB.get_node_title(fn)) for fn in final_nodes]
    }
    out_file = "/Users/cc/Desktop/GGBOM/xxxx/output/bullet_closure_report.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        
    log("==================================================")
    return saved

if __name__ == "__main__":
    build_projectile_logic()
