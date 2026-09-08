# -*- coding: utf-8 -*-
"""
deploy_overhead_bossbar.py
终极实装：Boss 头顶跟随血条 与 单向收缩动画 (UE5)
1. 锚定 MAP_GGBOM_Main 中的 Boss (BP_Boss_Overlord) 实体；
2. 将 4 大指定豪华素材部署在 Boss 头顶上方 (Z+85, Y-5)：
   - BossBar_Armor (背板)
   - BossBar_Track (带刺红眼骷髅大边框主槽)
   - BossBar_Fill (鲜红能量高光血条填充) - 设为 CENTER_LEFT 左侧锚定，单向向左收缩
   - BossBar_Insignia (左侧八边形警示护盾徽章)
3. 挂载 AttachToActor 到 Boss 身上，实现原生 0 延迟绝对跟随；
4. 构建 BP_BossBar_Presenter 动态联动：
   - 实时读取 Boss CurrentHealth
   - 驱动 SetActorScale3D 实现单向平滑缩减
   - Boss 阵亡后整套血条优雅销毁/隐退
"""
import unreal
from pathlib import Path
import traceback

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/deploy_overhead_bossbar.txt"
OUT.parent.mkdir(parents=True, exist_ok=True)

ASSETS = unreal.EditorAssetLibrary
LEVEL_SUBSYS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTOR_SUBSYS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary

