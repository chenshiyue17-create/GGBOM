# IDE Agent Task — Bullet Direction Root Fix

## Mission

直接修复项目中真实的：

```text
/Game/Blueprints/Player/BP_Player_Medic
/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase
```

目标：

```text
1. 普通子弹尺寸合理
2. 8方向运动正确
3. 停止移动后仍保持最后射击方向
4. 视觉弹头与真实弹道一致
5. 斜向速度与直向速度一致
6. Actor Rotation 不再决定实际弹道
```

不要只输出说明。
不要只提交 Python 文件。
必须修改真实 Blueprint、Compile、Save、验证。

---

# Existing implementation facts

当前项目移动坐标：

```text
A = +X
D = -X
W = +Z
S = -Z
Y = 0
```

当前错误 Projectile 默认：

```text
BulletFlipbook Scale = 0.13
ProjectileMovement Velocity = (1,0,0)
```

当前错误射击：

```text
Up    -> Pitch 90
Down  -> Pitch -90
Side  -> Pitch 0 / 180
```

必须替换。

---

# Required changes

## BP_Player_Medic

新增/复用：

```text
LastAimDirection Vector Default (0,0,-1)
MuzzleForwardOffset Float Default 40
MuzzleHeightOffset Float Default 0
```

当 MoveVector 非零：

```text
LastAimDirection =
Normalize(MoveVector)
```

MoveVector 为零：

```text
DO NOT overwrite LastAimDirection
```

删除/断开旧的 Pitch 分支 Spawn。

统一：

```text
ShotDirection =
Normalize(LastAimDirection)

MuzzleLocation =
ActorLocation
+
ShotDirection * MuzzleForwardOffset
+
(0,0,MuzzleHeightOffset)

Spawn BP_ProjectileBase

Projectile.InitializeProjectile(
    ShotDirection,
    FinalProjectileSpeed
)
```

如果现有武器数据已经有 FinalProjectileSpeed：

```text
必须复用现有武器数值
不得创建第二套冲突 ProjectileSpeed
```

---

## BP_ProjectileBase

BulletFlipbook：

```text
Scale = 0.03
```

ProjectileMovement：

```text
GravityScale = 0
Initial Velocity = (0,0,0)
InitialVelocityInLocalSpace = false
RotationFollowsVelocity = false
```

新增/复用：

```text
TravelDirection Vector
ProjectileSpeed Float
BulletVisualAngleOffset Float
```

创建：

```text
InitializeProjectile(Direction, Speed)
```

实现：

```text
SafeDirection =
GetSafeNormal(Direction)

Velocity =
SafeDirection * Speed
```

必须设置 ProjectileMovement 世界 Velocity。

### Visual

计算：

```text
Angle =
Degrees(
    Atan2(
        TravelDirection.Z,
        TravelDirection.X
    )
)

VisualAngle =
Angle + BulletVisualAngleOffset
```

只旋转 BulletFlipbook。

不得旋转 Actor 来修素材方向。

---

# Hard forbidden rules

```text
FORBIDDEN:
ProjectileMovement default Velocity = (1,0,0)

FORBIDDEN:
Pitch 90/-90/0/180 determines trajectory

FORBIDDEN:
Actor Rotation determines trajectory

FORBIDDEN:
Clear LastAimDirection when input becomes zero

FORBIDDEN:
Diagonal Direction used without normalization

FORBIDDEN:
BulletFlipbook Scale remains 0.13 for normal bullet

FORBIDDEN:
Visual rotation changes real projectile direction

FORBIDDEN:
Create 8 separate projectile spawn branches

FORBIDDEN:
Report success after only editing Python source
```

---

# Required compile/save evidence

必须提供：

```text
[MODIFIED]
/Game/Blueprints/Player/BP_Player_Medic
/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase

[VARIABLES]
LastAimDirection
TravelDirection
ProjectileSpeed
BulletVisualAngleOffset

[REMOVED OLD LOGIC]
List old Pitch spawn nodes removed/disconnected

[COMPILE]
BP_Player_Medic: PASS/FAIL
BP_ProjectileBase: PASS/FAIL

[SAVE]
Both saved: YES/NO
```

---

# Runtime test matrix

必须实际验证：

```text
W   -> +Z
WA  -> +X +Z normalized
A   -> +X
SA  -> +X -Z normalized
S   -> -Z
SD  -> -X -Z normalized
D   -> -X
WD  -> -X +Z normalized
```

每方向至少验证：

```text
1. while moving
2. after releasing movement key
```

即 16 个方向状态测试。

还必须验证：

```text
Diagonal speed == cardinal speed
Bullet visual angle follows trajectory
Normal bullet not oversized
Owner projectile spawn location correct
```

---

# Failure policy

任何没有实际运行验证的项必须报告：

```text
NOT VERIFIED
```

禁止：

```text
“应该没问题”
“理论上完成”
“代码已生成所以完成”
```

只认可：

```text
asset modified
compiled
saved
runtime behavior observed
```
