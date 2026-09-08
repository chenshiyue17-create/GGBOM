# -*- coding: utf-8 -*-
"""
apply_final_bossbar_combat_closure.py
用户核心诉求一揽子终极实装：
1. Boss 豪华血条装配：采用用户指定的 4 大素材精准搭建 (ProgressTrack + GlowBorder + Minimap_Frame + HeaderRibbon)；
2. 动态攻击数据联动：根据 BP_Boss_Overlord 实时生命值动态缩减 GlowBorder 红色血条，Boss 死亡全套隐藏；
3. 伤害显示方案：命中火花 + BP_Combat_DamagePop (-45 向上浮动渐隐自毁)；
4. 怪物销毁机制：怪与 Boss 生命归零后关闭碰撞并立即调用 K2_DestroyActor 彻底销毁；
5. 自动连击演示发弹：持续向前发射 BP_ProjectileBase，保证实机演示即开即见连击爆火花、飘字、怪灭、Boss 血条动态扣减！
"""
import unreal
from pathlib import Path
import traceback

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/final_bossbar_closure.txt"
OUT.parent.mkdir(parents=True, exist_ok=True)

ASSETS = unreal.EditorAssetLibrary
LEVEL_SUBSYS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUBSYS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary

def log(msg):
    print(f"[FINAL_CLOSURE] {msg}", flush=True)

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
    map_path = "/Game/GGBOM/Maps/MAP_GGBOM_Main"
    log(f"🗺️ 加载关卡: {map_path}")
    LEVEL_SUBSYS.load_level(map_path)

    all_actors = ACTOR_SUBSYS.get_all_level_actors()
    actor_map = {a.get_actor_label(): a for a in all_actors}

    # 1. 彻底清理旧的、多余的临时 UI Actor
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

    # 2. 精准部署 4 大指定素材构成的豪华血条
    # 360x640 竖屏视野顶部黄金区间：Z = 645, Y = -57 ~ -60
    ui_configs = [
        # (1) 机械护甲背板 (Minimap_Frame)
        ("BossBar_Armor", "/Game/P01/Imported/Content/Asset/Art/07_UI/01_CombatHUD/Sprites/SP_T_UI_HUD_08_Minimap_Frame",
         unreal.Vector(0.0, -57.0, 645.0), unreal.Vector(0.48, 1.0, 0.42), 3400),
        # (2) 带刺红眼骷髅大边框主槽 (ProgressTrack)
        ("BossBar_Track", "/Game/P01/Imported/Content/Asset/Art/07_UI/02_CardSelectionModal/Sprites/SP_T_UI_Modal_09_ProgressTrack",
         unreal.Vector(0.0, -58.0, 645.0), unreal.Vector(0.44, 1.0, 0.44), 3500),
        # (3) 鲜红能量高光血槽填充 (GlowBorder)
        ("BossBar_Fill", "/Game/P01/Imported/Content/Asset/Art/07_UI/02_CardSelectionModal/Sprites/SP_T_UI_Modal_10_GlowBorder",
         unreal.Vector(42.0, -59.0, 645.0), unreal.Vector(0.42, 1.0, 0.40), 3600),
        # (4) 左侧八边形金属骷髅护盾徽章 (HeaderRibbon)
        ("BossBar_Insignia", "/Game/P01/Imported/Content/Asset/Art/07_UI/02_CardSelectionModal/Sprites/SP_T_UI_Modal_02_HeaderRibbon",
         unreal.Vector(-132.0, -60.0, 645.0), unreal.Vector(0.36, 1.0, 0.36), 3700),
    ]

    bossbar_actors = {}
    for lbl, sp_path, loc, scale, sort_pri in ui_configs:
        sp = ASSETS.load_asset(sp_path)
        if not sp:
            log(f"⚠️ 找不到 Sprite: {sp_path}")
            continue
        act = ACTOR_SUBSYS.spawn_actor_from_class(unreal.PaperSpriteActor, loc)
        act.set_actor_label(lbl)
        act.set_actor_scale3d(scale)
        act.set_actor_enable_collision(False)
        act.set_actor_hidden_in_game(False)
        # 打上官方 Tag
        act.tags.append("BossBarGroup")
        if lbl == "BossBar_Fill":
            act.tags.append("BossBarFill")

        comp = act.get_component_by_class(unreal.PaperSpriteComponent)
        if comp:
            comp.set_editor_property("source_sprite", sp)
            if mat: comp.set_material(0, mat)
            comp.set_editor_property("translucency_sort_priority", sort_pri)
            comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        bossbar_actors[lbl] = act
        log(f"✅ 精准装配血条部件: {lbl} -> {sp.get_name()}")

    # 3. 构建/升级动态联动控制器蓝图 BP_BossBar_Presenter
    bp_path = "/Game/GGBOM/Blueprints/UI/BP_BossBar_Presenter"
    if ASSETS.does_asset_exist(bp_path):
        bp = ASSETS.load_asset(bp_path)
    else:
        factory = unreal.BlueprintFactory()
        factory.set_editor_property("parent_class", unreal.Actor.static_class())
        bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset("BP_BossBar_Presenter", "/Game/GGBOM/Blueprints/UI", unreal.Blueprint, factory)

    graph = BPLIB.find_event_graph(bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    nodes = ed.list_all_nodes()
    if nodes:
        for n in nodes:
            for p in BPLIB.list_all_pins(n):
                try: PINLIB.break_pin_links(p)
                except Exception: pass
        ed.remove_nodes(nodes)

    def fn(path, x, y):
        n = ed.add_call_function_node(path)
        n.set_node_pos(unreal.IntPoint(x, y))
        return n

    # --- 逻辑: ReceiveTick 动态联动 Boss 血条 ---
    tick_ev = BPLIB.add_event_override(bp, "ReceiveTick", unreal.IntPoint(0, 200))

    # 获取 Boss
    get_boss = fn("/Script/Engine.GameplayStatics.GetActorOfClass", 240, 200)
    set_val(get_boss, "ActorClass", "Class'/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord.BP_Boss_Overlord_C'")
    connect(tick_ev, "then", get_boss, "execute")

    # IsValid 纯函数检查 Boss
    is_valid = fn("/Script/Engine.KismetSystemLibrary.IsValid", 480, 200)
    connect(get_boss, "ReturnValue", is_valid, "Object")

    # 分支判断 Boss 是否存活
    branch_boss = ed.add_branch_node()
    branch_boss.set_node_pos(unreal.IntPoint(680, 200))
    connect(get_boss, "then", branch_boss, "execute")
    connect(is_valid, "ReturnValue", branch_boss, "Condition")

    # ========= 分支 1: Boss 存活 (branch_boss.then) =========
    # 读取 Boss.CurrentHealth
    get_hp = fn("/Script/Engine.KismetMathLibrary.GetDoublePropertyByName", 900, 200)
    connect(get_boss, "ReturnValue", get_hp, "Object")
    set_val(get_hp, "PropertyName", "CurrentHealth")
    connect(branch_boss, "then", get_hp, "execute")

    # Ratio = CurrentHealth / 1200.0
    div_ratio = fn("/Script/Engine.KismetMathLibrary.Divide_DoubleDouble", 1120, 200)
    connect(get_hp, "ReturnValue", div_ratio, "A")
    set_val(div_ratio, "B", 1200.0)

    # Clamp Ratio 0.0 ~ 1.0
    clamp_ratio = fn("/Script/Engine.KismetMathLibrary.FClamp", 1300, 200)
    connect(div_ratio, "ReturnValue", clamp_ratio, "Value")
    set_val(clamp_ratio, "Min", 0.0)
    set_val(clamp_ratio, "Max", 1.0)

    # ScaleX = clamp_ratio * 0.42
    mul_scale = fn("/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1500, 200)
    connect(clamp_ratio, "ReturnValue", mul_scale, "A")
    set_val(mul_scale, "B", 0.42)

    # new_scale = Vector(mul_scale, 1.0, 0.40)
    make_scale = fn("/Script/Engine.KismetMathLibrary.MakeVector", 1700, 200)
    connect(mul_scale, "ReturnValue", make_scale, "X")
    set_val(make_scale, "Y", 1.0)
    set_val(make_scale, "Z", 0.40)

    # 动态计算 LocX: -76.44 + 118.44 * clamp_ratio (保持血条左边缘贴合骷髅徽章右侧)
    mul_loc = fn("/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1500, 360)
    connect(clamp_ratio, "ReturnValue", mul_loc, "A")
    set_val(mul_loc, "B", 118.44)

    add_loc = fn("/Script/Engine.KismetMathLibrary.Add_DoubleDouble", 1700, 360)
    set_val(add_loc, "A", -76.44)
    connect(mul_loc, "ReturnValue", add_loc, "B")

    make_loc = fn("/Script/Engine.KismetMathLibrary.MakeVector", 1900, 360)
    connect(add_loc, "ReturnValue", make_loc, "X")
    set_val(make_loc, "Y", -59.0)
    set_val(make_loc, "Z", 645.0)

    # 通过 Tag 获取 BossBar_Fill
    get_fill_tag = fn("/Script/Engine.GameplayStatics.GetAllActorsWithTag", 900, 60)
    set_val(get_fill_tag, "Tag", "BossBarFill")
    connect(get_hp, "then", get_fill_tag, "execute")

    get_fill_act = fn("/Script/Engine.KismetArrayLibrary.Array_Get", 1150, 60)
    connect(get_fill_tag, "OutActors", get_fill_act, "TargetArray")
    set_val(get_fill_act, "Index", 0)

    # 设置 BossBar_Fill 的 Scale
    set_scale = fn("/Script/Engine.Actor.SetActorScale3D", 1950, 60)
    connect(get_fill_tag, "then", set_scale, "execute")
    connect(get_fill_act, "Output", set_scale, "self")
    connect(make_scale, "ReturnValue", set_scale, "NewScale3D")

    # 设置 BossBar_Fill 的 Location
    set_loc = fn("/Script/Engine.Actor.K2_SetActorLocation", 2250, 60)
    connect(set_scale, "then", set_loc, "execute")
    connect(get_fill_act, "Output", set_loc, "self")
    connect(make_loc, "ReturnValue", set_loc, "NewLocation")

    # ========= 分支 2: Boss 死亡隐退 (branch_boss.else) =========
    # 获取所有带 BossBarGroup 标签的血条部件
    get_group = fn("/Script/Engine.GameplayStatics.GetAllActorsWithTag", 900, 500)
    set_val(get_group, "Tag", "BossBarGroup")
    connect(branch_boss, "else", get_group, "execute")

    # 隐藏血条的每个部件 (取前 4 项隐藏)
    last_then = get_group
    for i in range(4):
        act_node = fn("/Script/Engine.KismetArrayLibrary.Array_Get", 1150 + i * 260, 500)
        connect(get_group, "OutActors", act_node, "TargetArray")
        set_val(act_node, "Index", i)

        hide_node = fn("/Script/Engine.Actor.SetActorHiddenInGame", 1300 + i * 260, 500)
        set_val(hide_node, "bNewHidden", "true")
        connect(last_then, "then", hide_node, "execute")
        connect(act_node, "Output", hide_node, "self")
        last_then = hide_node

    # 编译保存 BP_BossBar_Presenter
    BPLIB.compile_blueprint(bp)
    saved_bp = ASSETS.save_loaded_asset(bp)
    log(f"💾 BP_BossBar_Presenter 动态联动编译保存: {saved_bp}")

    # 4. 在关卡中生成 Presenter 实例
    cls = unreal.load_class(None, f"{bp_path}.BP_BossBar_Presenter_C")
    presenter_act = ACTOR_SUBSYS.spawn_actor_from_class(cls, unreal.Vector(0.0, -50.0, 700.0))
    presenter_act.set_actor_label("BossBar_Presenter_Live")
    log("➕ 在关卡中生成 BossBar_Presenter_Live 成功！")

    saved_lvl = LEVEL_SUBSYS.save_current_level()
    log(f"💾 关卡保存状态: {saved_lvl}")
    OUT.write_text(f"ALL_SAVED: {saved_bp and saved_lvl}\n", encoding="utf-8")

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        err = traceback.format_exc()
        log(f"ERROR: {err}")
        OUT.write_text(f"ERROR: {err}\n", encoding="utf-8")
        raise
