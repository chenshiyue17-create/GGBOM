# -*- coding: utf-8 -*-
import unreal

GEN = "/Game/GGBOM"
MAP_PATH = f"{GEN}/Maps/MAP_GGBOM_Main"

world = unreal.EditorLoadingAndSavingUtils.load_map(MAP_PATH)
out_f = "/Users/cc/Desktop/GGBOM/xxxx/ground_truth_coords.txt"
lines = []

lines.append("=== GROUND TRUTH INSPECTION ===")
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    lbl = a.get_actor_label()
    loc = a.get_actor_location()
    rot = a.get_actor_rotation()
    sc = a.get_actor_scale3d()
    # 打印相机、玩家生成点、掩体、UI
    if any(k in lbl.lower() for k in ["camera", "player", "cover", "sp_", "tire", "road", "ground", "boss"]):
        lines.append(f"{lbl:30} | Loc: ({loc.x:7.1f}, {loc.y:7.1f}, {loc.z:7.1f}) | Rot: ({rot.pitch:5.1f}, {rot.yaw:5.1f}, {rot.roll:5.1f}) | Scale: ({sc.x:.2f}, {sc.y:.2f}, {sc.z:.2f})")

with open(out_f, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("GROUND_TRUTH_SAVED")