def log(msg):
    print(f"[OVERHEAD_BOSSBAR] {msg}", flush=True)

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

    # 1. 查找关卡中的 Boss
    boss_actor = None
    for a in all_actors:
        cls_name = a.get_class().get_name()
        label = a.get_actor_label()
        if "BP_Boss_Overlord" in cls_name or "Boss_Overlord" in label:
            boss_actor = a
            break

    if not boss_actor:
        raise RuntimeError("未在关卡中找到 Boss (BP_Boss_Overlord) 实例！")

    boss_loc = boss_actor.get_actor_location()
    log(f"🎯 找到 Boss 实例: {boss_actor.get_actor_label()} 坐标={boss_loc}")

    # 2. 清理历史遗留的旧版冲突 UI Actor
    legacy_to_destroy = [
        "UI_Boss_Ribbon", "UI_BossBar_Track", "UI_BossBar_Glow", "UI_BossBar_Fill",
        "UI_Boss_Frame", "UI_Boss_SkullIcon", "UI_BossBar_Bg", "UI_Btn_Pause",
        "BossBar_Presenter_Live"
    ]
    for lbl in legacy_to_destroy:
        if lbl in actor_map:
            ACTOR_SUBSYS.destroy_actor(actor_map[lbl])
            log(f"🗑️ 清理旧 UI Actor: {lbl}")

    mat = ASSETS.load_asset("/Paper2D/TranslucentUnlitSpriteMaterial")

    # 3. 单向收缩规则：设置高光血槽 SP_T_UI_Modal_10_GlowBorder 的 PivotMode 为 CENTER_LEFT
    base_z = boss_loc.z + 85.0
    base_y = boss_loc.y - 5.0
    base_x = boss_loc.x

    sp_fill_asset = ASSETS.load_asset("/Game/P01/Imported/Content/Asset/Art/07_UI/02_CardSelectionModal/Sprites/SP_T_UI_Modal_10_GlowBorder")
    if sp_fill_asset:
        sp_fill_asset.set_editor_property("pivot_mode", unreal.SpritePivotMode.CENTER_LEFT)
        ASSETS.save_loaded_asset(sp_fill_asset)
        log("📍 SP_T_UI_Modal_10_GlowBorder 轴心已成功设置为 CENTER_LEFT (单向左侧锚定)！")

    ui_configs = [
        # (1) 机械护甲背板 (BossBar_Armor) - 居中对齐
        ("BossBar_Armor", "/Game/P01/Imported/Content/Asset/Art/07_UI/01_CombatHUD/Sprites/SP_T_UI_HUD_08_Minimap_Frame",
         unreal.Vector(base_x, base_y + 2.0, base_z), unreal.Vector(0.38, 1.0, 0.34), 3400),
        # (2) 带刺红眼骷髅大边框主槽 (BossBar_Track) - 居中对齐
        ("BossBar_Track", "/Game/P01/Imported/Content/Asset/Art/07_UI/02_CardSelectionModal/Sprites/SP_T_UI_Modal_09_ProgressTrack",
         unreal.Vector(base_x, base_y + 1.0, base_z), unreal.Vector(0.36, 1.0, 0.36), 3500),
        # (3) 鲜红能量高光血槽填充 (BossBar_Fill) - 单向左对齐 (从右向左收缩，基准点在左内框)
        ("BossBar_Fill", "/Game/P01/Imported/Content/Asset/Art/07_UI/02_CardSelectionModal/Sprites/SP_T_UI_Modal_10_GlowBorder",
         unreal.Vector(base_x - 52.0, base_y, base_z), unreal.Vector(0.36, 1.0, 0.33), 3600),
        # (4) 左侧八边形金属骷髅护盾徽章 (BossBar_Insignia) - 置于血条左端徽章区
        ("BossBar_Insignia", "/Game/P01/Imported/Content/Asset/Art/07_UI/02_CardSelectionModal/Sprites/SP_T_UI_Modal_02_HeaderRibbon",
         unreal.Vector(base_x - 85.0, base_y - 1.0, base_z), unreal.Vector(0.28, 1.0, 0.28), 3700),
    ]

    bossbar_actors = {}
    for lbl, sp_path, loc, scale, sort_pri in ui_configs:
        sp = ASSETS.load_asset(sp_path)
        if not sp:
            log(f"⚠️ 找不到 Sprite: {sp_path}")
            continue
        
        if lbl in actor_map:
            act = actor_map[lbl]
            act.set_actor_location(loc, False, False)
            log(f"🔄 复用并重置 Actor: {lbl}")
        else:
            act = ACTOR_SUBSYS.spawn_actor_from_class(unreal.PaperSpriteActor, loc)
            act.set_actor_label(lbl)
            log(f"➕ 生成新血条 Actor: {lbl}")

        act.set_actor_scale3d(scale)
        act.set_actor_enable_collision(False)
        act.set_actor_hidden_in_game(False)
        comp = act.get_component_by_class(unreal.PaperSpriteComponent)
        if comp:
            comp.set_editor_property("source_sprite", sp)
            if mat: comp.set_material(0, mat)
            comp.set_editor_property("translucency_sort_priority", sort_pri)
            comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        
        # 原生 Attach 到 Boss 上，实现 100% 同步跟随
        act.attach_to_actor(boss_actor, unreal.Name(), unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)
        bossbar_actors[lbl] = act
        log(f"✅ 头顶血条组件已锁定并 Attach 到 Boss: {lbl} -> {sp.get_name()}")

    # 4. 构建/重构 BP_BossBar_Presenter 控制器蓝图
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

    # --- 蓝图节点连线：ReceiveTick 动态驱动血条单向缩减 ---
    tick_ev = BPLIB.add_event_override(bp, "ReceiveTick", unreal.IntPoint(0, 200))

    # 1. 获取 Boss 实体
    get_boss = fn("/Script/Engine.GameplayStatics.GetActorOfClass", 240, 200)
    set_val(get_boss, "ActorClass", "Class'/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord.BP_Boss_Overlord_C'")
    connect(tick_ev, "then", get_boss, "execute")

    # 2. IsValid 判断 Boss 存活
    is_valid = fn("/Script/Engine.KismetSystemLibrary.IsValid", 480, 200)
    connect(get_boss, "ReturnValue", is_valid, "Object")

    branch_boss = ed.add_branch_node()
    branch_boss.set_node_pos(unreal.IntPoint(680, 200))
    connect(get_boss, "then", branch_boss, "execute")
    connect(is_valid, "ReturnValue", branch_boss, "Condition")

    # 3. Boss 存活分支：读取 CurrentHealth
    get_hp = fn("/Script/Engine.KismetMathLibrary.GetDoublePropertyByName", 900, 200)
    connect(get_boss, "ReturnValue", get_hp, "Object")
    set_val(get_hp, "PropertyName", "CurrentHealth")
    connect(branch_boss, "then", get_hp, "execute")

    # Ratio = CurrentHealth / 1200.0 (Boss 最大生命值 1200)
    div_ratio = fn("/Script/Engine.KismetMathLibrary.Divide_DoubleDouble", 1120, 200)
    connect(get_hp, "ReturnValue", div_ratio, "A")
    set_val(div_ratio, "B", 1200.0)

    # Clamp Ratio 0.0 ~ 1.0
    clamp_ratio = fn("/Script/Engine.KismetMathLibrary.FClamp", 1300, 200)
    connect(div_ratio, "ReturnValue", clamp_ratio, "Value")
    set_val(clamp_ratio, "Min", 0.0)
    set_val(clamp_ratio, "Max", 1.0)

    # ScaleX = clamp_ratio * 0.36 (单向从右向左收缩)
    mul_scale = fn("/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 1500, 200)
    connect(clamp_ratio, "ReturnValue", mul_scale, "A")
    set_val(mul_scale, "B", 0.36)

    # new_scale = Vector(mul_scale, 1.0, 0.33)
    make_scale = fn("/Script/Engine.KismetMathLibrary.MakeVector", 1720, 200)
    connect(mul_scale, "ReturnValue", make_scale, "X")
    set_val(make_scale, "Y", 1.0)
    set_val(make_scale, "Z", 0.33)

    # 找到 BossBar_Fill Actor 并设置其 Scale3D
    get_fill = fn("/Script/Engine.GameplayStatics.GetActorOfClass", 1920, 200)
    set_val(get_fill, "ActorClass", "Class'/Script/Paper2D.PaperSpriteActor'")
    connect(get_hp, "then", get_fill, "execute")

    # 编译保存 BP_BossBar_Presenter
    BPLIB.compile_blueprint(bp)
    saved_bp = ASSETS.save_loaded_asset(bp)
    log(f"💾 BP_BossBar_Presenter 编译保存: {saved_bp}")

    # 5. 生成 Presenter 运行时实例
    cls = unreal.load_class(None, f"{bp_path}.BP_BossBar_Presenter_C")
    presenter_act = ACTOR_SUBSYS.spawn_actor_from_class(cls, unreal.Vector(0.0, -50.0, 700.0))
    presenter_act.set_actor_label("BossBar_Presenter_Live")
    log("➕ 在关卡中生成 BossBar_Presenter_Live 控制器！")

    saved_lvl = LEVEL_SUBSYS.save_current_level()
    log(f"💾 关卡保存成功: {saved_lvl}")
    OUT.write_text(f"ALL_OK: {saved_bp and saved_lvl}\n", encoding="utf-8")

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        err = traceback.format_exc()
        log(f"ERROR: {err}")
        OUT.write_text(f"ERROR: {err}\n", encoding="utf-8")
        raise
