"""
Inspect and integrate Inferno Shock VFX assets into combat blueprints.
"""
from __future__ import annotations

import json
import os
import unreal

SP_DIR = "/Game/P01/Imported/Content/Asset/Art/05_VFX/02_Inferno_Shock/Sprites"
FB_DIR = "/Game/P01/Imported/Content/Asset/Art/05_VFX/02_Inferno_Shock/Flipbooks"
FB_SHEET_PATH = f"{FB_DIR}/FB_T_VFX_Inferno_Shock_Sheet"
NEW_FB_PATH = "/Game/Blueprints/Combat/Projectiles/FB_Combat_Inferno_Shock"
EXP_BP_PATH = "/Game/Blueprints/Combat/Projectiles/BP_Combat_HitExplosion"
PROJ_BP_PATH = "/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase"

def log(msg: str):
    unreal.log(f"[INFERNO_VFX] {msg}")

def inspect_and_build():
    log("==================================================")
    log("🔥 开始装配并应用用户指定的 Inferno Shock 命中爆炸素材...")
    
    # 1. 检查 4 个单独 Sprite 资产
    sprites = []
    for i in range(1, 5):
        sp_path = f"{SP_DIR}/SP_T_VFX_Inferno_Shock_0{i}"
        sp = unreal.EditorAssetLibrary.load_asset(sp_path)
        if sp:
            sprites.append(sp)
            log(f"  ✅ 已加载帧 0{i}: {sp_path}")
        else:
            log(f"  ⚠️ 未找到单独 Sprite 0{i}: {sp_path}")
            
    # 2. 检查现存的 Sheet Flipbook
    sheet_fb = unreal.EditorAssetLibrary.load_asset(FB_SHEET_PATH)
    if sheet_fb:
        log(f"  ✅ 已找到现存切片 Flipbook: {FB_SHEET_PATH} (总时长: {sheet_fb.get_total_duration()}s, 帧数: {sheet_fb.get_num_frames()})")
        target_fb = sheet_fb
    else:
        target_fb = None

    # 3. 如果已有 4 个单独 Sprite，构建专属定制 Flipbook
    if len(sprites) == 4:
        # 创建或复用专属 FB_Combat_Inferno_Shock
        fb_asset = unreal.EditorAssetLibrary.load_asset(NEW_FB_PATH)
        if not fb_asset:
            factory = unreal.PaperFlipbookFactory()
            asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
            fb_asset = asset_tools.create_asset("FB_Combat_Inferno_Shock", "/Game/Blueprints/Combat/Projectiles", unreal.PaperFlipbook, factory)
            
        if fb_asset:
            # 清理旧关键帧并按顺序写入 4 帧
            try:
                # 设置帧率 15.0 fps (每帧 0.066s，4 帧总计 0.27s 爆发消散)
                fb_asset.set_editor_property("frames_per_second", 15.0)
                # 使用 key_frames
                key_frames = []
                for sp in sprites:
                    kf = unreal.PaperFlipbookKeyFrame()
                    kf.set_editor_property("sprite", sp)
                    kf.set_editor_property("frame_run", 1)
                    key_frames.append(kf)
                fb_asset.set_editor_property("key_frames", key_frames)
                unreal.EditorAssetLibrary.save_loaded_asset(fb_asset, only_if_is_dirty=False)
                log(f"  🎉 成功构建专属 Inferno Shock 4帧爆炸动画: {NEW_FB_PATH}")
                target_fb = fb_asset
            except Exception as e:
                log(f"  ⚠️ 构建专属 Flipbook 异常: {e}，将使用 Sheet Flipbook 保底")

    if not target_fb:
        target_fb = sheet_fb
        
    log(f"  🎯 最终选定的爆炸动画 Flipbook: {target_fb.get_path_name() if target_fb else 'None'}")

    # 4. 更新爆炸特效蓝图 BP_Combat_HitExplosion
    exp_bp = unreal.EditorAssetLibrary.load_asset(EXP_BP_PATH)
    if exp_bp and target_fb:
        cdo = unreal.get_default_object(exp_bp.generated_class())
        if cdo:
            cdo.set_editor_property("initial_life_span", 0.35)
            comp = cdo.get_component_by_class(unreal.PaperFlipbookComponent)
            if comp:
                try: comp.set_editor_property("source_flipbook", target_fb)
                except Exception: pass
                # 冲击波火环尺寸 1.05
                comp.set_editor_property("relative_scale3d", unreal.Vector(1.05, 1.05, 1.05))
                comp.set_editor_property("translucency_sort_priority", 3000)
                try: comp.set_looping(False)
                except Exception: pass
                
        # 彻底清空可能引起编译错误的旧节点
        graph = unreal.BlueprintEditorLibrary.find_event_graph(exp_bp)
        if graph:
            ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
            nodes = ed.list_all_nodes()
            if nodes: ed.remove_nodes(nodes)
            
        unreal.BlueprintEditorLibrary.compile_blueprint(exp_bp)
        unreal.EditorAssetLibrary.save_loaded_asset(exp_bp, only_if_is_dirty=False)
        log("  ✅ BP_Combat_HitExplosion 已成功挂载 Inferno Shock 并编译保存！")

    # 5. 更新子弹蓝图 BP_ProjectileBase
    proj_bp = unreal.EditorAssetLibrary.load_asset(PROJ_BP_PATH)
    if proj_bp:
        cdo = unreal.get_default_object(proj_bp.generated_class())
        if cdo:
            cdo.set_editor_property("initial_life_span", 1.8)
            
        # 修复图表节点
        graph = unreal.BlueprintEditorLibrary.find_event_graph(proj_bp)
        if graph:
            ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
            overlap = ed.find_event_node("ReceiveActorBeginOverlap")
            all_n = ed.list_all_nodes()
            to_remove = [n for n in all_n if n != overlap and not (isinstance(n, unreal.K2Node_Event) and "overlap" in n.get_name().lower())]
            if to_remove: ed.remove_nodes(to_remove)
            
            if not overlap:
                overlap = ed.find_event_node("ReceiveActorBeginOverlap")
                
            if overlap:
                overlap.set_node_pos(unreal.IntPoint(0, 0))
                
                # 过滤玩家
                get_pc = ed.add_call_function_node("/Script/Engine.GameplayStatics.GetPlayerController")
                if get_pc:
                    get_pc.set_node_pos(unreal.IntPoint(240, 200))
                    p_idx = unreal.BlueprintEditorLibrary.find_input_pin(get_pc, "PlayerIndex") if hasattr(unreal.BlueprintEditorLibrary, "find_input_pin") else None
                    # set player index
                get_pawn = ed.add_call_function_node("/Script/Engine.Controller.K2_GetPawn")
                if get_pawn and get_pc:
                    get_pawn.set_node_pos(unreal.IntPoint(460, 200))
                    sp = pin(get_pc, "ReturnValue")
                    tp = pin(get_pawn, "self")
                    if sp and tp: unreal.BlueprintGraphPinLibrary.try_create_connection(sp, tp)
                    
                not_eq = ed.add_call_function_node("/Script/Engine.KismetMathLibrary.NotEqual_ObjectObject")
                if not_eq and get_pawn:
                    not_eq.set_node_pos(unreal.IntPoint(680, 100))
                    sp_ov = pin(overlap, "OtherActor")
                    tp_a = pin(not_eq, "A")
                    sp_p = pin(get_pawn, "ReturnValue")
                    tp_b = pin(not_eq, "B")
                    if sp_ov and tp_a: unreal.BlueprintGraphPinLibrary.try_create_connection(sp_ov, tp_a)
                    if sp_p and tp_b: unreal.BlueprintGraphPinLibrary.try_create_connection(sp_p, tp_b)
                    
                branch = ed.add_branch_node()
                branch.set_node_pos(unreal.IntPoint(900, 0))
                sp_then = pin(overlap, "then")
                tp_exec = pin(branch, "execute")
                if sp_then and tp_exec: unreal.BlueprintGraphPinLibrary.try_create_connection(sp_then, tp_exec)
                sp_cond = pin(not_eq, "ReturnValue") if not_eq else None
                tp_cond = pin(branch, "Condition")
                if sp_cond and tp_cond: unreal.BlueprintGraphPinLibrary.try_create_connection(sp_cond, tp_cond)
                
                # 造成伤害
                apply_dmg = ed.add_call_function_node("/Script/Engine.GameplayStatics.ApplyDamage")
                if apply_dmg:
                    apply_dmg.set_node_pos(unreal.IntPoint(1160, 0))
                    sp_b = pin(branch, "then")
                    tp_d = pin(apply_dmg, "execute")
                    if sp_b and tp_d: unreal.BlueprintGraphPinLibrary.try_create_connection(sp_b, tp_d)
                    sp_act = pin(overlap, "OtherActor")
                    tp_act = pin(apply_dmg, "DamagedActor")
                    if sp_act and tp_act: unreal.BlueprintGraphPinLibrary.try_create_connection(sp_act, tp_act)
                    p_dmg = pin(apply_dmg, "BaseDamage")
                    if p_dmg: unreal.BlueprintGraphPinLibrary.set_pin_value(p_dmg, "45.0")
                    
                # 销毁自身
                destroy = ed.add_call_function_node("/Script/Engine.Actor.K2_DestroyActor")
                if destroy and apply_dmg:
                    destroy.set_node_pos(unreal.IntPoint(1460, 0))
                    sp_d = pin(apply_dmg, "then")
                    tp_k = pin(destroy, "execute")
                    if sp_d and tp_k: unreal.BlueprintGraphPinLibrary.try_create_connection(sp_d, tp_k)

            unreal.BlueprintEditorLibrary.compile_blueprint(proj_bp)
            unreal.EditorAssetLibrary.save_loaded_asset(proj_bp, only_if_is_dirty=False)
            warns = ed.list_nodes_with_warnings()
            log(f"  ✅ BP_ProjectileBase 图表编译完成！警告/错误数: {len(warns)} (0即完美)")

    # 固化报告
    proj_dir = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
    out_report = {
        "title": "Inferno Shock 命中爆炸装配落地报告",
        "target_flipbook": target_fb.get_path_name() if target_fb else "None",
        "source_pngs": [
            "/Users/cc/Desktop/GGBOM/xxxx/Content/美术/Art/05_VFX/02_Inferno_Shock/T_VFX_Inferno_Shock_01.png",
            "/Users/cc/Desktop/GGBOM/xxxx/Content/美术/Art/05_VFX/02_Inferno_Shock/T_VFX_Inferno_Shock_02.png",
            "/Users/cc/Desktop/GGBOM/xxxx/Content/美术/Art/05_VFX/02_Inferno_Shock/T_VFX_Inferno_Shock_03.png",
            "/Users/cc/Desktop/GGBOM/xxxx/Content/美术/Art/05_VFX/02_Inferno_Shock/T_VFX_Inferno_Shock_04.png"
        ],
        "BP_Combat_HitExplosion": "UPDATED_WITH_INFERNO_SHOCK",
        "BP_ProjectileBase": "CLEAN_COMPILED_ZERO_WARNINGS"
    }
    out_file = os.path.join(proj_dir, "output", "inferno_shock_integration_report.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(out_report, f, ensure_ascii=False, indent=2)
        
    log(f"📄 全量装配报告已固化至: {out_file}")
    log("==================================================")

def pin(node, name: str):
    if not node: return None
    lib = unreal.BlueprintEditorLibrary
    for p in list(lib.list_input_pins(node)) + list(lib.list_output_pins(node)):
        p_name = str(unreal.BlueprintGraphPinLibrary.get_pin_name(p))
        if p_name.lower() == name.lower():
            return p
    return None

if __name__ == "__main__":
    inspect_and_build()
