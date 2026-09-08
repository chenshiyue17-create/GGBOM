# Direction Model

## 世界坐标约定

当前项目移动代码已经确定：

```text
A = +X
D = -X
W = +Z
S = -Z
Y = 0
```

因此整个战斗系统统一使用：

```text
Direction = Vector(X, 0, Z)
```

---

# LastAimDirection

创建变量：

```text
Name:
LastAimDirection

Type:
Vector

Default:
(0, 0, -1)
```

默认向下，因为当前角色默认 Idle_Down 更符合初始视觉状态。

## 更新规则

```text
RawDirection =
Vector(
    RawX,
    0,
    RawZ
)

If VectorLengthSquared(RawDirection) > 0.0001:

    LastAimDirection =
        Normalize(RawDirection)
```

禁止：

```text
Else
→ Set LastAimDirection = (0,0,0)
```

---

# 8方向标准表

```text
Down:
(0, 0, -1)

Down-Left:
(+0.7071068, 0, -0.7071068)

Left:
(+1, 0, 0)

Up-Left:
(+0.7071068, 0, +0.7071068)

Up:
(0, 0, +1)

Up-Right:
(-0.7071068, 0, +0.7071068)

Right:
(-1, 0, 0)

Down-Right:
(-0.7071068, 0, -0.7071068)
```

斜向必须 Normalize。

错误：

```text
(1,0,1) * 600
```

实际速度长度约 848.5。

正确：

```text
Normalize(1,0,1) * 600
```

速度始终 600。

---

# MuzzleLocation

禁止维护：

```text
Up Muzzle Offset
Down Muzzle Offset
Left Muzzle Offset
Right Muzzle Offset
```

统一：

```text
MuzzleLocation =
ActorLocation
+
LastAimDirection * MuzzleForwardOffset
+
Vector(0,0,MuzzleHeightOffset)
```

建议初始值：

```text
MuzzleForwardOffset = 40
MuzzleHeightOffset  = 0
```

如果人物美术需要统一抬高枪口：

```text
MuzzleHeightOffset = 10 ~ 20
```

不允许方向分支分别写固定 +40/-40。

---

# Auto Aim 兼容

以后改成自动瞄准目标时不需要重写 Projectile。

只替换 ShotDirection 来源：

```text
Delta =
TargetLocation - MuzzleLocation

Delta.Y = 0

ShotDirection =
Normalize(Delta)
```

Projectile 仍然：

```text
Velocity =
ShotDirection * ProjectileSpeed
```

所以：

```text
Manual 8-dir aim
Auto target aim
Boss aiming
Turret aiming
Enemy projectile
```

都可复用同一套 Projectile。
