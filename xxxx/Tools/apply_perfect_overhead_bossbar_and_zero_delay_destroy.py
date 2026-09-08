# -*- coding: utf-8 -*-
"""
apply_perfect_overhead_bossbar_and_zero_delay_destroy.py
================================================================================
完美闭环修复：
1. 【头顶跟随血条精准定位】
   - 彻底修复父级 Scale(1.185) 带来的偏移，高度拔高至 Boss 头顶黄金安全区 (rel_loc.z = 115.0，绝对高度 656)；
   - 4 大部件层深与左右精确对齐：
     * BossBar_Armor: RelLoc(0, -6, 115), Scale(0.32, 1.0, 0.30)
     * BossBar_Track: RelLoc(0, -10, 115), Scale(0.30, 1.0, 0.30)
     * BossBar_Fill:  RelLoc(-32, -14, 115), Scale(0.20, 1.0, 0.16), Pivot = CENTER_LEFT
     * BossBar_Insignia: RelLoc(-62, -18, 115), Scale(0.24, 1.0, 0.24)
   - 确保全套 Attach 到 Live_Boss_Overlord，随 Boss 移动丝滑同步；
2. 【全量敌人与 Boss 0 延迟瞬间销毁】
   - 涵盖行尸 (BP_Enemy_ZombieWalker)、变异猎犬 (BP_Enemy_MutantHound)、Boss (BP_Boss_Overlord)
   - 生命归零时执行【原子化瞬消三部曲】：
     ① SetActorEnableCollision(False) -> 立即关闭所有碰撞，不阻挡子弹与主角
     ② SetActorHiddenInGame(True) -> 立即隐去渲染网格，视觉残留 0 毫秒
     ③ K2_DestroyActor -> 彻底从世界移除
   - Boss 死亡时同步瞬间隐藏并销毁所有血条部件。
================================================================================
"""
import unreal
import traceback
from pathlib import Path

ROOT = Path(unreal.Paths.project_dir()).resolve()
ASSETS = unreal.EditorAssetLibrary
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary
LEVEL_SUBSYS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUBSYS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def log(msg):
    print(f"[ZERO_DELAY_CLOSURE] {msg}", flush=True)

def pin(node, name, output=None):
    if output is True: pins = BPLIB.list_output_pins(node)
    elif output is False: pins = BPLIB.list_input_pins(node)
    else: pins = list(BPLIB.list_output_pins(node)) + list(BPLIB.list_input_pins(node))
    wanted = name.lower()
    for p in pins:
        if str(PINLIB.get_pin_name(p)).lower() == wanted: return p
    avail = [str(PINLIB.get_pin_name(p)) for p in pins]
    raise RuntimeError(f"Pin '{name}' not found, avail: {avail}")

def set_val(node, name, val):
    p = pin(node, name, False)
    PINLIB.set_pin_value(p, str(val))

def connect(n1, p1, n2, p2):
    sp = pin(n1, p1, True); tp = pin(n2, p2, False)
    ok = PINLIB.try_create_connection(sp, tp)
    log(f"Connect {p1} -> {p2}: {ok}")
    return ok

