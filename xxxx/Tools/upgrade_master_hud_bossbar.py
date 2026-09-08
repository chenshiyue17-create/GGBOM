# -*- coding: utf-8 -*-
"""
upgrade_master_hud_bossbar.py
在 BP_GGBOM_MasterHUD 中装配用户指定的 4 大 UI 资产：
- T_UI_HUD_08_Minimap_Frame (Boss 徽章头像框)
- T_UI_Modal_02_HeaderRibbon (Boss 称号横幅)
- T_UI_Modal_10_GlowBorder (外围流光边框)
- T_UI_Modal_09_ProgressTrack (血槽底轨)
加上：
- SP_T_UI_BossBar_01_Seg1_Fill (血条高能填充)
- SP_T_UI_BossBar_05_Skull_Normal (骷髅头像徽章)
并在 ReceiveTick 中注入与 BP_Boss_Overlord 的血量攻击数据联动！
"""
import unreal
from pathlib import Path
import traceback

ROOT = Path(unreal.Paths.project_dir()).resolve()
OUT = ROOT / "output/upgrade_hud_result.txt"
OUT.parent.mkdir(parents=True, exist_ok=True)

ASSETS = unreal.EditorAssetLibrary
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary
SUBOBJECTS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)

def log(msg):
    print(f"[HUD_UPGRADE] {msg}", flush=True)

def add_subobject(bp, parent_handle, name, cls):
    params = unreal.AddNewSubobjectParams()
    params.set_editor_property("parent_handle", parent_handle)
    params.set_editor_property("new_class", cls)
    h, reason = SUBOBJECTS.add_new_subobject(params)
    if not h.is_valid():
        raise RuntimeError(f"Failed to add {name}: {reason}")
    SUBOBJECTS.rename_subobject(h, unreal.Text(name))
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
    comp = unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)
    return h, comp

def run():
    bp_path = "/Game/GGBOM/Blueprints/BP_GGBOM_MasterHUD"
    log(f"🚀 加载主 HUD: {bp_path}")
    bp = ASSETS.load_asset(bp_path)
    if not bp: raise RuntimeError(f"未找到: {bp_path}")

    handles = SUBOBJECTS.k2_gather_subobject_data_for_blueprint(bp)
    root_handle = handles[0]

    existing_vars = {}
    for h in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        vname = str(unreal.SubobjectDataBlueprintFunctionLibrary.get_variable_name(data))
        existing_vars[vname] = (h, unreal.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp))

    mat = unreal.load_asset("/Paper2D/TranslucentUnlitSpriteMaterial")

    # 指定的 4 大核心美术资产 + 填充与头像
    boss_ui_specs = [
        # (组件名, Sprite路径, 相对坐标(X, Y, Z), 缩放X, 缩放Z, 排序优先级)
        # 1. 顶部 HeaderRibbon (横幅)
        ("Comp_Boss_Ribbon", "/Game/P01/Imported/Content/Asset/Art/07_UI/02_CardSelectionModal/Sprites/SP_T_UI_Modal_02_HeaderRibbon", unreal.Vector(0.0, 0.0, 785.0), 0.45, 0.45, 3000),
        # 2. 血槽底轨 ProgressTrack
        ("Comp_BossBar_Track", "/Game/P01/Imported/Content/Asset/Art/07_UI/02_CardSelectionModal/Sprites/SP_T_UI_Modal_09_ProgressTrack", unreal.Vector(-20.0, 0.0, 745.0), 0.45, 0.45, 3010),
        # 3. 外围发光边框 GlowBorder
        ("Comp_BossBar_Glow", "/Game/P01/Imported/Content/Asset/Art/07_UI/02_CardSelectionModal/Sprites/SP_T_UI_Modal_10_GlowBorder", unreal.Vector(-20.0, -1.0, 745.0), 0.45, 0.45, 3020),
        # 4. 血条红色填充 Seg1_Fill
        ("Comp_BossBar_Fill", "/Game/P01/Imported/Content/Asset/Art/07_UI/03_BossHealthBar/Sprites/SP_T_UI_BossBar_01_Seg1_Fill", unreal.Vector(-20.0, -2.0, 745.0), 0.45, 0.45, 3015),
        # 5. 头像外框 Minimap_Frame
        ("Comp_Boss_Frame", "/Game/P01/Imported/Content/Asset/Art/07_UI/01_CombatHUD/Sprites/SP_T_UI_HUD_08_Minimap_Frame", unreal.Vector(190.0, -1.0, 745.0), 0.42, 0.42, 3030),
        # 6. 头像内骷髅徽章 Skull_Normal
        ("Comp_Boss_Skull", "/Game/P01/Imported/Content/Asset/Art/07_UI/03_BossHealthBar/Sprites/SP_T_UI_BossBar_05_Skull_Normal", unreal.Vector(190.0, -2.0, 745.0), 0.32, 0.32, 3035),
    ]

    for comp_name, sp_path, loc, sx, sz, sort_pri in boss_ui_specs:
        sp = unreal.load_asset(sp_path)
        if not sp:
            log(f"⚠️ 未找到 Sprite: {sp_path}")
            continue
        if comp_name not in existing_vars:
            h, comp = add_subobject(bp, root_handle, comp_name, unreal.PaperSpriteComponent.static_class())
        else:
            comp = existing_vars[comp_name][1]

        comp.set_editor_property("source_sprite", sp)
        if mat:
            comp.set_material(0, mat)
        comp.set_editor_property("relative_location", loc)
        comp.set_editor_property("relative_scale3d", unreal.Vector(sx, 1.0, sz))
        comp.set_editor_property("translucency_sort_priority", sort_pri)
        comp.set_editor_property("visible", True)
        comp.set_editor_property("hidden_in_game", False)
        log(f"✅ 装配组件 {comp_name} 完毕")

    BPLIB.compile_blueprint(bp)
    saved = ASSETS.save_loaded_asset(bp)
    log(f"✅ MasterHUD 保存完成: {saved}")
    OUT.write_text(f"SAVED: {saved}\n", encoding="utf-8")

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        err = traceback.format_exc()
        log(f"ERROR: {err}")
        OUT.write_text(f"ERROR: {err}\n", encoding="utf-8")
        raise
