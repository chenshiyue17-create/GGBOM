# Implementation Order

## Phase 0 — Backup

备份：

```text
BP_Player_Medic
BP_ProjectileBase
```

不得直接删除当前资产。

---

## Phase 1 — Projectile defaults

先修：

```text
BulletFlipbook Scale:
0.13 → 0.03

ProjectileMovement Velocity:
(1,0,0) → (0,0,0)

Gravity:
0

RotationFollowsVelocity:
false

InitialVelocityInLocalSpace:
false
```

Compile + Save。

---

## Phase 2 — Projectile initialization API

在 BP_ProjectileBase 创建：

```text
TravelDirection
ProjectileSpeed
BulletVisualAngleOffset

InitializeProjectile(Direction, Speed)
```

实现世界 Velocity。

Compile + Save。

---

## Phase 3 — Player persistent aim

在 BP_Player_Medic 创建：

```text
LastAimDirection
```

默认：

```text
(0,0,-1)
```

仅 MoveVector 非零时：

```text
Set LastAimDirection =
Normalize(MoveVector)
```

Compile + Save。

---

## Phase 4 — Delete Pitch branch shooting

删除/断开旧：

```text
Shoot Up
Shoot Down
Shoot Side
```

及其：

```text
Pitch 90
Pitch -90
Pitch 0
Pitch 180
```

---

## Phase 5 — Unified Fire

创建单一：

```text
FireProjectile
```

使用：

```text
LastAimDirection
```

计算 MuzzleLocation，并调用：

```text
Projectile.InitializeProjectile
```

---

## Phase 6 — Visual direction

基于：

```text
Atan2(Z,X)
```

只旋转：

```text
BulletFlipbook
```

调整：

```text
BulletVisualAngleOffset
```

直到视觉弹头与轨迹一致。

---

## Phase 7 — 8-dir test

逐项：

```text
W
WA
A
SA
S
SD
D
WD
```

每个都测试：

```text
移动中射击
停止移动后射击
连续射击
```

---

## Phase 8 — Regression

确认：

```text
角色移动仍正常
角色动画未损坏
子弹不会回到默认侧面
斜向速度不变快
普通子弹视觉尺寸正常
碰撞仍能命中
```