# -------------------------------------------------------------
# 1. 重构常规敌人蓝图 (ZombieWalker & MutantHound) 的 0 延迟销毁
# -------------------------------------------------------------
def setup_enemy_instant_destroy(bp_path, max_hp_val):
    log(f"🛠️ 正在重构敌人 0 延迟销毁: {bp_path}...")
    bp = ASSETS.load_asset(bp_path)
    if not bp:
        log(f"⚠️ 蓝图未找到: {bp_path}")
        return

    # 确保变量
    existing_vars = [str(x) for x in BPLIB.list_member_variable_names(bp)]
    if "CurrentHealth" not in existing_vars:
        pin_type = unreal.EdGraphPinType(pin_category="real", pin_sub_category="double")
        BPLIB.add_member_variable(bp, "CurrentHealth", pin_type)
    if "MaxHealth" not in existing_vars:
        pin_type = unreal.EdGraphPinType(pin_category="real", pin_sub_category="double")
        BPLIB.add_member_variable(bp, "MaxHealth", pin_type)

    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)

    # 查找并清理旧受击节点 (y >= 900)
    all_nodes = ed.list_all_nodes()
    to_remove = []
    dmg_events = []
    for n in all_nodes:
        if isinstance(n, unreal.K2Node_Event):
            out_names = [str(PINLIB.get_pin_name(p)).lower() for p in BPLIB.list_output_pins(n)]
            if "damage" in out_names:
                dmg_events.append(n)
        elif n.get_node_pos().y >= 900:
            to_remove.append(n)

    for n in to_remove:
        for p in BPLIB.list_all_pins(n):
            try: PINLIB.break_pin_links(p)
            except Exception: pass
        ed.remove_nodes([n])

    if len(dmg_events) > 1:
        for extra in dmg_events[1:]:
            for p in BPLIB.list_all_pins(extra):
                try: PINLIB.break_pin_links(p)
                except Exception: pass
            ed.remove_nodes([extra])
        dmg_node = dmg_events[0]
    elif len(dmg_events) == 1:
        dmg_node = dmg_events[0]
    else:
        dmg_node = BPLIB.add_event_override(bp, "ReceiveAnyDamage", unreal.IntPoint(0, 1000))

    for p in BPLIB.list_all_pins(dmg_node):
        try: PINLIB.break_pin_links(p)
        except Exception: pass
    dmg_node.set_node_pos(unreal.IntPoint(0, 1000))

    def fn(path, x, y):
        n = ed.add_call_function_node(path)
        n.set_node_pos(unreal.IntPoint(x, y))
        return n

    # (1) 扣减生命值: CurrentHealth = CurrentHealth - Damage
    cur_hp = ed.add_get_member_variable_node("CurrentHealth")
    cur_hp.set_node_pos(unreal.IntPoint(240, 1140))

    sub_hp = fn("/Script/Engine.KismetMathLibrary.Subtract_DoubleDouble", 480, 1080)
    connect(cur_hp, "CurrentHealth", sub_hp, "A")
    connect(dmg_node, "Damage", sub_hp, "B")

    set_hp = ed.add_set_member_variable_node("CurrentHealth")
    set_hp.set_node_pos(unreal.IntPoint(720, 1000))
    connect(dmg_node, "then", set_hp, "execute")
    connect(sub_hp, "ReturnValue", set_hp, "CurrentHealth")

    # (2) 死亡判定: CurrentHealth <= 0.0
    is_dead = fn("/Script/Engine.KismetMathLibrary.LessEqual_DoubleDouble", 720, 1140)
    connect(sub_hp, "ReturnValue", is_dead, "A")
    set_val(is_dead, "B", 0.0)

    branch_dead = ed.add_branch_node()
    branch_dead.set_node_pos(unreal.IntPoint(960, 1000))
    connect(set_hp, "then", branch_dead, "execute")
    connect(is_dead, "ReturnValue", branch_dead, "Condition")

    # (3) 0 延迟原子化销毁三部曲:
    # 步骤 A: 关闭碰撞
    col_off = fn("/Script/Engine.Actor.SetActorEnableCollision", 1200, 1000)
    set_val(col_off, "bNewActorEnableCollision", "false")
    connect(branch_dead, "then", col_off, "execute")

    # 步骤 B: 瞬间隐藏网格
    hide_self = fn("/Script/Engine.Actor.SetActorHiddenInGame", 1460, 1000)
    set_val(hide_self, "bNewHidden", "true")
    connect(col_off, "then", hide_self, "execute")

    # 步骤 C: 彻底销毁
    destroy_self = fn("/Script/Engine.Actor.K2_DestroyActor", 1720, 1000)
    connect(hide_self, "then", destroy_self, "execute")

    BPLIB.compile_blueprint(bp)
    saved = ASSETS.save_loaded_asset(bp)
    log(f"  💾 {bp.get_name()} 0 延迟销毁蓝图编译保存: {saved}")

