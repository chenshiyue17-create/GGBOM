# -*- coding: utf-8 -*-
"""
setup_boss_event_linkage.py
1. 关卡清理与 4 大指定素材精准布局：
   - T_UI_HUD_08_Minimap_Frame (BossBar_Armor, 机械装甲背板)
   - T_UI_Modal_09_ProgressTrack (BossBar_Track, 带刺红眼骷髅大边框主底槽)
   - T_UI_Modal_10_GlowBorder (BossBar_Fill, 鲜红高光能量血槽填充)
   - T_UI_Modal_02_HeaderRibbon (BossBar_Insignia, 八边形金属骷髅徽章)
2. 事件驱动：将 Boss 受击扣血与血条直接挂钩：
   - Boss 每次受到伤害，立即动态更新 BossBar_Fill 的缩放与位置；
   - Boss 死亡时，自动隐藏全部 BossBarGroup 部件并调用 K2_DestroyActor 自毁！
"""
import unreal
from pathlib import Path
import traceback

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/setup_boss_event_linkage.txt"
OUT.parent.mkdir(parents=True, exist_ok=True)

ASSETS = unreal.EditorAssetLibrary
LEVEL_SUBSYS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUBSYS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary

def log(msg):
    print(f"[BOSS_EVENT_LINKAGE] {msg}", flush=True)

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

