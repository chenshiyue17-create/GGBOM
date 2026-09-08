# GGBOM 全局 AI 项目治理协议 (GGBOM GLOBAL AI PROJECT GOVERNANCE PROTOCOL)

> **适用范围**：本协议适用于本项目未来的**每一个任务**（包括特性开发、缺陷修复、美术替换、UI调整、玩法修改、数值平衡、关卡场景、代码重构、资产导入、特效动画、性能优化、存档系统、数据配置及工具链开发）。
> **核心铁律**：**严禁将当前用户请求视为孤立修改目标！任何请求都是对整个游戏工程的全局变更。**

---

## 0. 核心原则 (Core Principle)
对每一个任务：
1. **禁止直接修改文件**。
2. **禁止仅检索显然相关的单个蓝图**。
3. **禁止仅为完成眼前请求做局部优化**。
4. **必须先回答 10 大架构问题**：
   - 此请求如何契合完整游戏架构？
   - 消耗/依赖了哪些现有系统？
   - 哪些间接系统可能受到波及？
   - 现有架构是否能安全、正确地支持该变更？
   - 是否会增加架构债务？
   - 是否会产生重复逻辑？
   - 是否会破坏已批准的视觉资产（Hash Lock）？
   - 是否会影响数值平衡与存档？
   - 是否会影响 UI 状态与多状态表现？
   - 是否会影响其他内容实例？

---

## 1. 优先加载全局项目真源 (Load Global Project State First)
每次任务前必须读取机器权威状态文件：
- `ProjectState/`: `architecture.yaml`, `systems.yaml`, `capabilities.yaml`, `features.yaml`, `dependencies.yaml`, `debt.yaml`, `roadmap.yaml`, `art_registry.yaml`, `visual_baseline.yaml`, `visual_review.yaml`, `visual_completeness.yaml`
- `GameDomain/`: `game_systems.yaml`, `attributes.yaml`, `damage_model.yaml`, `combat_model.yaml`, `weapon_model.yaml`, `projectile_model.yaml`, `enemy_model.yaml`, `boss_model.yaml`, `ability_model.yaml`, `status_effects.yaml`, `upgrade_model.yaml`, `progression_model.yaml`, `drop_model.yaml`, `scene_model.yaml`, `save_model.yaml`, `ui_state_model.yaml`
- 架构 ADR 与变更集（Change Sets）。

---

## 2. 全局影响矩阵 (Global Impact Matrix)
每个任务必须对以下所有领域给出明确状态（`DIRECT_CHANGE`, `INDIRECT_IMPACT`, `REUSE`, `SYSTEM_EXTENSION`, `REFACTOR_REQUIRED`, `BLOCKED`, `NO_IMPACT` 并附带理由）：
`PRODUCT RULES`, `GAME LOOP`, `PLAYER`, `ATTRIBUTES`, `HEALTH`, `DAMAGE`, `COMBAT`, `WEAPON`, `PROJECTILE`, `ABILITY`, `STATUS EFFECT`, `ENEMY`, `BOSS`, `AI`, `UPGRADE`, `PROGRESSION / XP`, `DROP / REWARD`, `ECONOMY`, `SCENE`, `ENCOUNTER`, `SPAWN`, `CAMERA`, `COLLISION / PHYSICS`, `INPUT`, `SAVE / LOAD`, `DATA / DEFINITIONS`, `UI`, `VIEWMODEL`, `PRESENTATION`, `ANIMATION`, `ART`, `VFX`, `AUDIO`, `ASSET REGISTRY`, `VISUAL BASELINE`, `PERFORMANCE`, `ANDROID / PLATFORM`, `TESTS`, `ARCHITECTURE`, `TECH DEBT`。

---

