# Blueprint Rewrite Specification

# A. BP_Player_Medic

路径：

```text
/Game/Blueprints/Player/BP_Player_Medic
```

## A1. Variables

新增：

```text
LastAimDirection      Vector  Default (0,0,-1)
ProjectileSpeed       Float   Default 600
MuzzleForwardOffset   Float   Default 40
MuzzleHeightOffset    Float   Default 0
```

如果武器系统已经有 ProjectileSpeed：

```text
不要创建第二套
直接读取 CurrentWeapon/WeaponData 的最终 ProjectileSpeed
```

---

# A2. Movement Direction Capture

当前已经存在：

```text
raw_x
raw_z
move_vec = MakeVector(raw_x,0,raw_z)
```

在此处增加：

```text
VectorLengthSquared(move_vec)
        ↓
> 0.0001
        ↓
Branch
```

True：

```text
GetSafeNormal(move_vec)
        ↓
Set LastAimDirection
```

False：

```text
不修改 LastAimDirection
```

这一步是停止移动仍能正确射击的关键。

---

# A3. Shooting

删除当前：

```text
br_shoot_up
br_shoot_down
pitch_val_side
rot_up
rot_down
rot_side
trans_up
trans_down
trans_side
spawn_up
spawn_down
spawn_side
```

最终射击只有一条执行链。

## Fire chain

```text
Shooting == true
        ↓
Get LastAimDirection
        ↓
GetSafeNormal
        ↓
Direction
```

计算 Spawn Location：

```text
ActorLocation

Direction * MuzzleForwardOffset

ActorLocation
+
Direction * MuzzleForwardOffset

+
Vector(0,0,MuzzleHeightOffset)
```

生成 Transform：

```text
Location:
MuzzleLocation

Rotation:
(0,0,0)

Scale:
(1,1,1)
```

重要：

```text
Spawn Rotation 不负责弹道。
```

Spawn：

```text
BeginDeferredActorSpawnFromClass
BP_ProjectileBase

↓

对新 Projectile 设置：
TravelDirection
ProjectileSpeed

↓

FinishSpawningActor
```

或者调用：

```text
InitializeProjectile(Direction, ProjectileSpeed)
```

首选后者。

---

# B. BP_ProjectileBase

路径：

```text
/Game/Blueprints/Combat/Projectiles/BP_ProjectileBase
```

## B1. Components

推荐：

```text
SceneRoot
├── SphereCollision
├── BulletFlipbook
└── ProjectileMovement
```

### BulletFlipbook

```text
RelativeScale3D = (0.03,0.03,0.03)
TranslucencySortPriority = 2800
```

### ProjectileMovement

```text
InitialSpeed = 600
MaxSpeed = 600
ProjectileGravityScale = 0
Velocity = (0,0,0)
bInitialVelocityInLocalSpace = false
bRotationFollowsVelocity = false
```

注意：

```text
初始 Velocity 不允许固定 (1,0,0)
```

---

# B2. Variables

新增：

```text
TravelDirection          Vector Default (1,0,0)
ProjectileSpeed          Float  Default 600
BulletVisualAngleOffset  Float  Default 0
```

可选：

```text
bInitialized Boolean
```

---

# B3. InitializeProjectile

Function：

```text
InitializeProjectile
```

Inputs：

```text
Direction Vector
Speed Float
```

逻辑：

```text
SafeDirection =
GetSafeNormal(Direction)

If SafeDirection.IsNearlyZero:
    SafeDirection = (1,0,0)

TravelDirection =
SafeDirection

ProjectileSpeed =
Max(Speed, 1)

ProjectileMovement.InitialSpeed =
ProjectileSpeed

ProjectileMovement.MaxSpeed =
ProjectileSpeed

ProjectileMovement.Velocity =
TravelDirection * ProjectileSpeed

ProjectileMovement.ProjectileGravityScale = 0
```

必须使用世界向量设置 Velocity。

不要使用：

```text
SetVelocityInLocalSpace
```

作为这套方案的主路径，因为本修复目的就是消除 Actor Rotation 对弹道的依赖。

---

# B4. Bullet Visual Rotation

视觉角：

```text
AngleDeg =
RadiansToDegrees(
    Atan2(
        TravelDirection.Z,
        TravelDirection.X
    )
)
```

然后：

```text
VisualAngle =
AngleDeg + BulletVisualAngleOffset
```

在 Paper2D 组件上设置：

```text
BulletFlipbook Relative Rotation
```

具体 Rotator 轴由当前 Paper2D 组件平面决定。

不要通过旋转 Projectile Actor 来适配贴图。

## Visual Offset 校准

如果原始 PNG 默认“弹头朝 +X”：

```text
BulletVisualAngleOffset = 0
```

如果原始 PNG 默认朝 +Z：

```text
BulletVisualAngleOffset = -90
```

只允许修改这个 Offset 校准素材。

禁止为了修贴图重新修改 Velocity。

---

# B5. Lifetime

当前 Delay 约 3.5 秒可以保留。

更推荐：

```text
SetLifeSpan = 3.5
```

无需额外 Tick。

---

# C. Attack Animation Direction

射击动作动画和实际弹道必须使用同一个：

```text
LastAimDirection
```

不能再：

```text
动画看 raw_x/raw_z
子弹看另一套方向变量
```

方向分类建议：

```text
abs(X) > abs(Z)
    → Side
else
    → Up/Down
```

如果后续素材有 5 基础方向：

```text
S / SE / E / NE / N
```

则再做 Angle→DirectionIndex 映射。

Projectile 本身仍然保持连续向量，不离散成 5/8 个物理方向。

---

# D. Collision and Size

BulletFlipbook 缩放绝不能缩小碰撞体。

```text
Visual Scale
!=
Collision Radius
```

建议普通弹：

```text
SphereCollision Radius = 6 ~ 12 UU
```

最终根据敌人碰撞和屏幕比例调整。

如果视觉细但碰撞太大：

```text
会出现“没碰到也中”
```

如果视觉大但碰撞太小：

```text
会出现“穿模不命中”
```

二者必须独立验收。
