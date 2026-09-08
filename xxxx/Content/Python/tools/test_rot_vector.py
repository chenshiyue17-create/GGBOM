# -*- coding: utf-8 -*-
import unreal

# 测试 UE 坐标系下，绕各轴旋转对 XZ 屏幕平面的影响
v_forward = unreal.Vector(1.0, 0.0, 0.0) # 世界 +X (右)
v_up = unreal.Vector(0.0, 0.0, 1.0)      # 世界 +Z (上)

# 测试 Pitch(绕Y轴)
# 如果 Pitch=90, 绕 Y 轴旋转
rot_pitch90 = unreal.Rotator(90.0, 0.0, 0.0)
v_p90 = rot_pitch90.rotate_vector(v_forward)

rot_pitch_neg90 = unreal.Rotator(-90.0, 0.0, 0.0)
v_p_neg90 = rot_pitch_neg90.rotate_vector(v_forward)

# 测试 Yaw(绕Z轴)
rot_yaw90 = unreal.Rotator(0.0, 90.0, 0.0)
v_y90 = rot_yaw90.rotate_vector(v_forward)

# 测试 Roll(绕X轴)
rot_roll90 = unreal.Rotator(0.0, 0.0, 90.0)
v_r90 = rot_roll90.rotate_vector(v_up)

res = f"""
v_forward = {v_forward}
rot_pitch90.rotate_vector(v_forward) = {v_p90}
rot_pitch_neg90.rotate_vector(v_forward) = {v_p_neg90}
rot_yaw90.rotate_vector(v_forward) = {v_y90}
rot_roll90.rotate_vector(v_up) = {v_r90}
"""
print(res)
with open("/Users/cc/Desktop/GGBOM/rot_test_result.txt", "w") as f:
    f.write(res)
