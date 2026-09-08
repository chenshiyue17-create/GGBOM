# Root Cause Analysis

## 当前脚本中的确定问题

### 1. BulletFlipbook 视觉尺寸过大

当前 `setup_clean_projectile()`：

```python
obj.set_editor_property(
    "relative_scale3d",
    unreal.Vector(0.13, 0.13, 0.13)
)
```

对于普通 AR/SMG 弹丸，0.13 仍然偏大。

修复基准：

```text
Normal bullet visual scale = 0.03
Allowed tuning range       = 0.02 ~ 0.05
Boss projectile            = separate data, not shared normal bullet scale
```

---

## 2. ProjectileMovement 被固定为 +X

当前：

```python
obj.set_editor_property("velocity", unreal.Vector(1.0, 0.0, 0.0))
```

与此同时，玩家脚本依赖 Spawn Actor Rotation 的 Pitch 去重定向 ProjectileMovement。

这是当前方向系统最脆弱的设计点。

### 必须改成

```text
ProjectileMovement.Velocity =
Normalize(ShotDirection) * ProjectileSpeed
```

速度值直接使用世界空间方向。

---

## 3. 停止移动后方向丢失

当前方向判断来自：

```text
raw_x
raw_z
```

方向节点：

```text
is_up_dir
is_down_dir
is_right_dir
```

玩家松开 WASD 后：

```text
raw_x = 0
raw_z = 0
```

因此：

```text
is_up_dir    = false
is_down_dir  = false
is_right_dir = false
```

当前射击分支会进入：

```text
Shoot Side
```

并选择默认侧向值。

这就是“人物停住之后，子弹突然飞错方向”的结构性原因。

### 根治

新增持久变量：

```text
LastAimDirection : Vector
```

只有输入方向非零时才更新。

停止移动绝对不能清零。

---

## 4. 运动和视觉旋转混用

当前方案使用：

```text
Pitch 90
Pitch -90
Pitch 0
Pitch 180
```

来决定实际飞行方向。

但 2D Flipbook 本身也需要旋转。

当前注释写了 Roll 控制贴图，但实际三个 MakeRotator 的 Roll 都是 0。

所以当前实现实际没有建立：

```text
Movement Rotation
!=
Visual Rotation
```

### 正确职责

```text
ProjectileMovement
    → trajectory only

BulletFlipbook
    → visual angle only

Collision
    → collision only
```

三者必须解耦。

---

# 必须删除的旧设计

删除或断开：

```text
Shoot Up
→ Pitch = 90
→ Spawn

Shoot Down
→ Pitch = -90
→ Spawn

Shoot Side
→ Pitch = 0 / 180
→ Spawn
```

禁止继续增加：

```text
Shoot UpRight
Shoot DownRight
Shoot UpLeft
Shoot DownLeft
```

否则会从 3 套分支变成 8 套分支，维护成本和错向概率继续上升。

最终只能保留一个：

```text
FireProjectile(Direction)
```
