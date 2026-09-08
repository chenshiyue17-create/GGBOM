# -*- coding: utf-8 -*-
"""
upgrade_bullet_with_damage_pop.py
升级子弹 BP_ProjectileBase：
命中敌人时生成微缩火光爆炸 + 生成 -45 伤害飘字 + ApplyDamage(45.0) + 自毁
"""
import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/upgrade_bullet_result.txt"

ASSETS = unreal.EditorAssetLibrary
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary

def log(msg):
    unreal.log(f"[BULLET_UPGRADE] {msg}")
    print(f"[BULLET_UPGRADE] {msg}", flush=True)

def pin(node, name, output=None):
    if output is True: pins = BPLIB.list_output_pins(node)
    elif output is False: pins = BPLIB.list_input_pins(node)
    else: pins = list(BPLIB.list_output_pins(node)) + list(BPLIB.list_input_pins(node))
    wanted = name.lower()
    for p in pins:
        if str(PINLIB.get_pin_name(p)).lower() == wanted: return p
    avail = [str(PINLIB.get_pin_name(p)) for p in pins]
    raise RuntimeError(f"Pin '{name}' not found, avail: {avail}")

def set_value(node, name, value):
    p = pin(node, name, False)
    PINLIB.set_pin_value(p, str(value))

def connect(n1, p1, n2, p2):
    sp = pin(n1, p1, True); tp = pin(n2, p2, False)
    PINLIB.try_create_connection(sp, tp)

