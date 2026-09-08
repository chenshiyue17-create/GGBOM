# Quick Install / Use

## 方案 A：给 IDE Agent

把整个 ZIP 放入 IDE 工作区并下达：

```text
严格执行 IDE_AGENT_TASK.md。
必须直接修改 UE5 项目中的真实 BP_Player_Medic 与 BP_ProjectileBase，
完成 Compile + Save + 16 项运行方向验收。
不得仅输出脚本或说明。
```

---

## 方案 B：先做安全默认修正

将：

```text
PATCH_COMPONENT_DEFAULTS.py
```

放入：

```text
<Project>/Content/Python/
```

在 UE Python Console 执行：

```python
import os, runpy, unreal
p = os.path.join(
    unreal.Paths.project_content_dir(),
    "Python",
    "PATCH_COMPONENT_DEFAULTS.py"
)
runpy.run_path(p, run_name="__main__")
```

这一步只会：

```text
BulletFlipbook Scale 0.13 -> 0.03
Projectile default Velocity -> 0
Gravity -> 0
尝试关闭 local initial velocity
尝试关闭 rotation follows velocity
Compile
Save
```

它不会替代完整 Blueprint 重构。

---

## 最终验收入口

实施后逐项执行：

```text
ACCEPTANCE_CHECKLIST.md
```

特别关注：

```text
W/A/S/D + 停止后射击
WA/WD/SA/SD + 停止后射击
```
