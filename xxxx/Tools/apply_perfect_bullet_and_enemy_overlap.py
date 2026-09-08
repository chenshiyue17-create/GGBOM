# -*- coding: utf-8 -*-
"""
apply_perfect_bullet_and_enemy_overlap.py
彻底解决：
1. 怪物是 ECC_WORLD_DYNAMIC，子弹必须对 ECC_WORLD_DYNAMIC 和 ECC_PAWN 开启 ECR_OVERLAP！
2. Branch 节点的输出引脚名字是 "then" 和 "else"，精确连通 else 分支到爆炸链路！
3. 命中主角 (then) 彻底放行不爆炸不销毁，命中敌人 (else) 立即触发微缩火光 (0.35无黑影) 并自毁！
"""
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
REPORT_PATH = ROOT / "output/perfect_bullet_overlap_report.json"

def log(msg):
    unreal.log(f"[PERFECT_COMBAT] {msg}")
    print(f"[PERFECT_COMBAT] {msg}", flush=True)

def run():
    log("==================================================")
    log("🚀 启动子弹-敌人完美命中闭环修复流水线...")

    ASSETS = unreal.EditorAssetLibrary
    BPLIB = unreal.BlueprintEditorLibrary
    PINLIB = unreal.BlueprintGraphPinLibrary

    # 1. 确保主角拥有 Player 标签
    player_bp = ASSETS.load_asset("/Game/Blueprints/Player/BP_Player_Medic")
    if player_bp:
        cdo_p = unreal.get_default_object(player_bp.generated_class())
        if cdo_p:
            tags = list(cdo_p.get_editor_property("tags"))
            if "Player" not in tags:
                tags.append("Player")
                cdo_p.set_editor_property("tags", tags)
        BPLIB.compile_blueprint(player_bp)
        ASSETS.save_loaded_asset(player_bp, only_if_is_dirty=False)
        log("  🏷️ 主角 BP_Player_Medic 'Player' 标签已锁定")

    # 2. 调校爆炸蓝图 BP_Combat_HitExplosion (Scale=0.35, 无阴影, 寿命0.22s)
    exp_bp = ASSETS.load_asset("/Game/Blueprints/Combat/Projectiles/BP_Combat_HitExplosion")
    if exp_bp:
        subsys = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
        handles = subsys.k2_gather_subobject_data_for_blueprint(exp_bp)
        for h in handles:
            data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
            vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data)).lower()
            obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, exp_bp)
            if not obj:
                continue
            if isinstance(obj, unreal.PaperFlipbookComponent) or "flipbook" in vname:
                obj.set_editor_property("relative_scale3d", unreal.Vector(0.35, 0.35, 0.35))
                try: obj.set_editor_property("cast_shadow", False)
                except Exception: pass
                try: obj.set_cast_shadow(False)
                except Exception: pass
                obj.set_editor_property("translucency_sort_priority", 3000)
            if isinstance(obj, unreal.PaperSpriteComponent) or "sprite" in vname:
                try: obj.set_editor_property("source_sprite", None)
                except Exception: pass
                obj.set_editor_property("relative_scale3d", unreal.Vector(0.0, 0.0, 0.0))
                obj.set_editor_property("hidden_in_game", True)
                obj.set_editor_property("visible", False)
                try: obj.set_editor_property("cast_shadow", False)
                except Exception: pass

        cdo_exp = unreal.get_default_object(exp_bp.generated_class())
        if cdo_exp:
            cdo_exp.set_editor_property("initial_life_span", 0.22)
        BPLIB.compile_blueprint(exp_bp)
        ASSETS.save_loaded_asset(exp_bp, only_if_is_dirty=False)
        log("  💥 爆炸特效已锁定: Scale=0.35, CastShadow=False, LifeSpan=0.22s")

    # 3. 权威重构 BP_ProjectileBase
    proj_bp = ASSETS.load_asset("/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase")
    if not proj_bp:
        raise RuntimeError("未找到子弹蓝图")

    subsys = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = subsys.k2_gather_subobject_data_for_blueprint(proj_bp)
    sphere_comp = None

    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data)).lower()
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, proj_bp)
        if not obj:
            continue
        if isinstance(obj, unreal.SphereComponent) or "sphere" in vname:
            sphere_comp = obj
        elif isinstance(obj, unreal.PaperSpriteComponent) or "sprite" in vname:
            try: obj.set_editor_property("source_sprite", None)
            except Exception: pass
            obj.set_editor_property("relative_scale3d", unreal.Vector(0.0, 0.0, 0.0))
            obj.set_editor_property("hidden_in_game", True)
            obj.set_editor_property("visible", False)

    if sphere_comp:
        # 核心关键：怪物全部是 ECC_WORLD_DYNAMIC！子弹必须对 ECC_WORLD_DYNAMIC 和 ECC_PAWN 同时响应 OVERLAP！
        sphere_comp.set_editor_property("sphere_radius", 20.0)
        sphere_comp.set_collision_profile_name("Custom")
        sphere_comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_ONLY)
        sphere_comp.set_collision_response_to_all_channels(unreal.CollisionResponseType.ECR_IGNORE)
        sphere_comp.set_collision_response_to_channel(unreal.CollisionChannel.ECC_WORLD_DYNAMIC, unreal.CollisionResponseType.ECR_OVERLAP)
        sphere_comp.set_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN, unreal.CollisionResponseType.ECR_OVERLAP)
        sphere_comp.set_editor_property("generate_overlap_events", True)
        try: sphere_comp.set_editor_property("cast_shadow", False)
        except Exception: pass
        log("  🎯 子弹碰撞矩阵配置完成: ECC_WORLD_DYNAMIC=OVERLAP, ECC_PAWN=OVERLAP, 地表=IGNORE")

    # 4. 图表节点清除与官方引脚权威连接
    graph = BPLIB.find_event_graph(proj_bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    all_nodes = ed.list_all_nodes()
    if all_nodes:
        for n in all_nodes:
            for p in BPLIB.list_all_pins(n):
                try: PINLIB.break_pin_links(p)
                except Exception: pass
        ed.remove_nodes(all_nodes)

    def get_pin(node, name, is_input=None):
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

    def connect(n1, p1, n2, p2):
        sp = get_pin(n1, p1, is_input=False)
        tp = get_pin(n2, p2, is_input=True)
        if sp and tp:
            ok = PINLIB.try_create_connection(sp, tp)
            if not ok:
                log(f"  ⚠️ 连接失败: {BPLIB.get_node_title(n1)}.{p1} -> {BPLIB.get_node_title(n2)}.{p2}")
            return ok
        else:
            log(f"  ❌ 引脚未找到: {p1} -> {p2}")
            return False

    def add_fn(fn_path, x, y):
        n = ed.add_call_function_node(fn_path)
        if n: n.set_node_pos(unreal.IntPoint(x, y))
        return n

    def set_val(n, pin_name, val):
        p = get_pin(n, pin_name, is_input=True)
        if p:
            try: PINLIB.set_pin_value(p, str(val))
            except Exception as e: log(f"设置引脚异常: {e}")

    # --- 逻辑 1: BeginPlay 2.0s 兜底超时自毁 ---
    begin_play = BPLIB.add_event_override(proj_bp, "ReceiveBeginPlay", unreal.IntPoint(-500, -300))
    delay_node = add_fn("/Script/Engine.KismetSystemLibrary.Delay", -200, -300)
    set_val(delay_node, "Duration", 2.0)
    destroy_timeout = add_fn("/Script/Engine.Actor.K2_DestroyActor", 100, -300)
    if begin_play and delay_node and destroy_timeout:
        connect(begin_play, "then", delay_node, "execute")
        connect(delay_node, "then", destroy_timeout, "execute")

    # --- 逻辑 2: ReceiveActorBeginOverlap 核心受击与防自碰判定 ---
    overlap_ev = BPLIB.add_event_override(proj_bp, "ReceiveActorBeginOverlap", unreal.IntPoint(-500, 100))

    # 判断 1: OtherActor 是否拥有 "Player" Tag
    has_tag = add_fn("/Script/Engine.Actor.ActorHasTag", -180, 220)
    set_val(has_tag, "Tag", "Player")
    if overlap_ev and has_tag:
        connect(overlap_ev, "OtherActor", has_tag, "self")

    # 判断 2: OtherActor 是否是当前本地 PlayerPawn
    get_pc = add_fn("/Script/Engine.GameplayStatics.GetPlayerController", -350, 400)
    set_val(get_pc, "PlayerIndex", 0)
    get_pawn = add_fn("/Script/Engine.Controller.K2_GetPawn", -120, 400)
    if get_pc and get_pawn:
        connect(get_pc, "ReturnValue", get_pawn, "self")

    eq_pawn = add_fn("/Script/Engine.KismetMathLibrary.EqualEqual_ObjectObject", 100, 320)
    if overlap_ev and get_pawn and eq_pawn:
        connect(overlap_ev, "OtherActor", eq_pawn, "A")
        connect(get_pawn, "ReturnValue", eq_pawn, "B")

    # 综合判定: 是 Player 标签 OR 是 Player Pawn
    or_node = add_fn("/Script/Engine.KismetMathLibrary.BooleanOR", 320, 240)
    if has_tag and eq_pawn and or_node:
        connect(has_tag, "ReturnValue", or_node, "A")
        connect(eq_pawn, "ReturnValue", or_node, "B")

    # Branch 节点 (Inputs: execute, Condition; Outputs: then, else)
    branch_node = ed.add_branch_node()
    branch_node.set_node_pos(unreal.IntPoint(500, 100))
    if overlap_ev and branch_node and or_node:
        connect(overlap_ev, "then", branch_node, "execute")
        connect(or_node, "ReturnValue", branch_node, "Condition")

    # --- 命中敌人分支 (精准从 Branch 的 'else' 引脚连接！) ---
    loc_node = add_fn("/Script/Engine.Actor.K2_GetActorLocation", 720, 260)
    trans_node = add_fn("/Script/Engine.KismetMathLibrary.MakeTransform", 940, 260)
    set_val(trans_node, "Scale", "1,1,1")
    if loc_node and trans_node:
        connect(loc_node, "ReturnValue", trans_node, "Location")

    spawn_exp = add_fn("/Script/Engine.GameplayStatics.BeginDeferredActorSpawnFromClass", 1180, 100)
    if spawn_exp:
        set_val(spawn_exp, "ActorClass", "Class'/Game/Blueprints/Combat/Projectiles/BP_Combat_HitExplosion.BP_Combat_HitExplosion_C'")
        if trans_node:
            connect(trans_node, "ReturnValue", spawn_exp, "SpawnTransform")

    finish_exp = add_fn("/Script/Engine.GameplayStatics.FinishSpawningActor", 1460, 100)
    if finish_exp and spawn_exp:
        connect(spawn_exp, "then", finish_exp, "execute")
        connect(spawn_exp, "ReturnValue", finish_exp, "Actor")
        if trans_node:
            connect(trans_node, "ReturnValue", finish_exp, "SpawnTransform")

    apply_dmg = add_fn("/Script/Engine.GameplayStatics.ApplyDamage", 1720, 100)
    set_val(apply_dmg, "BaseDamage", 45.0)
    if overlap_ev and apply_dmg:
        connect(overlap_ev, "OtherActor", apply_dmg, "DamagedActor")

    destroy_self = add_fn("/Script/Engine.Actor.K2_DestroyActor", 1980, 100)

    # 关键：通过精确的 'else' 引脚连接到 spawn_exp 的 'execute'
    conn_else = connect(branch_node, "else", spawn_exp, "execute")
    log(f"  🔗 Branch.else -> SpawnActor(Explosion) 连接状态: {'SUCCESS' if conn_else else 'FAILED'}")

    connect(finish_exp, "then", apply_dmg, "execute")
    connect(apply_dmg, "then", destroy_self, "execute")

    BPLIB.compile_blueprint(proj_bp)
    saved_proj = ASSETS.save_loaded_asset(proj_bp, only_if_is_dirty=False)
    log(f"  💾 BP_ProjectileBase 编译与存盘: {'成功' if saved_proj else '失败'}")

    report = {
        "status": "PASS" if (saved_proj and conn_else) else "FAIL",
        "branch_else_connected": conn_else,
        "enemy_collision_channel": "ECC_WORLD_DYNAMIC + ECC_PAWN",
        "bullet_saved": saved_proj,
        "explosion_scale": 0.35
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    log(f"📄 最终诊断与验收报告: {REPORT_PATH}")

if __name__ == "__main__":
    run()