def run():
    proj_bp_path = "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase"
    log(f"🚀 升级子弹蓝图: {proj_bp_path}")
    bp = ASSETS.load_asset(proj_bp_path)
    if not bp: raise RuntimeError(f"未找到: {proj_bp_path}")

    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    
    all_nodes = ed.list_all_nodes()
    if all_nodes:
        for n in all_nodes:
            for p in BPLIB.list_all_pins(n):
                try: PINLIB.break_pin_links(p)
                except Exception: pass
        ed.remove_nodes(all_nodes)

    def fn(path, x, y):
        n = ed.add_call_function_node(path); n.set_node_pos(unreal.IntPoint(x, y)); return n

    # 1. 2秒超时自毁
    begin_play = BPLIB.add_event_override(bp, "ReceiveBeginPlay", unreal.IntPoint(-500, -300))
    delay_node = fn("/Script/Engine.KismetSystemLibrary.Delay", -200, -300)
    set_value(delay_node, "Duration", 2.0)
    connect(begin_play, "then", delay_node, "execute")
    destroy_timeout = fn("/Script/Engine.Actor.K2_DestroyActor", 100, -300)
    connect(delay_node, "then", destroy_timeout, "execute")

    # 2. ReceiveActorBeginOverlap 核心受击判定
    overlap_ev = BPLIB.add_event_override(bp, "ReceiveActorBeginOverlap", unreal.IntPoint(-500, 100))

    has_tag = fn("/Script/Engine.Actor.ActorHasTag", -180, 220); set_value(has_tag, "Tag", "Player")
    connect(overlap_ev, "OtherActor", has_tag, "self")

    get_pc = fn("/Script/Engine.GameplayStatics.GetPlayerController", -350, 400); set_value(get_pc, "PlayerIndex", 0)
    get_pawn = fn("/Script/Engine.Controller.K2_GetPawn", -120, 400)
    connect(get_pc, "ReturnValue", get_pawn, "self")

    eq_pawn = fn("/Script/Engine.KismetMathLibrary.EqualEqual_ObjectObject", 100, 320)
    connect(overlap_ev, "OtherActor", eq_pawn, "A")
    connect(get_pawn, "ReturnValue", eq_pawn, "B")

    or_node = fn("/Script/Engine.KismetMathLibrary.BooleanOR", 320, 240)
    connect(has_tag, "ReturnValue", or_node, "A")
    connect(eq_pawn, "ReturnValue", or_node, "B")

    branch_node = ed.add_branch_node()
    branch_node.set_node_pos(unreal.IntPoint(500, 100))
    connect(overlap_ev, "then", branch_node, "execute")
    connect(or_node, "ReturnValue", branch_node, "Condition")

    # --- 命中敌人分支 (branch_node.else) ---
    loc_node = fn("/Script/Engine.Actor.K2_GetActorLocation", 720, 260)

    # 爆炸 Transform (原位)
    trans_exp = fn("/Script/Engine.KismetMathLibrary.MakeTransform", 940, 260)
    set_value(trans_exp, "Scale", "1,1,1")
    connect(loc_node, "ReturnValue", trans_exp, "Location")

    # 爆炸 Actor 生成
    spawn_exp = fn("/Script/Engine.GameplayStatics.BeginDeferredActorSpawnFromClass", 1180, 100)
    set_value(spawn_exp, "ActorClass", "Class'/Game/Blueprints/Combat/Projectiles/BP_Combat_HitExplosion.BP_Combat_HitExplosion_C'")
    connect(trans_exp, "ReturnValue", spawn_exp, "SpawnTransform")
    connect(branch_node, "else", spawn_exp, "execute")

    finish_exp = fn("/Script/Engine.GameplayStatics.FinishSpawningActor", 1460, 100)
    connect(spawn_exp, "then", finish_exp, "execute")
    connect(spawn_exp, "ReturnValue", finish_exp, "Actor")
    connect(trans_exp, "ReturnValue", finish_exp, "SpawnTransform")

    # 飘字 Transform (受击点上方 35 uu)
    break_loc = fn("/Script/Engine.KismetMathLibrary.BreakVector", 940, 440)
    connect(loc_node, "ReturnValue", break_loc, "InVec")

    add_z = fn("/Script/Engine.KismetMathLibrary.Add_DoubleDouble", 1160, 480)
    connect(break_loc, "Z", add_z, "A"); set_value(add_z, "B", 35.0)

    make_pop_loc = fn("/Script/Engine.KismetMathLibrary.MakeVector", 1380, 440)
    connect(break_loc, "X", make_pop_loc, "X")
    connect(break_loc, "Y", make_pop_loc, "Y")
    connect(add_z, "ReturnValue", make_pop_loc, "Z")

    trans_pop = fn("/Script/Engine.KismetMathLibrary.MakeTransform", 1600, 440)
    set_value(trans_pop, "Scale", "1,1,1")
    connect(make_pop_loc, "ReturnValue", trans_pop, "Location")

    # 飘字 Actor 生成 (BP_Combat_DamagePop)
    spawn_pop = fn("/Script/Engine.GameplayStatics.BeginDeferredActorSpawnFromClass", 1720, 100)
    set_value(spawn_pop, "ActorClass", "Class'/Game/Blueprints/Combat/Projectiles/BP_Combat_DamagePop.BP_Combat_DamagePop_C'")
    connect(trans_pop, "ReturnValue", spawn_pop, "SpawnTransform")
    connect(finish_exp, "then", spawn_pop, "execute")

    finish_pop = fn("/Script/Engine.GameplayStatics.FinishSpawningActor", 2000, 100)
    connect(spawn_pop, "then", finish_pop, "execute")
    connect(spawn_pop, "ReturnValue", finish_pop, "Actor")
    connect(trans_pop, "ReturnValue", finish_pop, "SpawnTransform")

    # 伤害结算 ApplyDamage
    apply_dmg = fn("/Script/Engine.GameplayStatics.ApplyDamage", 2260, 100)
    set_value(apply_dmg, "BaseDamage", 45.0)
    connect(overlap_ev, "OtherActor", apply_dmg, "DamagedActor")
    connect(finish_pop, "then", apply_dmg, "execute")

    # 子弹自毁
    destroy_self = fn("/Script/Engine.Actor.K2_DestroyActor", 2520, 100)
    connect(apply_dmg, "then", destroy_self, "execute")

    BPLIB.compile_blueprint(bp)
    saved = ASSETS.save_loaded_asset(bp, only_if_is_dirty=False)
    log(f"  💾 子弹 BP_ProjectileBase 升级落盘: {'成功' if saved else '失败'}")
    OUT.write_text(f"SAVED: {saved}", encoding="utf-8")
    return saved

if __name__ == "__main__":
    run()
