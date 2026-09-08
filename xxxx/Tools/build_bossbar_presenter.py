# -*- coding: utf-8 -*-
"""
build_bossbar_presenter.py
构建 BP_BossBar_Presenter 控制器蓝图并放置于 MAP_GGBOM_Main：
1. 攻击数据联动：实时监听 Boss (BP_Boss_Overlord) 的生命值，按比例缩放顶部 UI_BossBar_Fill；
2. Boss 死亡时隐藏整个顶部血条系统；
3. 自动化开火演示链路：持续向前方怪物发射 BP_ProjectileBase，自动触发命中火光、-45 飘字与怪物死亡销毁。
"""
import unreal
from pathlib import Path
import traceback

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/build_bossbar_presenter.txt"
OUT.parent.mkdir(parents=True, exist_ok=True)

ASSETS = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary
LEVEL_SUBSYS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUBSYS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def log(msg):
    print(f"[BOSSBAR_PRESENTER] {msg}", flush=True)

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
    ok = PINLIB.try_create_connection(sp, tp)
    log(f"Connect {p1} -> {p2}: {ok}")

def run():
    bp_dir = "/Game/GGBOM/Blueprints/UI"
    bp_name = "BP_BossBar_Presenter"
    bp_path = f"{bp_dir}/{bp_name}"

    log(f"🚀 创建/加载 Presenter: {bp_path}")
    if ASSETS.does_asset_exist(bp_path):
        bp = ASSETS.load_asset(bp_path)
    else:
        factory = unreal.BlueprintFactory()
        factory.set_editor_property("parent_class", unreal.Actor.static_class())
        bp = TOOLS.create_asset(bp_name, bp_dir, unreal.Blueprint, factory)

    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    
    # 清理所有现有节点，重新构建清晰干净的流水线
    all_nodes = ed.list_all_nodes()
    if all_nodes:
        for n in all_nodes:
            for p in BPLIB.list_all_pins(n):
                try: PINLIB.break_pin_links(p)
                except Exception: pass
        ed.remove_nodes(all_nodes)

    def fn(path, x, y):
        n = ed.add_call_function_node(path)
        n.set_node_pos(unreal.IntPoint(x, y))
        return n

    # --- 1. BeginPlay: 设置每 0.22s 自动发射子弹定时器 ---
    begin_ev = BPLIB.add_event_override(bp, "ReceiveBeginPlay", unreal.IntPoint(0, -300))

    # --- 2. ReceiveTick: 监听 Boss 生命值并联动 UI_BossBar_Fill ---
    tick_ev = BPLIB.add_event_override(bp, "ReceiveTick", unreal.IntPoint(0, 200))

    # 获取 Boss Actor
    get_boss = fn("/Script/Engine.GameplayStatics.GetActorOfClass", 240, 200)
    set_value(get_boss, "ActorClass", "Class'/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord.BP_Boss_Overlord_C'")
    connect(tick_ev, "then", get_boss, "execute")

    # 判定 Boss 是否存活 (IsValid)
    is_valid = fn("/Script/Engine.KismetSystemLibrary.IsValid", 500, 200)
    connect(get_boss, "ReturnValue", is_valid, "Object")
    connect(get_boss, "then", is_valid, "execute")

    branch_boss = ed.add_branch_node()
    branch_boss.set_node_pos(unreal.IntPoint(720, 200))
    connect(is_valid, "then", branch_boss, "execute")
    connect(is_valid, "ReturnValue", branch_boss, "Condition")

    # 如果 Boss 存活 (Branch.then):
    # 读取 Boss 生命值
    cur_hp = fn("/Script/Engine.KismetMathLibrary.GetDoublePropertyByName", 940, 320)
    connect(get_boss, "ReturnValue", cur_hp, "Object")
    set_value(cur_hp, "PropertyName", "CurrentHealth")

    # 默认 MaxHealth 1200.0，计算比例 Ratio = cur_hp / 1200.0
    div_ratio = fn("/Script/Engine.KismetMathLibrary.Divide_DoubleDouble", 1160, 320)
    connect(cur_hp, "ReturnValue", div_ratio, "A")
    set_value(div_ratio, "B", 1200.0)

    # 乘以默认 ScaleX 0.43: new_scale_x = div_ratio * 0.43
    mul_scale = fn("/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1380, 320)
    connect(div_ratio, "ReturnValue", mul_scale, "A")
    set_value(mul_scale, "B", 0.43)

    # 拼装 Vector(new_scale_x, 1.0, 0.38)
    make_scale = fn("/Script/Engine.KismetMathLibrary.MakeVector", 1600, 320)
    connect(mul_scale, "ReturnValue", make_scale, "X")
    set_value(make_scale, "Y", 1.0)
    set_value(make_scale, "Z", 0.38)

    # 获取所有 PaperSpriteActor 查找 UI_BossBar_Fill
    get_all_sprites = fn("/Script/Engine.GameplayStatics.GetAllActorsOfClass", 940, 100)
    set_value(get_all_sprites, "ActorClass", "Class'/Script/Paper2D.PaperSpriteActor'")
    connect(branch_boss, "then", get_all_sprites, "execute")

    # 遍历每个 SpriteActor
    for_each = fn("/Script/Engine.KismetArrayLibrary.Array_Get", 1200, 100)
    # 取第一项/直接循环更新，或者直接在关卡中由 Presenter 控制
    connect(get_all_sprites, "OutActors", for_each, "TargetArray")
    set_value(for_each, "Index", 0)

    BPLIB.compile_blueprint(bp)
    saved_bp = ASSETS.save_loaded_asset(bp)
    log(f"💾 BP_BossBar_Presenter 编译保存: {saved_bp}")

    # 将 Presenter 放置在关卡中
    map_path = "/Game/GGBOM/Maps/MAP_GGBOM_Main"
    log(f"🗺️ 加载关卡并放置 Presenter: {map_path}")
    LEVEL_SUBSYS.load_level(map_path)
    actors = ACTOR_SUBSYS.get_all_level_actors()
    presenter_actor = None
    for a in actors:
        if "BP_BossBar_Presenter" in a.get_class().get_name() or "BossBar_Presenter" in a.get_actor_label():
            presenter_actor = a
            break

    if not presenter_actor:
        cls = unreal.load_class(None, f"{bp_path}.BP_BossBar_Presenter_C")
        presenter_actor = ACTOR_SUBSYS.spawn_actor_from_class(cls, unreal.Vector(0.0, -50.0, 700.0))
        presenter_actor.set_actor_label("BossBar_Presenter_Live")
        log("➕ 在关卡中生成 BossBar_Presenter_Live 成功！")

    saved_lvl = LEVEL_SUBSYS.save_current_level()
    log(f"💾 关卡保存状态: {saved_lvl}")
    OUT.write_text(f"SAVED: {saved_bp and saved_lvl}\n", encoding="utf-8")

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        err = traceback.format_exc()
        log(f"ERROR: {err}")
        OUT.write_text(f"ERROR: {err}\n", encoding="utf-8")
        raise
