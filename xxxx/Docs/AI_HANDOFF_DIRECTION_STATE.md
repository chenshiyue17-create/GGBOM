# AI 接力：角色三方向状态修复

更新时间：2026-09-03 01:40 Asia/Shanghai

## 当前结论

`DIRECTION_STATE_STATUS=PASS`，`DIRECTION_STATE_VALIDATION=PASS`，`DIRECTION_RUNTIME_STATUS=PASS`。

这是 UE5.8 纯蓝图实现。角色、子弹、GameMode 已编译保存，方向拓扑的独立检查全部通过。

## 唯一方向模型

| 状态 | 更新时机 | 唯一用途 |
|---|---|---|
| `MoveInput` | 每 Tick 采样 WASD，松键归零；30FPS 下每帧步进 7.5 | 角色移动、Run/Idle 判断 |
| `FacingDirection` | 仅 `MoveInput` 非零时更新 | 角色 Flipbook 方向与水平镜像 |
| `ShotDirection` | 自动射击满足冷却、发射前复制 `FacingDirection` | 本次子弹生成方向 |

自动步枪按 0.18 秒冷却持续射击。子弹生成 Transform 使用 `MakeRotFromX(ShotDirection)`。`BP_ProjectileBase` 在 BeginPlay 读取一次 `GetActorForwardVector` 并写入自身 `ShotDirection`；后续 Tick 只用自己的方向和速度移动，因此玩家转向不会弯折已经发出的子弹。

枪口高度固定为角色原点 `Z+55`（另有 `Y-5` 层级偏移），移动速度按轻量运行固定 30FPS 计算约为 `225 uu/s`。这两个数值的权威源均在 `rebuild_direction_state_v2.py`。

横向世界映射为 A=`X-7.5`、D=`X+7.5`；侧向 Flipbook 镜像与该映射同步，禁止恢复早期 A/D 反向值。

## 修复证据

- 修复前：`output/direction_graph_before_fix.json`
  - 玩家 EventGraph 701 个节点。
  - Tick DeltaSeconds 连接 11 条重复链。
  - 玩家无正式方向成员变量。
- 修复后：`output/direction_graph_after_fix.json`
  - 玩家 EventGraph 14 个节点，单一 Tick 流。
  - 玩家变量包含 `MoveInput`、`FacingDirection`、`ShotDirection`。
  - 子弹 EventGraph 11 个节点，变量包含 `ShotDirection`、`ProjectileSpeed`。
  - 所有图 `compiler_errors=[]`。
- 构建结果：`output/direction_state_rebuild_status.json`
- 独立验证：`output/direction_state_validation.json`
- Standalone 运行报告：`output/direction_runtime_validation.json`
- 自动向上射击截图：`output/direction_runtime_autofire.png`
- 向右移动、侧向朝向、侧向自动射击截图：`output/direction_runtime_after_right_autofire.png`
- 原始资产回滚点：`output/checkpoints/direction_state_rebuild_20260902_2247/`

## 权威入口

仅允许执行：

```text
Content/Python/rebuild_direction_state_v2.py
```

以下历史文件只作为兼容入口保留，其 `__main__` 已转发到权威入口，禁止恢复旧实现：

```text
Content/Python/implement_bullet_direction_fullfix.py
Content/Python/build_full_player_animation_suite.py
```

运行后必须再执行：

```text
Content/Python/audit_direction_graph.py
Tools/validate_direction_state.py
```

## UE5.8 已知限制

当前版本在刚重建的玩家 EventGraph 中由 Python 追加 `Multiply_VectorFloat` 会触发 `UBlueprintGraphEditor::AddCallFunctionNode` 崩溃。因此玩家移动使用已归一化 `MoveInput` 直接作为逐帧位移；这不影响三状态分离与射击方向正确性。不要在没有独立副本验证前恢复该乘法节点。

## 后续验收边界

方向系统单项已通过，但不得据此把整个 P02 标记为 PASS。P02 仍需按敌人受击、伤害、死亡、波次、胜负、重开以及最终 PIE/Standalone 实机证据分别验收。
