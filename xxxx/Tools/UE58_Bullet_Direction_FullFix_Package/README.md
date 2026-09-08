# UE5.8 子弹尺寸 + 方向错乱完整修复包

适用当前项目：

```text
Player:
 /Game/Blueprints/Player/BP_Player_Medic

Projectile:
 /Game/Blueprints/Combat/Projectiles/BP_ProjectileBase
```

本包针对当前脚本中的两个实际问题：

1. BulletFlipbook 默认 Scale=0.13，普通子弹视觉过大。
2. ProjectileMovement 默认 Velocity=(1,0,0)，同时玩家端又用 Pitch 90/-90/0/180 去决定弹道，导致“运动方向”和“视觉朝向”耦合。
3. 射击方向直接读取当前 raw_x/raw_z；角色停止后两个值归零，射击分支会退化到固定侧向。
4. 当前注释声称 Roll 用于贴图朝向，但实际 MakeRotator 中 Roll 均为 0。

## 最终架构

```text
Input / Target
      ↓
ShotDirection (X,0,Z)
      ↓
Normalize
      ↓
LastAimDirection
      ↓
Spawn at MuzzleLocation
      ↓
BP_ProjectileBase.InitializeProjectile(Direction, Speed)
      ↓
ProjectileMovement.Velocity = Direction * Speed
```

视觉独立：

```text
Velocity / Direction
      ↓
Atan2(Z, X)
      ↓
VisualAngle + BulletVisualAngleOffset
      ↓
BulletFlipbook.RelativeRotation
```

### 关键原则

- Actor Rotation 不再决定实际弹道。
- ProjectileMovement 的世界 Velocity 决定实际弹道。
- BulletFlipbook Rotation 只决定视觉。
- 普通子弹视觉 Scale 默认从 0.13 降到 0.03。
- Collision 不跟着视觉缩放。
- 对角方向必须归一化，避免斜向速度比直线快。
- 停止移动时必须保留 LastAimDirection。
- 当前项目世界平面固定为 X-Z，Y=0。

## 文件说明

```text
README.md
ROOT_CAUSE_ANALYSIS.md
DIRECTION_MODEL.md
BLUEPRINT_REWRITE_SPEC.md
PROJECTILE_SIZE_SPEC.md
IDE_AGENT_TASK.md
IMPLEMENTATION_ORDER.md
ACCEPTANCE_CHECKLIST.md
DIRECTION_TABLE.csv
BULLET_FIX_CONTRACT.json
PATCH_COMPONENT_DEFAULTS.py
ORIGINAL_CURRENT_SCRIPT.py
```

## 首选实施方式

把整个 ZIP 给 IDE Agent，并让它先执行：

```text
IDE_AGENT_TASK.md
```

不要只运行 PATCH_COMPONENT_DEFAULTS.py 后就报告“修复完成”。
该 Python 文件只负责安全修正 Projectile 默认组件参数；真正的根治必须完成 Blueprint 数据流重写。
