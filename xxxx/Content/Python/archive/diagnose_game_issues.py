# -*- coding: utf-8 -*-
import unreal
from pathlib import Path

out_lines = []
def plog(msg):
    out_lines.append(str(msg))
    print(msg)
    unreal.log(msg)

plog("================================================================")
plog("🔍 开始诊断游戏两大问题：子弹阻挡角色 & 怪物未加载")
plog("================================================================")

# 1. 检查子弹 BP_ProjectileBase 碰撞配置
proj_bp = unreal.load_asset("/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase")
if proj_bp:
    cdo = unreal.get_default_object(proj_bp.generated_class())
    plog("\n[1] BP_ProjectileBase CDO 组件与碰撞响应:")
    comps = cdo.get_components_by_class(unreal.PrimitiveComponent)
    for c in comps:
        cname = c.get_name()
        profile = c.get_collision_profile_name()
        can_block = c.get_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN)
        overlap_events = c.get_editor_property("generate_overlap_events")
        plog(f"  - 组件: {cname} | Profile: {profile} | 对 Pawn 响应: {can_block} | OverlapEvents: {overlap_events}")

# 2. 检查玩家 BP_Player_Medic 碰撞配置
player_bp = unreal.load_asset("/Game/Blueprints/Player/BP_Player_Medic")
if player_bp:
    cdo = unreal.get_default_object(player_bp.generated_class())
    plog("\n[2] BP_Player_Medic CDO 组件与碰撞响应:")
    comps = cdo.get_components_by_class(unreal.PrimitiveComponent)
    for c in comps:
        cname = c.get_name()
        profile = c.get_collision_profile_name()
        plog(f"  - 组件: {cname} | Profile: {profile}")

# 3. 检查关卡 MAP_GGBOM_Main 中的 Actor
map_path = "/Game/GGBOM/Maps/MAP_GGBOM_Main"
plog(f"\n[3] 检查地图实体: {map_path}")
world = unreal.EditorLoadingAndSavingUtils.load_map(map_path)
actors = unreal.EditorLevelLibrary.get_all_level_actors()
plog(f"  总 Actor 数: {len(actors)}")
wave_mgr = None
for a in actors:
    cname = a.get_class().get_name()
    loc = a.get_actor_location()
    lbl = a.get_actor_label()
    if "Wave" in cname or "Wave" in lbl:
        wave_mgr = a
        plog(f"  ⭐ 找到波次管理器: {lbl} ({cname}) at ({loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f})")
    elif "Enemy" in cname or "Enemy" in lbl:
        plog(f"  👾 地图内已存怪物: {lbl} ({cname}) at ({loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f})")

if not wave_mgr:
    plog("  ❌ 警告: 地图中未找到任何 WaveManager 相关 Actor！")

# 4. 检查 BP_StageWaveManager 蓝图图表
wave_bp = unreal.load_asset("/Game/Blueprints/Stage/BP_StageWaveManager")
if wave_bp:
    graph = unreal.BlueprintEditorLibrary.find_event_graph(wave_bp)
    ed = unreal.BlueprintGraphEditor.get_graph_editor(graph)
    nodes = ed.list_all_nodes()
    plog(f"\n[4] BP_StageWaveManager 节点数: {len(nodes)}")
    for n in nodes:
        plog(f"  - 节点: {n.get_name()} | 标题: {unreal.BlueprintEditorLibrary.get_node_title(n)}")

plog("================================================================")

out_file = Path("/Users/cc/Desktop/GGBOM/xxxx/output/diagnose_output.txt")
out_file.parent.mkdir(parents=True, exist_ok=True)
with open(out_file, "w", encoding="utf-8") as f:
    f.write("\n".join(out_lines))
print(f"Written to {out_file}")
