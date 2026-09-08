# -*- coding: utf-8 -*-
"""
inject_damage_zombie.py
为 BP_Enemy_ZombieWalker 注入 ReceiveAnyDamage 扣血与死亡销毁 (K2_DestroyActor)
保持原有 Tick 寻路和避障完全不受影响！
"""
import unreal
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/inject_damage_zombie.txt"
OUT.parent.mkdir(parents=True, exist_ok=True)

ASSETS = unreal.EditorAssetLibrary
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary

def log(msg):
    unreal.log(f"[ZOMBIE_DAMAGE] {msg}")
    print(f"[ZOMBIE_DAMAGE] {msg}", flush=True)

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
    bp_path = "/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker"
    log(f"🚀 加载行尸蓝图: {bp_path}")
    bp = ASSETS.load_asset(bp_path)
    if not bp: raise RuntimeError(f"未找到: {bp_path}")

    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)

    # 检查是否已存在 ReceiveAnyDamage 节点，如果有旧的先断开连接
    existing_dmg = ed.find_event_node("ReceiveAnyDamage")
    if existing_dmg:
        for p in BPLIB.list_all_pins(existing_dmg):
            try: PINLIB.break_pin_links(p)
            except Exception: pass
        dmg_node = existing_dmg
        dmg_node.set_node_pos(unreal.IntPoint(0, 1000))
    else:
        dmg_node = BPLIB.add_event_override(bp, "ReceiveAnyDamage", unreal.IntPoint(0, 1000))

    def fn(path, x, y):
        n = ed.add_call_function_node(path)
        n.set_node_pos(unreal.IntPoint(x, y))
        return n

    # 1. 扣减生命值: CurrentHealth = CurrentHealth - Damage
    cur_hp = ed.add_get_member_variable_node("CurrentHealth")
    cur_hp.set_node_pos(unreal.IntPoint(260, 1120))

    sub_hp = fn("/Script/Engine.KismetMathLibrary.Subtract_DoubleDouble", 460, 1060)
    connect(cur_hp, "CurrentHealth", sub_hp, "A")
    connect(dmg_node, "Damage", sub_hp, "B")

    set_hp = ed.add_set_member_variable_node("CurrentHealth")
    set_hp.set_node_pos(unreal.IntPoint(720, 1000))
    connect(dmg_node, "then", set_hp, "execute")
    connect(sub_hp, "ReturnValue", set_hp, "CurrentHealth")

    # 2. 死亡判定: CurrentHealth <= 0.0
    is_dead = fn("/Script/Engine.KismetMathLibrary.LessEqual_DoubleDouble", 720, 1140)
    connect(sub_hp, "ReturnValue", is_dead, "A")
    set_value(is_dead, "B", 0.0)

    branch_dead = ed.add_branch_node()
    branch_dead.set_node_pos(unreal.IntPoint(960, 1000))
    connect(set_hp, "then", branch_dead, "execute")
    connect(is_dead, "ReturnValue", branch_dead, "Condition")

    # 3. 死亡分支 (then): 销毁怪物 Actor
    destroy_node = fn("/Script/Engine.Actor.K2_DestroyActor", 1200, 980)
    connect(branch_dead, "then", destroy_node, "execute")

    BPLIB.compile_blueprint(bp)
    saved = ASSETS.save_loaded_asset(bp)
    log(f"✅ 行尸蓝图受击扣血与死亡销毁构建完成, 保存状态: {saved}")
    OUT.write_text(f"SAVED: {saved}\n", encoding="utf-8")

if __name__ == "__main__":
    import traceback
    try:
        run()
    except Exception as e:
        err = traceback.format_exc()
        log(f"CRASH: {err}")
        OUT.write_text(f"ERROR: {err}\n", encoding="utf-8")
        raise
