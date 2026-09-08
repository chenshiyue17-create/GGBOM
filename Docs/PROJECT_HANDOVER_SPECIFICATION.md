> 更新提示（2026-09-08）：本文包含历史架构与验收声明，不能直接作为当前功能PASS。常用入口、跨端配置和运行边界以仓库 README.md、Docs/MULTI_DEVICE_DEVELOPMENT.md、ProjectState/verification.yaml 为准。

# 《GGBOM: 终末医疗兵》完整项目技术交接白皮书
> **Project Handover & Architecture Specification (v2.0)**  
> **文档密级**：内部技术基准  
> **更新时间**：2026-09-06  
> **目标读者**：接手开发工程师、技术美术 (TA)、系统策划、AI 协作 Agent

---

## 📖 目录 (Table of Contents)
1. [项目概况与核心技术栈](#1-项目概况与核心技术栈)
2. [数据驱动架构全景图](#2-数据驱动架构全景图)
3. [工程目录与核心资产索引](#3-工程目录与核心资产索引)
4. [三大核心数据表配置规范](#4-三大核心数据表配置规范)
5. [标准操作流：运行、调试与验收](#5-标准操作流运行调试与验收)
6. [工程稳定性铁律与避坑红线](#6-工程稳定性铁律与避坑红线)
7. [后续里程碑路线图与待办交接](#7-后续里程碑路线图与待办交接)

---

## 1. 项目概况与核心技术栈

* **游戏代号**：`GGBOM` (终末医疗兵 / The Last Medic)
* **游戏类型**：2D 竖屏 Top-Down 俯视角 Roguelike 动作射击
* **引擎环境**：Unreal Engine 5.8 (Mac Apple Silicon arm64 架构)
* **画幅基准**：
  * **设计基准**：$1080 \times 1920$ (9:16 Portrait 竖屏)
  * **轻量预览**：$360 \times 640$ (桌面独立 Standalone 窗口，锁定 30 FPS，秒级极速拉起)
  * **正交相机**：`OrthoWidth = 941.0`，`AspectRatio ≈ 0.5628`（满屏无裁切双层地图）
* **核心技术基调**：
  * **100% 纯蓝图底座**：零 C++ 模块编译依赖，零黑盒第三方插件，彻底杜绝编译链断裂。
  * **100% 外部纯数据驱动**：所有数值（生命、弹道、移速、出怪波次时间轴）全量收敛至 `Content/Data/*.json`，修改数值**零引擎编译、毫秒级热更生效**。

---

## 2. 数据驱动架构全景图

项目彻底废弃了“使用 Python 脚本在无头模式下删改蓝图图表（EventGraph）”的脆弱反模式，建立了严格的三层解耦架构：

```mermaid
flowchart TD
    subgraph 配置层 (Data Tier - 纯JSON配置 / 毫秒级编辑 / 零崩溃)
        D1[Content/Data/DT_Enemies.json<br/>行尸/猎犬/领主 数值与外观]
        D2[Content/Data/DT_WaveProgression.json<br/>40秒出怪时间轴与车道配置]
        D3[Content/Data/DT_Weapons.json<br/>突击步枪/霰弹枪/毒液枪 弹道参数]
    end

    subgraph 逻辑层 (Logic Tier - 蓝图固化为只读稳定底座)
        B1[BP_StageWaveManager<br/>通用波次时钟与出怪调度器]
        B2[BP_Enemy 怪物家族<br/>4向移动与动画骨架 / 碰撞受击扣血]
        B3[BP_ProjectileBase<br/>通用高速直线投射物 / 2.5s自毁]
        B4[BP_Player_Medic<br/>主角 8向数学平滑位移 / 自动射击]
    end

    subgraph 校验与运行时 (Tooling & Runtime Tier)
        T1[tools/validate_data_tables.py<br/>0.03秒离线静态合规校验]
        R1[Tools/launch_lightweight_game.sh<br/>360x640 @ 30FPS 桌面秒级启动]
    end

    D1 -.->|读取数值| B2
    D2 -.->|读取时间轴| B1
    D3 -.->|读取弹道| B3

    T1 -->|毫秒验证| D1 & D2 & D3
    B1 & B2 & B3 & B4 --> R1
```

---

## 3. 工程目录与核心资产索引

### 核心资产树
```text
xxxx/
├── Content/
│   ├── Data/                                       # 全量外部 JSON 数据驱动仓库 (开发修改核心区)
│   │   ├── DT_Enemies.json                         # 怪物体质、移速、掉落、切图
│   │   ├── DT_WaveProgression.json                 # 40秒波次时钟时间轴
│   │   ├── DT_Weapons.json                         # 武器伤害、射频、子弹飞行参数
│   │   ├── DT_Characters.json                      # 玩家基础属性
│   │   ├── DT_HitEffects.json                      # 顿帧、火花与打击反馈
│   │   └── DT_TacticalCards.json                   # 肉鸽卡牌升级池
│   │
│   ├── Blueprints/                                 # 核心玩法只读逻辑蓝图
│   │   ├── Player/BP_Player_Medic                  # 玩家主角
│   │   ├── Characters/Enemies/
│   │   │   ├── BP_Enemy_ZombieWalker               # 4帧单向推进行尸
│   │   │   ├── BP_Enemy_MutantHound                # 变异猎犬寻路追逐
│   │   │   ├── BP_Enemy_VenomShooter               # 远程毒液射手
│   │   │   └── BP_Boss_Overlord                    # 深渊领主 Boss (头顶大血条)
│   │   ├── Combat/Projectiles/BP_ProjectileBase    # 标准子弹投射物
│   │   ├── Pickups/BP_Pickup_ExpGem                # 经验补给宝石
│   │   └── Stage/BP_StageWaveManager               # 关卡波次时钟与出怪调度实体
│   │
│   └── GGBOM/
│       ├── Maps/MAP_GGBOM_Main                     # 主战斗关卡 (净化版，仅留核心实体)
│       └── UI/                                     # UMG 界面控件库
│           ├── WBP_GGBOM_CombatHUD                 # 竖屏主战斗 HUD
│           └── WBP_Boss_OverheadHealthBar          # Boss 头顶血条
│
├── Tools/                                          # 常用自动化与轻量验证工具箱
│   ├── launch_lightweight_game.sh                  # 360x640 独立小窗口启动器
│   ├── verify_playable_game_full.sh                # 自动化阶段截帧验收工具
│   └── exec_pipeline.py                            # 无缓冲无头批处理执行器
│
└── output/                                         # 验收截图与报告输出目录
```

---

## 4. 三大核心数据表配置规范

### 1. 敌人配置表：[`DT_Enemies.json`](file:///Users/cc/Desktop/GGBOM/xxxx/Content/Data/DT_Enemies.json)
| 字段名 | 类型 | 说明与范例 |
| :--- | :--- | :--- |
| `DisplayName` | String | 中文显示名称（如 `"基础感染行尸"`） |
| `MaxHealth` | Number | 最大生命值（如 `65`） |
| `MoveSpeed` | Number | 移动速度（如 `75`） |
| `ContactDamage` | Number | 接触触碰伤害（如 `15`） |
| `ExpGemValue` | Number | 死亡掉落经验值（如 `5`） |
| `Scale` | Number | 精灵缩放比例（如 `0.45`） |
| `Flipbook` | AssetPath | 动作帧动画路径（留空则使用静态 Sprite） |
| `BlueprintClass` | ClassPath | 对应的敌人实体蓝图类路径 |

### 2. 关卡波次时间轴：[`DT_WaveProgression.json`](file:///Users/cc/Desktop/GGBOM/xxxx/Content/Data/DT_WaveProgression.json)
关卡 `Stage_01_Main` 总时长设为 `40` 秒，配置 4 条下压车道 $X \in \{-120, -40, 40, 120\}$：
```json
"Waves": [
  { "TimeOffset": 2,  "LaneIndex": 1, "EnemyType": "Enemy_Zombie_Walker", "Count": 2, "Interval": 1.0 },
  { "TimeOffset": 6,  "LaneIndex": 2, "EnemyType": "Enemy_Zombie_Walker", "Count": 3, "Interval": 0.8 },
  { "TimeOffset": 12, "LaneIndex": 0, "EnemyType": "Enemy_Mutant_Hound",   "Count": 2, "Interval": 0.6 },
  { "TimeOffset": 18, "LaneIndex": 3, "EnemyType": "Enemy_Venom_Shooter",  "Count": 2, "Interval": 1.2 },
  { "TimeOffset": 25, "LaneIndex": 1, "EnemyType": "Enemy_Zombie_Walker", "Count": 4, "Interval": 0.5 },
  { "TimeOffset": 30, "LaneIndex": 2, "EnemyType": "Boss_Overlord",        "Count": 1, "Interval": 0.0, "DangerAlert": true }
]
```

### 3. 武器弹道表：[`DT_Weapons.json`](file:///Users/cc/Desktop/GGBOM/xxxx/Content/Data/DT_Weapons.json)
定义步枪、霰弹枪、毒液发射器的伤害 (`Damage`)、射频 (`FireRate`)、弹道速度 (`ProjectileSpeed`) 与存活周期 (`LifeSpan`)。

---

## 5. 标准操作流：运行、调试与验收

### ① 离线毫秒级校验 (0.03 秒，无引擎依赖)
每次修改任何 JSON 配置后，先运行静态校验工具：
```bash
python3 tools/validate_data_tables.py
```
*自动检查 JSON 语法、时间轴单调性、车道越界及敌人引用一致性，输出 100% PASS 即合规。*

### ② 极速启动独立游戏窗口 (秒级开玩)
```bash
cd /Users/cc/Desktop/GGBOM/xxxx
./Tools/launch_lightweight_game.sh
```
*以 360×640 窗口在桌面拉起 Standalone 游戏，支持按键即开即测：*
* **`A` / `D`**：控制玩家左右防守走位；
* **自动射击**：枪口持续向前方射出动能子弹；
* **关闭窗口**：直接点击红叉关闭或在终端按 `Ctrl+C`。

### ③ 自动化实机分阶段截帧验收
```bash
cd /Users/cc/Desktop/GGBOM/xxxx
./Tools/verify_playable_game_full.sh
```
*自动拉起游戏并在 8s (开局)、16s (行尸下压)、24s (猎犬交火) 抓取 3 张实机截图存入 `output/`。*

---

## 6. 工程稳定性铁律与避坑红线

> ⚠️ **以下规则由多次严重事故总结沉淀，严禁违反！**

1. **红线一：严禁在无头 Python 中动态删改已有蓝图的 EventGraph 节点**：
   * 在已包含继承层级的复杂 Actor（如 Character）上调用 `remove_nodes` 和 `add_call_function_node`，因缺乏 Slate 编辑器上下文，会触发底层 C++ 野指针崩溃（`SIGSEGV 0x0`）。
   * **正解**：蓝图保持固化只读，业务数值与时间轴全量使用 JSON 数据驱动。
2. **红线二：严禁同会话 `delete_asset` 后立即新建同名资产**：
   * 会导致旧 UObject Package 标记 PendingKill 触发 Object.h Line 1899 的断言闪退。
3. **红线三：2D 像素色彩与抗闪烁规范**：
   * 贴图采样必须锁定 `AddressX=TA_Clamp`, `MipGenSettings=TMGS_NoMipmaps`, `Filter=TF_Nearest`；
   * 渲染后处理必须强制关闭 Lumen、AutoExposure 与 TAA 抖动（锁定 1:1 无损直通原画色彩）。
4. **红线四：Pawn 单体防重**：
   * 保证主角 Pawn 内部永久仅有且只有 1 个 `PaperFlipbookComponent` 和 1 个 `Collision` 盒，严禁无条件重复追加组件。

---

## 7. 后续里程碑路线图与待办交接

| 阶段 | 任务目标 | 核心执行事项 | 推荐方式 |
| :--- | :--- | :--- | :--- |
| **Phase 3 细节精细化** | 数值与波次手感调优 | 根据实机体验微调 `DT_Enemies.json` 血量与移速，优化割草快感 | **直接编辑 JSON** |
| **Phase 4** | Boss 领主多阶段机制 | 打通领主半血狂暴、酸液扩散弹幕触发逻辑与顶部大血条分段 | 数据驱动 + 组件挂载 |
| **Phase 5** | 移动端性能与打包发布 | iOS / Android 移动端工程打包配置、30FPS 功耗压测 | Lite Runner |

---
*白皮书制定人：Antigravity Agentic Pair Programmer*  
*如对工程有任何疑问，请优先参考 [`PROJECT_LESSONS_AND_STABILITY_RULES.md`](file:///Users/cc/Desktop/GGBOM/PROJECT_LESSONS_AND_STABILITY_RULES.md) 与 [`xxxx/DEVELOPMENT_LOG.md`](file:///Users/cc/Desktop/GGBOM/xxxx/DEVELOPMENT_LOG.md)。*