def run():
    # 步骤 1: 关卡布局
    map_path = "/Game/GGBOM/Maps/MAP_GGBOM_Main"
    log(f"🗺️ 加载关卡: {map_path}")
    LEVEL_SUBSYS.load_level(map_path)

    all_actors = ACTOR_SUBSYS.get_all_level_actors()
    actor_map = {a.get_actor_label(): a for a in all_actors}

    legacy_to_destroy = [
        "UI_Boss_Ribbon", "UI_BossBar_Track", "UI_BossBar_Glow", "UI_BossBar_Fill",
        "UI_Boss_Frame", "UI_Boss_SkullIcon", "UI_BossBar_Bg", "UI_Btn_Pause",
        "BossBar_Presenter_Live", "BossBar_Armor", "BossBar_Track", "BossBar_Fill", "BossBar_Insignia"
    ]
    for lbl in legacy_to_destroy:
        if lbl in actor_map:
            ACTOR_SUBSYS.destroy_actor(actor_map[lbl])
            log(f"🗑️ 销毁旧 UI Actor: {lbl}")

    mat = ASSETS.load_asset("/Paper2D/TranslucentUnlitSpriteMaterial")

    ui_configs = [
        ("BossBar_Armor", "/Game/P01/Imported/Content/Asset/Art/07_UI/01_CombatHUD/Sprites/SP_T_UI_HUD_08_Minimap_Frame",
         unreal.Vector(0.0, -57.0, 645.0), unreal.Vector(0.48, 1.0, 0.42), 3400),
        ("BossBar_Track", "/Game/P01/Imported/Content/Asset/Art/07_UI/02_CardSelectionModal/Sprites/SP_T_UI_Modal_09_ProgressTrack",
         unreal.Vector(0.0, -58.0, 645.0), unreal.Vector(0.44, 1.0, 0.44), 3500),
        ("BossBar_Fill", "/Game/P01/Imported/Content/Asset/Art/07_UI/02_CardSelectionModal/Sprites/SP_T_UI_Modal_10_GlowBorder",
         unreal.Vector(42.0, -59.0, 645.0), unreal.Vector(0.42, 1.0, 0.40), 3600),
        ("BossBar_Insignia", "/Game/P01/Imported/Content/Asset/Art/07_UI/02_CardSelectionModal/Sprites/SP_T_UI_Modal_02_HeaderRibbon",
         unreal.Vector(-132.0, -60.0, 645.0), unreal.Vector(0.36, 1.0, 0.36), 3700),
    ]

    for lbl, sp_path, loc, scale, sort_pri in ui_configs:
        sp = ASSETS.load_asset(sp_path)
        if not sp: continue
        act = ACTOR_SUBSYS.spawn_actor_from_class(unreal.PaperSpriteActor, loc)
        act.set_actor_label(lbl)
        act.set_actor_scale3d(scale)
        act.set_actor_enable_collision(False)
        act.set_actor_hidden_in_game(False)
        act.tags.append("BossBarGroup")
        if lbl == "BossBar_Fill":
            act.tags.append("BossBarFill")

        comp = act.get_component_by_class(unreal.PaperSpriteComponent)
        if comp:
            comp.set_editor_property("source_sprite", sp)
            if mat: comp.set_material(0, mat)
            comp.set_editor_property("translucency_sort_priority", sort_pri)
            comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        log(f"✅ 装配血条部件: {lbl}")

    saved_lvl = LEVEL_SUBSYS.save_current_level()
    log(f"💾 关卡血条布局保存: {saved_lvl}")

    # 步骤 2: 在 BP_Boss_Overlord 中植入受击扣血联动与死亡隐退逻辑
    bp_path = "/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord"
    bp = ASSETS.load_asset(bp_path)
    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    log(f"Opened {bp_path}")

    # 清理所有现有 Damage 节点
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

    if to_remove:
        for n in to_remove:
            for p in BPLIB.list_all_pins(n):
                try: PINLIB.break_pin_links(p)
                except Exception: pass
        ed.remove_nodes(to_remove)

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

    # 1. 读取 CurrentHealth 并扣除 Damage
    cur_hp = ed.add_get_member_variable_node("CurrentHealth")
    cur_hp.set_node_pos(unreal.IntPoint(240, 1140))

    sub_hp = fn("/Script/Engine.KismetMathLibrary.Subtract_DoubleDouble", 460, 1080)
    connect(cur_hp, "CurrentHealth", sub_hp, "A")
    connect(dmg_node, "Damage", sub_hp, "B")

    set_hp = ed.add_set_member_variable_node("CurrentHealth")
    set_hp.set_node_pos(unreal.IntPoint(700, 1000))
    connect(dmg_node, "then", set_hp, "execute")
    connect(sub_hp, "ReturnValue", set_hp, "CurrentHealth")

    # 2. 死亡判定
    is_dead = fn("/Script/Engine.KismetMathLibrary.LessEqual_DoubleDouble", 700, 1160)
    connect(sub_hp, "ReturnValue", is_dead, "A")
    set_val(is_dead, "B", "0.0")

    branch = ed.add_branch_node()
    branch.set_node_pos(unreal.IntPoint(940, 1000))
    connect(set_hp, "then", branch, "execute")
    connect(is_dead, "ReturnValue", branch, "Condition")

    # 3. 死亡分支 (branch.then): 隐藏血条并销毁自身
    get_group = fn("/Script/Engine.GameplayStatics.GetAllActorsWithTag", 1160, 900)
    set_val(get_group, "Tag", "BossBarGroup")
    connect(branch, "then", get_group, "execute")

    last_hide = get_group
    for i in range(4):
        act_get = fn("/Script/Engine.KismetArrayLibrary.Array_Get", 1400 + i * 280, 900)
        connect(get_group, "OutActors", act_get, "TargetArray")
        set_val(act_get, "Index", i)

        hide_node = fn("/Script/Engine.Actor.SetActorHiddenInGame", 1550 + i * 280, 900)
        set_val(hide_node, "bNewHidden", "true")
        connect(last_hide, "then", hide_node, "execute")
        connect(act_get, "Item", hide_node, "self")
        last_hide = hide_node

    destroy_self = fn("/Script/Engine.Actor.K2_DestroyActor", 2700, 900)
    connect(last_hide, "then", destroy_self, "execute")

    # 4. 存活受击分支 (branch.else): 动态联动血条缩放与位置！
    # Ratio = Clamp(sub_hp / 1200.0, 0.0, 1.0)
    div_ratio = fn("/Script/Engine.KismetMathLibrary.Divide_DoubleDouble", 1160, 1140)
    connect(sub_hp, "ReturnValue", div_ratio, "A")
    set_val(div_ratio, "B", 1200.0)

    clamp_ratio = fn("/Script/Engine.KismetMathLibrary.FClamp", 1360, 1140)
    connect(div_ratio, "ReturnValue", clamp_ratio, "Value")
    set_val(clamp_ratio, "Min", 0.0)
    set_val(clamp_ratio, "Max", 1.0)

    # ScaleX = clamp_ratio * 0.42
    mul_scale = fn("/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1560, 1140)
    connect(clamp_ratio, "ReturnValue", mul_scale, "A")
    set_val(mul_scale, "B", 0.42)

    make_scale = fn("/Script/Engine.KismetMathLibrary.MakeVector", 1760, 1140)
    connect(mul_scale, "ReturnValue", make_scale, "X")
    set_val(make_scale, "Y", 1.0)
    set_val(make_scale, "Z", 0.40)

    # LocX = -76.44 + 118.44 * clamp_ratio
    mul_loc = fn("/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1560, 1300)
    connect(clamp_ratio, "ReturnValue", mul_loc, "A")
    set_val(mul_loc, "B", 118.44)

    add_loc = fn("/Script/Engine.KismetMathLibrary.Add_DoubleDouble", 1760, 1300)
    set_val(add_loc, "A", -76.44)
    connect(mul_loc, "ReturnValue", add_loc, "B")

    make_loc = fn("/Script/Engine.KismetMathLibrary.MakeVector", 1960, 1300)
    connect(add_loc, "ReturnValue", make_loc, "X")
    set_val(make_loc, "Y", -59.0)
    set_val(make_loc, "Z", 645.0)

    # 获取 BossBarFill
    get_fill = fn("/Script/Engine.GameplayStatics.GetAllActorsWithTag", 1160, 1300)
    set_val(get_fill, "Tag", "BossBarFill")
    connect(branch, "else", get_fill, "execute")

    fill_act = fn("/Script/Engine.KismetArrayLibrary.Array_Get", 1360, 1300)
    connect(get_fill, "OutActors", fill_act, "TargetArray")
    set_val(fill_act, "Index", 0)

    set_scale = fn("/Script/Engine.Actor.SetActorScale3D", 2160, 1140)
    connect(get_fill, "then", set_scale, "execute")
    connect(fill_act, "Item", set_scale, "self")
    connect(make_scale, "ReturnValue", set_scale, "NewScale3D")

    set_loc = fn("/Script/Engine.Actor.K2_SetActorLocation", 2420, 1140)
    connect(set_scale, "then", set_loc, "execute")
    connect(fill_act, "Item", set_loc, "self")
    connect(make_loc, "ReturnValue", set_loc, "NewLocation")

    log("Compiling BP_Boss_Overlord...")
    BPLIB.compile_blueprint(bp)
    saved_boss = ASSETS.save_loaded_asset(bp)
    log(f"💾 BP_Boss_Overlord 编译保存: {saved_boss}")

    OUT.write_text(f"ALL_OK: {saved_lvl and saved_boss}\n", encoding="utf-8")

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        err = traceback.format_exc()
        log(f"ERROR: {err}")
        OUT.write_text(f"ERROR: {err}\n", encoding="utf-8")
        raise