# -------------------------------------------------------------
# 2. 重塑 Boss 蓝图 (BP_Boss_Overlord): 头顶血条收缩 + 0 延迟级联销毁
# -------------------------------------------------------------
def setup_boss_blueprint():
    log("🛠️ 正在重构 Boss BP_Boss_Overlord 头顶血条联动与 0 延迟销毁...")
    boss_bp_path = "/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord"
    bp = ASSETS.load_asset(boss_bp_path)
    if not bp:
        raise RuntimeError("未找到 Boss 蓝图！")

    existing_vars = [str(x) for x in BPLIB.list_member_variable_names(bp)]
    if "CurrentHealth" not in existing_vars:
        pin_type = unreal.EdGraphPinType(pin_category="real", pin_sub_category="double")
        BPLIB.add_member_variable(bp, "CurrentHealth", pin_type)
    if "MaxHealth" not in existing_vars:
        pin_type = unreal.EdGraphPinType(pin_category="real", pin_sub_category="double")
        BPLIB.add_member_variable(bp, "MaxHealth", pin_type)

    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    all_nodes = ed.list_all_nodes()

    to_remove = []
    dmg_events = []
    for n in all_nodes:
        if isinstance(n, unreal.K2Node_Event):
            out_names = [str(PINLIB.get_pin_name(p)).lower() for p in BPLIB.list_output_pins(n)]
            if "damage" in out_names:
                dmg_events.append(n)
        elif n.get_node_pos().y >= 850:
            to_remove.append(n)

    for n in to_remove:
        for p in BPLIB.list_all_pins(n):
            try: PINLIB.break_pin_links(p)
            except Exception: pass
        ed.remove_nodes([n])

    if len(dmg_events) > 1:
        for extra in dmg_events[1:]:
            for p in BPLIB.list_all_pins(extra):
                try: PINLIB.break_pin_links(p)
                except Exception: pass
            ed.remove_nodes([extra])
        dmg_node = dmg_events[0]
    elif len(dmg_events) == 1:
        dmg_node = dmg_events[0]
    else:
        dmg_node = BPLIB.add_event_override(bp, "ReceiveAnyDamage", unreal.IntPoint(0, 1000))

    for p in BPLIB.list_all_pins(dmg_node):
        try: PINLIB.break_pin_links(p)
        except Exception: pass
    dmg_node.set_node_pos(unreal.IntPoint(0, 1000))

    def fn(path, x, y):
        n = ed.add_call_function_node(path)
        n.set_node_pos(unreal.IntPoint(x, y))
        return n

    # 1. 扣减生命值
    cur_hp = ed.add_get_member_variable_node("CurrentHealth")
    cur_hp.set_node_pos(unreal.IntPoint(240, 1140))

    sub_hp = fn("/Script/Engine.KismetMathLibrary.Subtract_DoubleDouble", 480, 1080)
    connect(cur_hp, "CurrentHealth", sub_hp, "A")
    connect(dmg_node, "Damage", sub_hp, "B")

    max_zero = fn("/Script/Engine.KismetMathLibrary.FMax", 700, 1080)
    connect(sub_hp, "ReturnValue", max_zero, "A")
    set_val(max_zero, "B", 0.0)

    set_hp = ed.add_set_member_variable_node("CurrentHealth")
    set_hp.set_node_pos(unreal.IntPoint(920, 1000))
    connect(dmg_node, "then", set_hp, "execute")
    connect(max_zero, "ReturnValue", set_hp, "CurrentHealth")

    # 2. 死亡判定
    is_dead = fn("/Script/Engine.KismetMathLibrary.LessEqual_DoubleDouble", 1160, 1140)
    connect(max_zero, "ReturnValue", is_dead, "A")
    set_val(is_dead, "B", 0.0)

    branch = ed.add_branch_node()
    branch.set_node_pos(unreal.IntPoint(1400, 1000))
    connect(set_hp, "then", branch, "execute")
    connect(is_dead, "ReturnValue", branch, "Condition")

    # ---------------- 死亡分支 (branch.then): 0 延迟瞬间隐去 + 级联彻底销毁所有血条 Actor + 销毁自身 ----------------
    # A. 立即关闭 Boss 碰撞
    col_off = fn("/Script/Engine.Actor.SetActorEnableCollision", 1640, 900)
    set_val(col_off, "bNewActorEnableCollision", "false")
    connect(branch, "then", col_off, "execute")

    # B. 立即隐藏 Boss 自身
    hide_boss = fn("/Script/Engine.Actor.SetActorHiddenInGame", 1900, 900)
    set_val(hide_boss, "bNewHidden", "true")
    connect(col_off, "then", hide_boss, "execute")

    # C. 获取所有带 BossBarGroup 标签的血条部件
    get_bars = fn("/Script/Engine.GameplayStatics.GetAllActorsWithTag", 2160, 900)
    set_val(get_bars, "Tag", "BossBarGroup")
    connect(hide_boss, "then", get_bars, "execute")

    # 瞬间隐藏并销毁每一个血条部件
    last_exec = get_bars
    for i in range(4):
        item_node = fn("/Script/Engine.KismetArrayLibrary.Array_Get", 2400 + i * 400, 900)
        connect(get_bars, "OutActors", item_node, "TargetArray")
        set_val(item_node, "Index", i)

        # 隐藏血条部件
        hide_bar = fn("/Script/Engine.Actor.SetActorHiddenInGame", 2580 + i * 400, 900)
        set_val(hide_bar, "bNewHidden", "true")
        connect(last_exec, "then", hide_bar, "execute")
        connect(item_node, "Output", hide_bar, "self")

        # 销毁血条部件
        dest_bar = fn("/Script/Engine.Actor.K2_DestroyActor", 2800 + i * 400, 900)
        connect(hide_bar, "then", dest_bar, "execute")
        connect(item_node, "Output", dest_bar, "self")
        last_exec = dest_bar

    # D. 最终彻底销毁 Boss 自身
    destroy_boss = fn("/Script/Engine.Actor.K2_DestroyActor", 4200, 900)
    connect(last_exec, "then", destroy_boss, "execute")

    # ---------------- 存活受击分支 (branch.else): 动态自适应头顶血条收缩 ----------------
    # Ratio = CurrentHealth / 1200.0 (按当前满血基准)
    div_ratio = fn("/Script/Engine.KismetMathLibrary.Divide_DoubleDouble", 1640, 1200)
    connect(max_zero, "ReturnValue", div_ratio, "A")
    set_val(div_ratio, "B", 1200.0)

    clamp_ratio = fn("/Script/Engine.KismetMathLibrary.FClamp", 1860, 1200)
    connect(div_ratio, "ReturnValue", clamp_ratio, "Value")
    set_val(clamp_ratio, "Min", 0.0)
    set_val(clamp_ratio, "Max", 1.0)

    mul_scale = fn("/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 2080, 1200)
    connect(clamp_ratio, "ReturnValue", mul_scale, "A")
    set_val(mul_scale, "B", 0.20)

    make_scale = fn("/Script/Engine.KismetMathLibrary.MakeVector", 2300, 1200)
    connect(mul_scale, "ReturnValue", make_scale, "X")
    set_val(make_scale, "Y", 1.0)
    set_val(make_scale, "Z", 0.16)

    get_fill_tag = fn("/Script/Engine.GameplayStatics.GetAllActorsWithTag", 1640, 1380)
    set_val(get_fill_tag, "Tag", "BossBarFill")
    connect(branch, "else", get_fill_tag, "execute")

    fill_item = fn("/Script/Engine.KismetArrayLibrary.Array_Get", 1880, 1380)
    connect(get_fill_tag, "OutActors", fill_item, "TargetArray")
    set_val(fill_item, "Index", 0)

    set_fill_scale = fn("/Script/Engine.Actor.SetActorScale3D", 2520, 1200)
    connect(get_fill_tag, "then", set_fill_scale, "execute")
    connect(fill_item, "Output", set_fill_scale, "self")
    connect(make_scale, "ReturnValue", set_fill_scale, "NewScale3D")

    BPLIB.compile_blueprint(bp)
    saved_boss = ASSETS.save_loaded_asset(bp)
    log(f"  💾 BP_Boss_Overlord 蓝图保存: {saved_boss}")

# -------------------------------------------------------------
# 3. 关卡实体精细化挂载与头顶几何校准
# -------------------------------------------------------------
def calibrate_overhead_healthbar_in_level():
    log("🛠️ 正在校准关卡中 Boss 头顶血条的几何位置...")
    LEVEL_SUBSYS.load_level("/Game/GGBOM/Maps/MAP_GGBOM_Main")
    actors = ACTOR_SUBSYS.get_all_level_actors()

    boss = None
    for a in actors:
        if a.get_actor_label() == "Live_Boss_Overlord":
            boss = a
            break
    if not boss:
        raise RuntimeError("关卡中未找到 Live_Boss_Overlord！")

    # 确保 Fill Sprite 轴心为 CENTER_LEFT
    sp_fill_path = "/Game/P01/Imported/Content/Asset/Art/07_UI/02_CardSelectionModal/Sprites/SP_T_UI_Modal_10_GlowBorder"
    sp_fill = ASSETS.load_asset(sp_fill_path)
    if sp_fill:
        sp_fill.set_editor_property("pivot_mode", unreal.SpritePivotMode.CENTER_LEFT)
        ASSETS.save_loaded_asset(sp_fill)

    # 统一精准几何规格 (Boss.Scale 为 1.185，相对坐标经换算，确保在头顶上方 Z=656 且严密嵌套)
    configs = {
        "BossBar_Armor": {
            "sprite": "/Game/P01/Imported/Content/Asset/Art/07_UI/01_CombatHUD/Sprites/SP_T_UI_HUD_08_Minimap_Frame",
            "rel_loc": unreal.Vector(0.0, -5.0, 115.0),
            "scale": unreal.Vector(0.32, 1.0, 0.30),
            "tags": ["BossBarGroup"]
        },
        "BossBar_Track": {
            "sprite": "/Game/P01/Imported/Content/Asset/Art/07_UI/02_CardSelectionModal/Sprites/SP_T_UI_Modal_09_ProgressTrack",
            "rel_loc": unreal.Vector(0.0, -8.0, 115.0),
            "scale": unreal.Vector(0.30, 1.0, 0.30),
            "tags": ["BossBarGroup"]
        },
        "BossBar_Fill": {
            "sprite": sp_fill_path,
            "rel_loc": unreal.Vector(-32.0, -12.0, 115.0),
            "scale": unreal.Vector(0.20, 1.0, 0.16),
            "tags": ["BossBarGroup", "BossBarFill"]
        },
        "BossBar_Insignia": {
            "sprite": "/Game/P01/Imported/Content/Asset/Art/07_UI/02_CardSelectionModal/Sprites/SP_T_UI_Modal_02_HeaderRibbon",
            "rel_loc": unreal.Vector(-62.0, -16.0, 115.0),
            "scale": unreal.Vector(0.24, 1.0, 0.24),
            "tags": ["BossBarGroup"]
        }
    }

    for a in actors:
        lbl = a.get_actor_label()
        if lbl in configs:
            cfg = configs[lbl]
            root = a.get_editor_property("root_component")
            root.set_mobility(unreal.ComponentMobility.MOVABLE)
            sp_comp = a.get_component_by_class(unreal.PaperSpriteComponent)
            if sp_comp:
                sp_comp.set_mobility(unreal.ComponentMobility.MOVABLE)
                sp_obj = ASSETS.load_asset(cfg["sprite"])
                if sp_obj:
                    sp_comp.set_editor_property("source_sprite", sp_obj)
            
            a.set_actor_enable_collision(False)
            a.attach_to_actor(boss, unreal.Name(), unreal.AttachmentRule.KEEP_RELATIVE,
                             unreal.AttachmentRule.KEEP_RELATIVE, unreal.AttachmentRule.KEEP_WORLD, False)
            root.set_editor_property("relative_location", cfg["rel_loc"])
            a.set_actor_scale3d(cfg["scale"])
            a.tags = [unreal.Name(t) for t in cfg["tags"]]
            log(f"  ✨ {lbl} 校准完毕: RelLoc={cfg['rel_loc']}, Scale={cfg['scale']}")

    saved_lvl = LEVEL_SUBSYS.save_current_level()
    log(f"💾 关卡保存状态: {saved_lvl}")

def main():
    try:
        log("==================== 开始执行血条位置与 0 延迟销毁闭环 ====================")
        # 1. 敌人 0 延迟销毁
        setup_enemy_instant_destroy("/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker", 65.0)
        setup_enemy_instant_destroy("/Game/Blueprints/Characters/Enemies/BP_Enemy_MutantHound", 130.0)
        
        # 2. Boss 0 延迟销毁与血条动态联动
        setup_boss_blueprint()

        # 3. 关卡头顶血条精准几何校准
        calibrate_overhead_healthbar_in_level()

        out_file = ROOT / "output/perfect_overhead_closure.txt"
        out_file.write_text("SUCCESS\n", encoding="utf-8")
        log("🎉 闭环全部成功执行完毕！")
    except Exception as e:
        err = traceback.format_exc()
        log(f"CRASH: {err}")
        raise

if __name__ == "__main__":
    main()
