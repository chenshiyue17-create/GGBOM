# 《GGBOM: 终末医疗兵》全量美术资产与视觉生产状态审计报告 (Art Audit)

> **审计执行阶段**：Phase 0-B — Comprehensive Art / Visual Production Audit  
> **审计范围**：UE5.8 Content 全量资产目录 ([`/Game/P01`](file:///Users/cc/Desktop/GGBOM/xxxx/Content/P01), [`/Game/GGBOM`](file:///Users/cc/Desktop/GGBOM/xxxx/Content/GGBOM), [`/Game/Blueprints`](file:///Users/cc/Desktop/GGBOM/xxxx/Content/Blueprints)) 与源切片目录 ([`Content/美术/`](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术))  
> **资产总览**：
> - 引擎已导入 `.uasset` 资产：**`2384` 个**（`/Game/P01/Imported/Content/Asset/Art` 下分类导入包含 `2080` 个 Texture2D / PaperSprite / PaperFlipbook）
> - 原始源文件：**`949` 个 PNG**（`801` 个标准化高精资产 + `148` 个历史散装单图）
> **审计原则**：**拒绝 AI 擅自决定 APPROVED！** 严禁以代码编译成功或文件存在代替视觉完成；未获明确人工批准的资产一律标记为 `CANDIDATE`、`PLACEHOLDER`、`LEGACY` 或 `UNKNOWN`。  
> **审计日期**：2026-09-03  

---

## 核心技术问题专项解答 (Mandatory Technical Inquiries)

### Q1: 项目里实际有哪些 Muzzle VFX 出膛火花？
- **真实存在**：全项目仅有 **`01_KineticPistol` 拥有专用 Muzzle 资产**：
  - UE 路径：[`/Game/GGBOM/Art/Sprites/Weapons/SP_Bullet_KP_01_Muzzle.uasset`](file:///Users/cc/Desktop/GGBOM/xxxx/Content/GGBOM/Art/Sprites/Weapons/SP_Bullet_KP_01_Muzzle.uasset) 与 [`/Game/P01/Imported/Content/Asset/Art/03_Weapons/01_KineticPistol/T_Bullet_KineticPistol_01_Muzzle.uasset`](file:///Users/cc/Desktop/GGBOM/xxxx/Content/P01/Imported/Content/Asset/Art/03_Weapons/01_KineticPistol/T_Bullet_KineticPistol_01_Muzzle.uasset)。
- **缺失现状**：其余 9 把武器（AR01, Shotgun, LaserRail, Flame, Cryo, Plasma, Tesla, BioAcid, Rocket）在美术库中**均没有直接命名的独立 Muzzle 切片**，需通过通用特效（如 `VFX_Spark`、`VFX_Flame`）复用或下发 Art Work Order 补齐！

### Q2: 项目里实际有哪些 Impact VFX 命中爆炸？
- **专用命中资产**：`01_KineticPistol` 拥有 [`SP_Bullet_KP_03_Impact.uasset`](file:///Users/cc/Desktop/GGBOM/xxxx/Content/GGBOM/Art/Sprites/Weapons/SP_Bullet_KP_03_Impact.uasset)。
- **通用特效库**：`/Game/P01/Imported/Content/Asset/Art/05_VFX` 下导入了 **18 组高品质连续动画 Flipbook**（共 214 个 uasset），包含：烈焰 (`VFX_Flame`)、爆炸 (`VFX_Explosion`)、机械火花 (`VFX_Spark`)、强酸腐蚀 (`VFX_Acid`)、高压电弧 (`VFX_Lightning`)、冰霜冻结 (`VFX_Frost`)、护盾 (`VFX_Shield`)、治疗 (`VFX_Heal`) 等。

### Q3: 哪些可以复用？哪些属于 UNKNOWN？哪些当前 Runtime 根本没引用？
- **可复用**：`VFX_Spark` 可作为 AR01/SMG 的 Impact VFX；`VFX_Flame` 可作为 Shotgun/FlameThrower 的 Impact VFX；`VFX_Acid` 可作为 BioAcid 的 Impact VFX；`VFX_Lightning` 可作为 Tesla 的 Impact VFX。
- **属于 UNKNOWN**：`Content/美术/` 根目录下的 148 个早期散装切片（如 `icon_01.png`、`temp_btn.png`），无前缀且用途未标明。
- **当前 Runtime 根本没引用**：全部 18 组 VFX Flipbook（214 个 uasset）在当前关卡 `MAP_GGBOM_Main` 中**调用率为 0%**；18 种僵尸怪物与 Boss 的 983 个动画资产**调用率为 0%**。

### Q4: AR01 当前实际引用的是哪个 Projectile Asset？
- 当前 `rebuild_direction_state_v2.py` 与 `BP_Player_Medic` 实际生成的是 [`/Game/GGBOM/Art/Sprites/SP_Bullet_Flight.SP_Bullet_Flight`](file:///Users/cc/Desktop/GGBOM/xxxx/Content/GGBOM/Art/Sprites/SP_Bullet_Flight.uasset)（单帧 Sprite）。

### Q5: SG01 当前实际引用的是哪个 Projectile Asset？
- 蓝图 `BP_Bullet_Buckshot` 静态默认值引用的是早期单帧占位切片 [`/Game/GGBOM/Art/Sprites/SP_Bullet.SP_Bullet`](file:///Users/cc/Desktop/GGBOM/xxxx/Content/GGBOM/Art/Sprites/SP_Bullet.uasset)，尚未连接 P01 中候选的 `T_Bullet_Buckshot_02_Flight`。

### Q6: KineticPistol 当前实际引用的是哪个 Projectile Asset？
- 引用的是专用的 [`/Game/GGBOM/Art/Sprites/Weapons/SP_Bullet_KP_02_Flight.SP_Bullet_KP_02_Flight`](file:///Users/cc/Desktop/GGBOM/xxxx/Content/GGBOM/Art/Sprites/Weapons/SP_Bullet_KP_02_Flight.uasset)（已校准 0.25 缩放）。

---

## A. 角色资产审计 (Character Assets)

### 玩家医疗兵 (`01_Player` — 110 PNG / 308 UAssets)
- **`APPROVED` 资产**（经实机验证且哈希锁定）：
  - `CHR.MEDIC.IDLE.SOUTH` ([`T_Player_Medic_Idle_Dir_01_Down_Sheet.png`](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/Art/01_Player/01_Idle_Run/Dir_01_Down/Idle/T_Player_Medic_Idle_Dir_01_Down_Sheet.png)) — MD5: `ca0cbfae259b15b3eec6a9881881dc67`
  - `CHR.MEDIC.RUN.SOUTH` ([`T_Player_Medic_Run_Dir_01_Down_Sheet.png`](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/Art/01_Player/01_Idle_Run/Dir_01_Down/Run/T_Player_Medic_Run_Dir_01_Down_Sheet.png)) — MD5: `a8d626359e80fcfcbe2001eb709214ca`
- **`CANDIDATE` 资产**：8 方向 Attack, Hurt, Dead, Reload, Roll 4 帧连续动画 Flipbook（已在 P01 生成，待在 `L_Preview_Character` 中离线走查并由人工批准）。

---

## B. 敌人资产审计 (Enemy Assets — 351 PNG / 983 UAssets)

- **18 种行尸小怪 (`Zombie_01` ~ `18`)**：每种 4 帧连续动画，P01 已就绪，状态：**`CANDIDATE / UNUSED`**。
- **变异猎犬 (`Hound`)**：4 方向 x 5 动作共 80 帧，状态：**`CANDIDATE / UNUSED`**。
- **毒液射手 (`Spitter`)**：4 方向 x 5 动作 + 毒液弹道，状态：**`CANDIDATE / UNUSED`**。
- **终极领主 Boss (`Lord`)**：4 方向 6 动作 + 10 技能大招，状态：**`CANDIDATE / UNUSED`**。

---

## C. 武器资产审计 (Weapon Assets — 40 PNG / 110 UAssets)

- 10 种武器的外观切片均已导入 P01，状态为 **`CANDIDATE`**。

---

## D. 投射物资产审计 (Projectile Assets)

- **`PROJ.KINETIC_PISTOL.FLIGHT`**：已校准 0.25 缩放（32x32 uu），状态：**`APPROVED`** (MD5: `90cf9ab400a40d5885c34cbfe0e28590`)。
- 其余 9 种武器的飞行子弹切片状态均为 **`CANDIDATE`**。

---

## E. 视觉特效审计 (VFX — 77 PNG / 214 UAssets)

- 18 组特效 Flipbook 完整就绪，目前主关卡调用率为 0%，状态均为 **`CANDIDATE / UNUSED`**。

---

## F. UI 资产审计 (UI — 73 PNG / 141 UAssets)

- 包含 5 组 UI 组件切片。当前主 HUD 使用了临时纯色条，状态为 **`CANDIDATE`**（包含 2 个 Placeholder 占位切片）。

---

## G. 环境与关卡资产审计 (Environment — 10 PNG / 20 UAssets)

- `MAP.STAGE00.GROUND` ([`T_Map_Stage00_Ground.png`](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/Art/08_Maps/Stage00_Start/T_Map_Stage00_Ground.png)) — **`APPROVED`** (MD5: `96a7dd7a531e28509c2565bc97f52554`)
- `MAP.STAGE00.OVERHEAD` ([`T_Map_Stage00_Overhead.png`](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/Art/08_Maps/Stage00_Start/T_Map_Stage00_Overhead.png)) — **`APPROVED`** (MD5: `e2a4be6cebc1bf75fa227cf43534d0b0`)

---

## H. 占位资产清单 (Placeholder Inventory)

1. `SP_ZombieWalker`（单帧静态图，占位替代 4 帧连续动画）
2. `SP_Hound`（单帧静态图，占位替代 4 帧连续动画）
3. `SP_Boss`（单帧静态图，占位替代 4 向领主动画）
4. `SP_HUD_HP_Fill` / `SP_HUD_HP_Bg`（临时红绿纯色色块）
5. `SP_Tactical_Barricade`（无损坏 3 态单图）

---

## I. 未知语义资产清单 (Unknown Asset Inventory)

- 根目录 `Content/美术/` 下的 148 个无统一前缀的散装单图（如 `icon_01.png`, `temp_btn.png`），全部标记为 **`UNKNOWN / LEGACY`**，严禁在运行时静默引用。

---

## J. 损坏与重复资产清单 (Broken / Duplicate Assets)

- `GGBOM/Art/Sprites/SP_Bullet.uasset` 与 `SP_Bullet_Flight.uasset` 重复。
- `90_ARCHIVE_Legacy_WorldSpace_HUD` 目录下的 15 个世界空间 HUD Actor 属于废弃遗留。

---

## K. 缺失美术依赖清单 (Missing Art Dependencies)

1. `Weapon.AR01`：缺失专用 Muzzle VFX 出膛火花（阻断集成：`BLOCKED_BY_ART`）。
2. `Weapon.SG01`：缺失扇形 5 弹丸散射 Muzzle VFX（阻断集成：`BLOCKED_BY_ART`）。
3. `Props.Barricade`：缺失 Damaged (50%) 与 Destroyed (0%) 切片。

---

## L. 视觉技术债务清单 (Visual Debt)

| 债务 ID | 严重程度 | 描述 | 阻断影响 |
| :--- | :--- | :--- | :--- |
| **`VIS-01`** | **HIGH** | 18 组 VFX 资产闲置，开火无枪口火花，命中无爆炸 | 武器无法达成 COMPLETE |
| **`VIS-02`** | **HIGH** | 场景怪物全员使用单帧静态贴图占位 | 敌人系统处于 INCOMPLETE |
| **`VIS-03`** | **MEDIUM** | 可破坏掩体缺少 3 态物理外观联动 | 场景互动表现力缺失 |
| **`VIS-04`** | **MEDIUM** | UMG HUD 缺乏 Mock ViewModel 驱动 | UI 无法独立走查评审 |

---

## M. 推荐锁定资产清单 (Assets Recommended for LOCK)

| 语义 Asset ID | 资产路径 | MD5 锁定哈希 | 锁定理由 |
| :--- | :--- | :--- | :--- |
| `MAP.STAGE00.GROUND` | `美术/Art/08_Maps/Stage00_Start/T_Map_Stage00_Ground.png` | `96a7dd7a531e28509c2565bc97f52554` | 关卡正交地面基石 |
| `MAP.STAGE00.OVERHEAD`| `美术/Art/08_Maps/Stage00_Start/T_Map_Stage00_Overhead.png`| `e2a4be6cebc1bf75fa227cf43534d0b0` | 顶层遮挡透视基石 |
| `CHR.MEDIC.IDLE.SOUTH`| `美术/Art/01_Player/01_Idle_Run/Dir_01_Down/Idle/T_Player_Medic_Idle_Dir_01_Down_Sheet.png` | `ca0cbfae259b15b3eec6a9881881dc67` | 玩家基础朝向动画 |
| `CHR.MEDIC.RUN.SOUTH` | `美术/Art/01_Player/01_Idle_Run/Dir_01_Down/Run/T_Player_Medic_Run_Dir_01_Down_Sheet.png` | `a8d626359e80fcfcbe2001eb709214ca` | 玩家移动朝向动画 |
| `PROJ.KINETIC_PISTOL.FLIGHT` | `美术/Art/03_Weapons/01_KineticPistol/T_Bullet_KineticPistol_02_Flight.png` | `90cf9ab400a40d5885c34cbfe0e28590` | 投射物尺寸标准基线 |
