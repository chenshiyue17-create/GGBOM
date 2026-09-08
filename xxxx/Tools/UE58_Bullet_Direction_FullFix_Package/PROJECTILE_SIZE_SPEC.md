# Projectile Size Specification

## 普通子弹视觉规格

目标不是固定 UE Scale，而是固定“屏幕相对视觉尺寸”。

### 普通 AR / SMG

```text
子弹可见长度：
角色身体宽度的 8% ~ 15%

子弹可见厚度：
角色身体宽度的 2% ~ 5%
```

默认起点：

```text
BulletFlipbook RelativeScale3D
= (0.03,0.03,0.03)
```

允许微调：

```text
0.02 ~ 0.05
```

不要重新回到：

```text
0.13
```

除非原素材本身尺寸极小。

---

# 分类尺寸

```text
AR:
0.025 ~ 0.035

SMG:
0.020 ~ 0.030

Sniper:
0.030 ~ 0.045

Shotgun pellet:
0.018 ~ 0.028

Grenade:
0.050 ~ 0.080

Boss normal projectile:
按独立数据配置，不复用普通弹视觉 Scale
```

这些是初始调参区间，不是强制最终值。

---

# Collision

普通高速子弹：

```text
Sphere Radius:
6 ~ 12 UU
```

必须独立于 Flipbook Scale。

---

# Debug Validation

临时开启：

```text
Show Collision
```

检查：

1. 碰撞球中心是否与视觉弹体中心一致。
2. 碰撞球不能达到视觉长度的数倍。
3. 高速弹不能因为视觉缩小而缩小 Collision 到几乎无法命中。