## 3. 全局架构决策 (Global Architecture Decision)
每个任务必须确定一个决策分类：
`REUSE`, `CONTENT_CHANGE`, `SYSTEM_EXTENSION`, `REFACTOR_FIRST`, `PRESENTATION_ONLY`, `DATA_ONLY`, `BUG_FIX_WITHIN_CONTRACT`, `BLOCKED_BY_DEPENDENCY`, `BLOCKED_BY_ART`, `BLOCKED_BY_ARCHITECTURE`。

---

## 4. 架构债务防线与能力复用
- 严查 `debt.yaml`：`HIGH` 债务必须在涉及前解决；`CRITICAL` 债务阻断该系统的新开发。
- 检索 `capabilities.yaml`：坚决复用通用能力，严禁针对特定 ID 编写硬编码特异逻辑（禁止 `if WeaponID == Plasma`, `if EnemyName == Hound` 等）。

---

## 5. 跨域契约与职责所有权
- **系统职责严禁越界**：UI 仅负责显示，ViewModel 负责适配，Presentation 负责音画，Weapon 负责执行，Projectile 负责飞行，Damage 负责结算。
- **全局属性管线**：Base ➔ Character Mod ➔ Equip Mod ➔ Upgrade Mod ➔ Buff/Debuff ➔ Difficulty ➔ Final Value。
- **全局伤害管线**：DamageSource ➔ DamageRequest ➔ Attacker Attributes ➔ Modifiers ➔ Crit ➔ Defense ➔ Status ➔ Final Damage ➔ DamageResult ➔ Health。

---

## 6. 美术资产锁与 Feature 完整性门禁
- 任何未经授权修改 Approved 资产行为触发 `VISUAL_LOCK_VIOLATION`。
- 缺少 Mandatory 美术时标记 `BLOCKED_BY_ART`。
- 任务完成不代表 Feature 完成，必须严格重新计算 17 维完整性状态。

---

## 7. 变更集与边界控制 (Change Sets & Boundaries)
- 每次任务在 `Changes/CHG-XXXX-task-name/` 创建完整变更集描述。
- 严格划定 `ALLOWED_TO_MODIFY` 与 `FORBIDDEN_TO_MODIFY`。
- 严禁范围蔓延（No Scope Creep）。

---

## 8. 标准任务完成汇报结构 (Required Final Response Structure)
每个任务结束时必须严格按照以下结构输出报告：
```text
TASK: ...
ARCHITECTURE DECISION: ...
GLOBAL IMPACT MATRIX: ...
REUSED CAPABILITIES: ...
NEW CAPABILITIES: ...
ARCHITECTURE DEBT: ...
VISUAL IMPACT: ...
FILES / ASSETS MODIFIED: ...
FORBIDDEN MODIFICATIONS: 0 / N
LOCAL TEST: ...
CROSS-SYSTEM REGRESSION: ...
VISUAL REVIEW: ...
PROJECT STATE UPDATE: ...
AFFECTED FEATURE COMPLETENESS: ...
REMAINING BLOCKERS: ...
FINAL RESULT: PASS / FAIL / BLOCKED
```

---

## 9. 蓝图逻辑修改 H5 可视化审核铁律 (Mandatory H5 Blueprint Visual Audit)
1. **全覆盖范围**：对任何蓝图资产（`.uasset` / `.umap`）、事件图表（EventGraph）、函数图表（Function Graph）、引脚连线、变量默认值、节点新增或重构的修改，**必须同步生成或更新 1:1 虚幻引擎原生风格的交互式 H5 可视化审核页面**（`Docs/blueprint_audit.html`）。
2. **中文本地化要求**：H5 页面内所有节点名称、副标题、输入引脚、输出引脚、默认值标签、注释框（Comment Box）必须采用 100% 地道规范的虚幻引擎官方简体中文。
3. **交互与验收门禁**：H5 必须支持节点自由拖动、贝塞尔连线实时联动重绘、平移缩放视口、属性检查，并由 AI 自动在本地浏览器中打开供用户审核签署。未提供 H5 审核页面或未经用户审核的蓝图修改，一律不得判定为交付完成。
