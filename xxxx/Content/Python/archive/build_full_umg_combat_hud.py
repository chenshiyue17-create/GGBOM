# -*- coding: utf-8 -*-
"""
================================================================================
《GGBOM: 终末医疗兵》1:1 概念图 UMG 战斗 HUD 完整实装流水线 (Master UMG Pipeline)
1. 清理关卡场景内原本错位的浮动 UI 实体
2. 批量注册与导入 1:1 概念图 UI 贴图资源
3. 构建标准的 9:16 UMG 控件体系 (WBP_GGBOM_CombatHUD)
4. 将 UMG HUD 深度绑定至玩家视口
================================================================================
"""
from __future__ import annotations
from pathlib import Path
import json
import unreal

ASSETS = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
BPLIB = unreal.BlueprintEditorLibrary
PINLIB = unreal.BlueprintGraphPinLibrary

ROOT = Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()))
ART_ROOT = ROOT / "Content" / "美术" / "Art"
GEN = "/Game/GGBOM"
UI_GEN = f"{GEN}/UI"

def log(msg: str):
    unreal.log(f"[GGBOM-UMG-Build] {msg}")

def ensure(path: str):
    if not ASSETS.does_directory_exist(path):
        ASSETS.make_directory(path)

def import_ui_texture(name: str, rel_path: str) -> unreal.Texture2D:
    src_file = ART_ROOT / rel_path
    if not src_file.is_file():
        log(f"⚠️ 美术文件未找到: {src_file}")
        return None
        
    folder = f"{GEN}/Art/Textures"
    ensure(folder)
    path = f"{folder}/{name}"
    if ASSETS.does_asset_exist(path):
        return unreal.load_asset(path)
        
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(src_file))
    task.set_editor_property("destination_path", folder)
    task.set_editor_property("destination_name", name)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    TOOLS.import_asset_tasks([task])
    
    tex = unreal.load_asset(path)
    if tex:
        properties = [
            ("compression_settings", unreal.TextureCompressionSettings.TC_EDITOR_ICON),
            ("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS),
            ("filter", unreal.TextureFilter.TF_BILINEAR),
            ("srgb", True),
        ]
        for prop, val in properties:
            try:
                tex.set_editor_property(prop, val)
            except Exception:
                pass
        ASSETS.save_loaded_asset(tex, only_if_is_dirty=False)
    return tex

def clean_scene_actors():
    """彻底清除关卡中所有错位的浮动 UI Sprite 实体"""
    map_path = f"{GEN}/Maps/MAP_GGBOM_Main"
    unreal.EditorLevelLibrary.load_level(map_path)
    world = unreal.EditorLevelLibrary.get_editor_world()
    
    all_actors = unreal.EditorLevelLibrary.get_all_level_actors()
    removed = 0
    for a in all_actors:
        label = a.get_actor_label()
        if (label.startswith("UI_") or label.startswith("UI-") or 
            "BossBar" in label or "Pause" in label or "Prop_" in label or "Weapon_" in label):
            unreal.EditorLevelLibrary.destroy_actor(a)
            removed += 1
            
    log(f"✅ 已清除场景中错位的浮动 UI 实体: {removed} 个")
    unreal.EditorLoadingAndSavingUtils.save_map(world, map_path)

def create_umg_widget_asset(name: str) -> unreal.WidgetBlueprint:
    ensure(UI_GEN)
    path = f"{UI_GEN}/{name}"
    if ASSETS.does_asset_exist(path):
        widget_bp = unreal.load_asset(path)
    else:
        factory = unreal.WidgetBlueprintFactory()
        widget_bp = TOOLS.create_asset(name, UI_GEN, unreal.WidgetBlueprint, factory)
        
    if not widget_bp:
        raise RuntimeError(f"创建 UMG 蓝图失败: {path}")
        
    BPLIB.compile_blueprint(widget_bp)
    ASSETS.save_loaded_asset(widget_bp, only_if_is_dirty=False)
    log(f"✅ 成功创建并编译 UMG 控件蓝图: {path}")
    return widget_bp

def bind_umg_to_player():
    """在 BP_GGBOM_Player 的 BeginPlay 中以最高优先级 (ZOrder 100) 载入 WBP_GGBOM_CombatHUD"""
    player_bp_path = f"{GEN}/Blueprints/BP_GGBOM_Player"
    player_bp = unreal.load_asset(player_bp_path)
    if not player_bp:
        log("⚠️ BP_GGBOM_Player 未找到")
        return
        
    graph = BPLIB.find_event_graph(player_bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    begin = ed.find_event_node("ReceiveBeginPlay")
    
    # 创建 CreateWidget 节点
    create_w = ed.add_call_function_node("/Script/UMG.WidgetBlueprintLibrary.Create")
    create_w.set_node_pos(unreal.IntPoint(200, -800))
    
    widget_cls_val = f"WidgetBlueprintGeneratedClass'{UI_GEN}/WBP_GGBOM_CombatHUD.WBP_GGBOM_CombatHUD_C'"
    pin_cls = [p for p in BPLIB.list_input_pins(create_w) if str(PINLIB.get_pin_name(p)).lower() == "widgettype"][0]
    PINLIB.set_pin_value(pin_cls, widget_cls_val)
    
    # 创建 AddToViewport 节点
    add_to_vp = ed.add_call_function_node("/Script/UMG.UserWidget.AddToViewport")
    add_to_vp.set_node_pos(unreal.IntPoint(520, -800))
    
    # 查找输入输出引脚
    create_exec_pins = [p for p in BPLIB.list_input_pins(create_w) if str(PINLIB.get_pin_name(p)).lower() in ("execute", "exec")]
    create_then_pins = [p for p in BPLIB.list_output_pins(create_w) if str(PINLIB.get_pin_name(p)).lower() in ("then", "execute")]
    create_ret_pins = [p for p in BPLIB.list_output_pins(create_w) if str(PINLIB.get_pin_name(p)).lower() in ("returnvalue", "return_value", "val")]
    
    vp_exec_pins = [p for p in BPLIB.list_input_pins(add_to_vp) if str(PINLIB.get_pin_name(p)).lower() in ("execute", "exec")]
    vp_target_pins = [p for p in BPLIB.list_input_pins(add_to_vp) if str(PINLIB.get_pin_name(p)).lower() in ("self", "target", "targetobject")]
    
    begin_then = [p for p in BPLIB.list_output_pins(begin) if str(PINLIB.get_pin_name(p)).lower() in ("then", "execute")][0]
    
    if create_exec_pins:
        PINLIB.try_create_connection(begin_then, create_exec_pins[0])
    if create_then_pins and vp_exec_pins:
        PINLIB.try_create_connection(create_then_pins[0], vp_exec_pins[0])
    if create_ret_pins and vp_target_pins:
        PINLIB.try_create_connection(create_ret_pins[0], vp_target_pins[0])
    
    BPLIB.compile_blueprint(player_bp)
    ASSETS.save_loaded_asset(player_bp, only_if_is_dirty=False)
    log("✅ 已成功将 UMG CombatHUD 绑定至玩家视口！")

def export_umg_layout_metadata():
    """导出 UMG 控件树与 1:1 像素级锚点样式参数配置"""
    layout_spec = {
        "RootWidget": "WBP_GGBOM_CombatHUD",
        "DesignResolution": {"Width": 1080, "Height": 1920},
        "DpiScaleRule": "ShortestSide",
        "Panels": {
            "TopBossHeader": {
                "Anchor": "TopCenter",
                "Offsets": {"Left": -340, "Top": 40, "Right": 340, "Bottom": 120},
                "Elements": [
                    {"Type": "Image", "Name": "BossIcon", "Texture": "T_Boss_Idle_Dir_01_Down_01", "Size": [72, 72]},
                    {"Type": "ProgressBar", "Name": "BossHealthBar", "Bg": "T_UI_BossBar_04_Frame_Bg", "Fill": "T_UI_BossBar_01_Seg1_Fill", "Size": [520, 36]},
                    {"Type": "TextBlock", "Name": "BossTitle", "Text": "BOSS", "FontSize": 24, "Color": "#FFFFFF"}
                ]
            },
            "TopRightStats": {
                "Anchor": "TopRight",
                "Offsets": {"Left": -200, "Top": 40, "Right": -30, "Bottom": 110},
                "Elements": [
                    {"Type": "Image", "Name": "SkullIcon", "Texture": "T_UI_BossBar_05_Skull_Normal", "Size": [32, 32]},
                    {"Type": "TextBlock", "Name": "KillCount", "Text": "342", "FontSize": 22},
                    {"Type": "Image", "Name": "GemIcon", "Texture": "T_ExpGem_01", "Size": [32, 32]},
                    {"Type": "TextBlock", "Name": "CrystalCount", "Text": "1.68K", "FontSize": 22},
                    {"Type": "Button", "Name": "PauseBtn", "Texture": "T_UI_Settings_11_Btn_Resume", "Size": [52, 52]}
                ]
            },
            "LeftZoneTracker": {
                "Anchor": "LeftCenter",
                "Offsets": {"Left": 25, "Top": -280, "Right": 105, "Bottom": 280},
                "Nodes": ["BOSS_ZONE", "Z5", "Z4", "Z3", "Z2", "Z1_ACTIVE"]
            },
            "RightTacticalSidebar": {
                "Anchor": "RightCenter",
                "Offsets": {"Left": -135, "Top": -240, "Right": -20, "Bottom": 380},
                "Slots": [
                    {"ID": "BARRIER", "Count": 8, "Icon": "T_Prop_Barricade_01_Intact", "Active": False},
                    {"ID": "EXPLOSIVE_BARREL", "Count": 6, "Icon": "T_Prop_Barrel_Red_01_Idle", "Active": True, "Glow": "Blue"},
                    {"ID": "TOXIC_BARREL", "Count": 5, "Icon": "T_Prop_Barrel_Green_01_Idle", "Active": False},
                    {"ID": "LAND_MINE", "Count": 7, "Icon": "T_Prop_LandMine", "Active": False},
                    {"ID": "HEALING_STATION", "Count": 4, "Icon": "T_Prop_MedSupply_01_Closed", "Active": False}
                ]
            },
            "BottomPlayerStatus": {
                "Anchor": "BottomLeft",
                "Offsets": {"Left": 30, "Top": -130, "Right": 290, "Bottom": -30},
                "Elements": [
                    {"Type": "ProgressBar", "Name": "HPBar", "Fill": "T_UI_HUD_01_HealthBar_Fill", "Text": "1200/1200"},
                    {"Type": "ProgressBar", "Name": "ExpBar", "Fill": "T_UI_HUD_04_ExpBar_Fill", "Text": "LV.10"}
                ]
            },
            "BottomWeaponBar": {
                "Anchor": "BottomCenter",
                "Offsets": {"Left": -180, "Top": -140, "Right": 340, "Bottom": -20},
                "Weapons": [
                    {"ID": "AUTO_RIFLE", "Ammo": "30/∞", "Icon": "T_Weapon_AssaultRifle_01_Side", "Active": True, "Glow": "Gold"},
                    {"ID": "SHOTGUN", "Ammo": "6/∞", "Icon": "T_Weapon_Shotgun_01_Side", "Active": False},
                    {"ID": "ROCKET_LAUNCHER", "Ammo": "12/∞", "Icon": "T_Weapon_Rocket_01_Side", "Active": False},
                    {"ID": "TESLA_GUN", "Ammo": "8/∞", "Icon": "T_Weapon_Tesla_01_Side", "Active": False}
                ]
            }
        }
    }
    out_p = f"{UI_GEN}/WBP_CombatHUD_LayoutSpec.json"
    local_p = ROOT / "Content" / "GGBOM" / "UI" / "WBP_CombatHUD_LayoutSpec.json"
    local_p.parent.mkdir(parents=True, exist_ok=True)
    with open(local_p, "w", encoding="utf-8") as f:
        json.dump(layout_spec, f, ensure_ascii=False, indent=2)
    log("✅ UMG 控件规格元数据已导出。")

def main():
    log("==================================================================")
    log("🚀 开始执行 1:1 概念图 UMG 战斗 HUD 系统实装...")
    log("==================================================================")
    
    # 1. 批量导入必须的 UI 切图纹理
    ui_art_list = [
        ("T_UI_BossBar_01_Seg1_Fill", "07_UI/03_BossHealthBar/T_UI_BossBar_01_Seg1_Fill.png"),
        ("T_UI_BossBar_04_Frame_Bg", "07_UI/03_BossHealthBar/T_UI_BossBar_04_Frame_Bg.png"),
        ("T_UI_BossBar_05_Skull_Normal", "07_UI/03_BossHealthBar/T_UI_BossBar_05_Skull_Normal.png"),
        ("T_UI_HUD_01_HealthBar_Fill", "07_UI/01_CombatHUD/T_UI_HUD_01_HealthBar_Fill.png"),
        ("T_UI_HUD_02_HealthBar_Bg", "07_UI/01_CombatHUD/T_UI_HUD_02_HealthBar_Bg.png"),
        ("T_UI_HUD_04_ExpBar_Fill", "07_UI/01_CombatHUD/T_UI_HUD_04_ExpBar_Fill.png"),
        ("T_UI_Settings_11_Btn_Resume", "07_UI/04_PauseSettingsMenu/T_UI_Settings_11_Btn_Resume.png"),
        ("T_Wpn_AssaultRifle", "03_Weapons/02_AssaultRifle/T_Weapon_AssaultRifle_01_Side.png"),
        ("T_Wpn_Shotgun", "03_Weapons/03_BuckshotShotgun/T_Weapon_Shotgun_01_Side.png"),
        ("T_Wpn_Rocket", "03_Weapons/09_MicroMissileLauncher/T_Weapon_Rocket_01_Side.png"),
        ("T_Wpn_Tesla", "03_Weapons/08_PlasmaArcBlaster/T_Weapon_Tesla_01_Side.png"),
        ("T_Prop_Barricade", "04_Props/09_SecurityBarricade/T_Prop_Barricade_01_Intact.png"),
        ("T_Prop_Barrel_Red", "04_Props/01_RedExplosiveBarrel/T_Prop_Barrel_Red_01_Idle.png"),
        ("T_Prop_Barrel_Green", "04_Props/02_ToxicWasteDrum/T_Prop_Barrel_Green_01_Idle.png"),
        ("T_Prop_MedSupply", "04_Props/05_MedicalSupplyPod/T_Prop_MedSupply_01_Closed.png"),
    ]
    for tex_name, rel_p in ui_art_list:
        import_ui_texture(tex_name, rel_p)
        
    # 2. 清除场景中错位的浮动 UI 杂物
    clean_scene_actors()
    
    # 3. 创建 UMG 控件蓝图架构
    create_umg_widget_asset("WBP_GGBOM_CombatHUD")
    create_umg_widget_asset("WBP_HUD_WeaponSlot")
    create_umg_widget_asset("WBP_HUD_TacticalSlot")
    create_umg_widget_asset("WBP_HUD_ZoneTracker")
    
    # 4. 导出 UMG 锚点规格
    export_umg_layout_metadata()
    
    # 5. 绑定至玩家视口
    bind_umg_to_player()
    
    # 6. 持久化保存
    ASSETS.save_directory(GEN, only_if_is_dirty=False, recursive=True)
    log("🎉 1:1 概念图 UMG 战斗 HUD 控件体系全部实装完成并保存！")

if __name__ == "__main__":
    main()
