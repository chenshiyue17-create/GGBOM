# -*- coding: utf-8 -*-
"""
apply_final_boss_combat_and_health_closure.py
终极闭环落盘脚本：
1. 子弹 BP_ProjectileBase 碰撞通道：全量开启 ECC_WorldDynamic 与 ECC_Pawn 的 Overlap，彻底解决远程不掉血；
2. Boss BP_Boss_Overlord 蓝图：
   - 注入 CurrentHealth 与 MaxHealth (1200.0)；
   - 碰撞设为 ECC_Pawn + Overlap ECC_WorldDynamic；
   - ReceiveAnyDamage 受击扣血、飘字 (-45)、血条等比单向收缩；
   - 生命归零级联销毁全部挂载血条 Actor 与自身；
3. 关卡 MAP_GGBOM_Main：
   - 清理冲突的 Presenter 控制器；
   - 精准校准 4 大血条几何尺寸与相对位置 (Z=0.17, X=0.24, CENTER_LEFT 锚定，严丝合缝内嵌凹槽)；
   - 挂载 Attached 到 Boss 头顶；
   - 保存关卡。
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
    print(f"[FIX_COMBAT] {msg}", flush=True)

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
        return ok
    else:
        log(f"  ❌ 连接引脚未找到: {p1} -> {p2}")
        return False

def set_val(n, pin_name, val):
    p = get_pin(n, pin_name, is_input=True)
    if p:
        try:
            PINLIB.set_pin_value(p, str(val))
        except Exception as e:
            log(f"设置引脚异常: {e}")

def run():
    log("🚀 ==================== 开始执行终极修复闭环 ====================")

    # -------------------------------------------------------------
    # 步骤 1: 修复子弹 BP_ProjectileBase 碰撞通道
    # -------------------------------------------------------------
    log("1. 配置子弹 BP_ProjectileBase 碰撞通道与触发响应...")
    proj_bp_path = "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase"
    proj_bp = ASSETS.load_asset(proj_bp_path)
    if not proj_bp:
        raise RuntimeError("未找到子弹蓝图！")

    subsys = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = subsys.k2_gather_subobject_data_for_blueprint(proj_bp)
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data)).lower()
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, proj_bp)
        if isinstance(obj, unreal.SphereComponent) or "sphere" in vname:
            obj.set_editor_property("sphere_radius", 24.0)
            obj.set_collision_profile_name("Custom")
            obj.set_collision_enabled(unreal.CollisionEnabled.QUERY_ONLY)
            obj.set_collision_response_to_all_channels(unreal.CollisionResponseType.ECR_IGNORE)
            # 关键：同时对 Pawn 和 WorldDynamic 开启 Overlap！
            obj.set_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN, unreal.CollisionResponseType.ECR_OVERLAP)
            obj.set_collision_response_to_channel(unreal.CollisionChannel.ECC_WORLD_DYNAMIC, unreal.CollisionResponseType.ECR_OVERLAP)
            obj.set_collision_response_to_channel(unreal.CollisionChannel.ECC_PHYSICS_BODY, unreal.CollisionResponseType.ECR_OVERLAP)
            obj.set_editor_property("generate_overlap_events", True)
            log("  🎯 子弹碰撞体已对 ECC_Pawn 和 ECC_WorldDynamic 全量开启 Overlap！")

    BPLIB.compile_blueprint(proj_bp)
    ASSETS.save_loaded_asset(proj_bp)
    log("  💾 BP_ProjectileBase 保存完毕")

    # -------------------------------------------------------------
    # 步骤 2: 重塑 Boss BP_Boss_Overlord 碰撞与受击销毁图表
    # -------------------------------------------------------------
    log("2. 配置 Boss BP_Boss_Overlord 蓝图生命值与图表...")
    boss_bp_path = "/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord"
    boss_bp = ASSETS.load_asset(boss_bp_path)
    if not boss_bp:
        raise RuntimeError("未找到 Boss 蓝图！")

    # 确保变量存在
    existing_vars = [str(x) for x in BPLIB.list_member_variable_names(boss_bp)]
    if "CurrentHealth" not in existing_vars:
        pin_type = unreal.EdGraphPinType(pin_category="real", pin_sub_category="double")
        BPLIB.add_member_variable(boss_bp, "CurrentHealth", pin_type)
        log("  ➕ 添加成员变量 CurrentHealth")
    if "MaxHealth" not in existing_vars:
        pin_type = unreal.EdGraphPinType(pin_category="real", pin_sub_category="double")
        BPLIB.add_member_variable(boss_bp, "MaxHealth", pin_type)
        log("  ➕ 添加成员变量 MaxHealth")

    # 配置组件碰撞为 ECC_PAWN 并开启 Overlap
    boss_handles = subsys.k2_gather_subobject_data_for_blueprint(boss_bp)
    for h in boss_handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data)).lower()
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, boss_bp)
        if isinstance(obj, unreal.PrimitiveComponent):
            obj.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
            obj.set_collision_object_type(unreal.CollisionChannel.ECC_PAWN)
            obj.set_collision_response_to_all_channels(unreal.CollisionResponseType.ECR_BLOCK)
            obj.set_collision_response_to_channel(unreal.CollisionChannel.ECC_WORLD_DYNAMIC, unreal.CollisionResponseType.ECR_OVERLAP)
            obj.set_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN, unreal.CollisionResponseType.ECR_BLOCK)
            obj.set_editor_property("generate_overlap_events", True)
            log(f"  🛡️ Boss 组件 {vname} 碰撞已设为 ECC_PAWN + Overlap ECC_WorldDynamic")

    # 蓝图图表清理旧受击节点（保留移动和 AI，y < 900）
    graph = BPLIB.find_event_graph(boss_bp)
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
        dmg_node = BPLIB.add_event_override(boss_bp, "ReceiveAnyDamage", unreal.IntPoint(0, 1000))

    for p in BPLIB.list_all_pins(dmg_node):
        try: PINLIB.break_pin_links(p)
        except Exception: pass
    dmg_node.set_node_pos(unreal.IntPoint(0, 1000))

    def fn(path, x, y):
        n = ed.add_call_function_node(path)
        n.set_node_pos(unreal.IntPoint(x, y))
        return n

    # 1. 扣减血量
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

    # 2. 生成伤害飘字 -45 (BP_Combat_DamagePop)
    loc_boss = fn("/Script/Engine.Actor.K2_GetActorLocation", 920, 1260)
    pop_loc_add = fn("/Script/Engine.KismetMathLibrary.Add_VectorVector", 1140, 1260)
    connect(loc_boss, "ReturnValue", pop_loc_add, "A")
    set_val(pop_loc_add, "B", "0, -10, 50")

    pop_trans = fn("/Script/Engine.KismetMathLibrary.MakeTransform", 1360, 1260)
    connect(pop_loc_add, "ReturnValue", pop_trans, "Location")
    set_val(pop_trans, "Scale", "1, 1, 1")

    spawn_pop = fn("/Script/Engine.GameplayStatics.BeginDeferredActorSpawnFromClass", 1580, 1000)
    set_val(spawn_pop, "ActorClass", "Class'/Game/Blueprints/Combat/Projectiles/BP_Combat_DamagePop.BP_Combat_DamagePop_C'")
    connect(set_hp, "then", spawn_pop, "execute")
    connect(pop_trans, "ReturnValue", spawn_pop, "SpawnTransform")

    finish_pop = fn("/Script/Engine.GameplayStatics.FinishSpawningActor", 1840, 1000)
    connect(spawn_pop, "then", finish_pop, "execute")
    connect(spawn_pop, "ReturnValue", finish_pop, "Actor")
    connect(pop_trans, "ReturnValue", finish_pop, "SpawnTransform")

    # 3. 死亡判定
    is_dead = fn("/Script/Engine.KismetMathLibrary.LessEqual_DoubleDouble", 1840, 1180)
    connect(max_zero, "ReturnValue", is_dead, "A")
    set_val(is_dead, "B", 0.0)

    branch = ed.add_branch_node()
    branch.set_node_pos(unreal.IntPoint(2080, 1000))
    connect(finish_pop, "then", branch, "execute")
    connect(is_dead, "ReturnValue", branch, "Condition")

    # ---------------- 死亡分支 (branch.then): 级联彻底销毁所有血条 Actor + 销毁自身 ----------------
    get_tag_bars = fn("/Script/Engine.GameplayStatics.GetAllActorsWithTag", 2320, 880)
    set_val(get_tag_bars, "Tag", "BossBarGroup")
    connect(branch, "then", get_tag_bars, "execute")

    last_destroy = get_tag_bars
    for i in range(4):
        tag_get = fn("/Script/Engine.KismetArrayLibrary.Array_Get", 2560 + i * 260, 880)
        connect(get_tag_bars, "OutActors", tag_get, "TargetArray")
        set_val(tag_get, "Index", i)

        dest_tag = fn("/Script/Engine.Actor.K2_DestroyActor", 2700 + i * 260, 880)
        connect(last_destroy, "then", dest_tag, "execute")
        connect(tag_get, "Item", dest_tag, "self")
        last_destroy = dest_tag

    # 最终销毁 Boss 自身
    destroy_boss = fn("/Script/Engine.Actor.K2_DestroyActor", 3800, 880)
    connect(last_destroy, "then", destroy_boss, "execute")

    # ---------------- 存活受击分支 (branch.else): 动态自适应血条单向收缩 ----------------
    div_ratio = fn("/Script/Engine.KismetMathLibrary.Divide_DoubleDouble", 2320, 1200)
    connect(max_zero, "ReturnValue", div_ratio, "A")
    set_val(div_ratio, "B", 1200.0)

    clamp_ratio = fn("/Script/Engine.KismetMathLibrary.FClamp", 2540, 1200)
    connect(div_ratio, "ReturnValue", clamp_ratio, "Value")
    set_val(clamp_ratio, "Min", 0.0)
    set_val(clamp_ratio, "Max", 1.0)

    mul_scale = fn("/Script/Engine.KismetMathLibrary.Multiply_DoubleDouble", 2760, 1200)
    connect(clamp_ratio, "ReturnValue", mul_scale, "A")
    set_val(mul_scale, "B", 0.24)

    make_scale = fn("/Script/Engine.KismetMathLibrary.MakeVector", 2980, 1200)
    connect(mul_scale, "ReturnValue", make_scale, "X")
    set_val(make_scale, "Y", 1.0)
    set_val(make_scale, "Z", 0.17)

    get_fill_tag = fn("/Script/Engine.GameplayStatics.GetAllActorsWithTag", 2320, 1380)
    set_val(get_fill_tag, "Tag", "BossBarFill")
    connect(branch, "else", get_fill_tag, "execute")

    fill_get = fn("/Script/Engine.KismetArrayLibrary.Array_Get", 2560, 1380)
    connect(get_fill_tag, "OutActors", fill_get, "TargetArray")
    set_val(fill_get, "Index", 0)

    set_fill_scale = fn("/Script/Engine.Actor.SetActorScale3D", 3200, 1200)
    connect(get_fill_tag, "then", set_fill_scale, "execute")
    connect(fill_get, "Item", set_fill_scale, "self")
    connect(make_scale, "ReturnValue", set_fill_scale, "NewScale3D")

    # 编译并保存 Boss 蓝图
    BPLIB.compile_blueprint(boss_bp)
    ASSETS.save_loaded_asset(boss_bp)
    log("  💾 BP_Boss_Overlord 蓝图重塑保存完毕！")

    # -------------------------------------------------------------
    # 步骤 3: 治理 MAP_GGBOM_Main 关卡 Actor 与血条几何
    # -------------------------------------------------------------
    log("3. 治理 MAP_GGBOM_Main 关卡 Actor 与血条几何...")
    LEVEL_SUBSYS.load_level("/Game/GGBOM/Maps/MAP_GGBOM_Main")
    lvl_actors = ACTOR_SUBSYS.get_all_level_actors()

    # 1. 彻底清理冲突的 Presenter
    for a in lvl_actors:
        lbl = a.get_actor_label()
        if "Presenter" in lbl:
            ACTOR_SUBSYS.destroy_actor(a)
            log(f"  🗑️ 已彻底清理冲突控制器: {lbl}")

    # 2. 查找 Boss
    boss_inst = None
    for a in lvl_actors:
        if a.get_actor_label() == "Live_Boss_Overlord":
            boss_inst = a
            break

    if not boss_inst:
        raise RuntimeError("未在关卡中找到 Live_Boss_Overlord！")

    boss_inst.set_actor_enable_collision(True)
    for c in boss_inst.get_components_by_class(unreal.PrimitiveComponent):
        c.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
        c.set_collision_object_type(unreal.CollisionChannel.ECC_PAWN)
        c.set_collision_response_to_all_channels(unreal.CollisionResponseType.ECR_BLOCK)
        c.set_collision_response_to_channel(unreal.CollisionChannel.ECC_WORLD_DYNAMIC, unreal.CollisionResponseType.ECR_OVERLAP)
        c.set_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN, unreal.CollisionResponseType.ECR_BLOCK)
        c.set_editor_property("generate_overlap_events", True)
    log("  🛡️ 关卡中 Live_Boss_Overlord 碰撞体已全面激活 ECC_PAWN")

    # 3. 校准 4 个血条 Actor
    sp_track_path = "/Game/P01/Imported/Content/Asset/Art/07_UI/02_CardSelectionModal/Sprites/SP_T_UI_Modal_09_ProgressTrack"
    sp_fill_path = "/Game/P01/Imported/Content/Asset/Art/07_UI/02_CardSelectionModal/Sprites/SP_T_UI_Modal_10_GlowBorder"
    sp_armor_path = "/Game/P01/Imported/Content/Asset/Art/07_UI/01_CombatHUD/Sprites/SP_T_UI_HUD_08_Minimap_Frame"
    sp_insignia_path = "/Game/P01/Imported/Content/Asset/Art/07_UI/02_CardSelectionModal/Sprites/SP_T_UI_Modal_02_HeaderRibbon"

    # 确保 Fill 轴心为 CENTER_LEFT
    sp_fill = ASSETS.load_asset(sp_fill_path)
    if sp_fill:
        sp_fill.set_editor_property("pivot_mode", unreal.SpritePivotMode.CENTER_LEFT)
        ASSETS.save_loaded_asset(sp_fill)

    configs = {
        "BossBar_Armor": {
            "sprite": sp_armor_path,
            "rel_loc": unreal.Vector(0.0, -2.53, 71.73),
            "scale": unreal.Vector(0.38, 1.0, 0.34),
            "tags": ["BossBarGroup"]
        },
        "BossBar_Track": {
            "sprite": sp_track_path,
            "rel_loc": unreal.Vector(0.0, -3.38, 71.73),
            "scale": unreal.Vector(0.36, 1.0, 0.36),
            "tags": ["BossBarGroup"]
        },
        "BossBar_Fill": {
            "sprite": sp_fill_path,
            "rel_loc": unreal.Vector(-58.0, -4.20, 71.73),
            "scale": unreal.Vector(0.24, 1.0, 0.17),
            "tags": ["BossBarGroup", "BossBarFill"]
        },
        "BossBar_Insignia": {
            "sprite": sp_insignia_path,
            "rel_loc": unreal.Vector(-71.73, -5.06, 71.73),
            "scale": unreal.Vector(0.28, 1.0, 0.28),
            "tags": ["BossBarGroup"]
        }
    }

    # 查找或重新绑定血条 Actor
    for a in lvl_actors:
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
            a.attach_to_actor(boss_inst, unreal.Name(), unreal.AttachmentRule.KEEP_RELATIVE,
                             unreal.AttachmentRule.KEEP_RELATIVE, unreal.AttachmentRule.KEEP_WORLD, False)
            root.set_editor_property("relative_location", cfg["rel_loc"])
            a.set_actor_scale3d(cfg["scale"])
            a.tags = [unreal.Name(t) for t in cfg["tags"]]
            log(f"  ✨ {lbl} 已校准附加至 Boss，相对坐标: {cfg['rel_loc']}, 缩放: {cfg['scale']}")

    saved_lvl = LEVEL_SUBSYS.save_current_level()
    log(f"💾 关卡保存状态: {saved_lvl}")
    log("🎉 ==================== 完整修复全部圆满达成 ====================")

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        err = traceback.format_exc()
        log(f"ERROR: {err}")
        raise
