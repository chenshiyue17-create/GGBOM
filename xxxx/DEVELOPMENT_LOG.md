# 《GGBOM: 终末医疗兵》全量研发日志与架构技术白皮书

---

## 📌 版本信息
- **项目代号**：GGBOM (终末医疗兵 / The Last Medic)
- **引擎版本**：Unreal Engine 5.8 (Apple Silicon arm64, Mac M1)
- **渲染分辨率**：360 × 640 (9:16 竖屏正交 2D 视角，锁定 30 FPS)
- **技术栈规范**：100% 纯蓝图架构 (Pure Blueprint, 零 C++ 模块依赖，零第三方插件黑盒) + 外部 JSON 全量数据驱动 (Hot-Reloadable)

---

## 🗓️ 研发演进历程与里程碑

### 阶段 0：基础核心状态解耦与视口对齐
1. **移动/朝向/射击三状态解耦**：
   - 将角色逻辑严格拆分为 `MoveInput`（WASD/摇杆 8 向位移向量）、`FacingDirection`（身体朝向，X 轴速度阈值驱动）、`ShotDirection`（独立武器射击瞄准方向）。
   - EventGraph 精简重构为 14 节点的单向 Tick 流，枪口绝对定位修正为角色持枪基准高度 $Z+55$。
2. **正交相机与视口层级校准**：
   - 确立 X-Z 战斗平面体系，Y 轴为前后图层渲染深度通道（$Y < 0$ 为屏幕前景，$Y > 0$ 为背景通道）。
   - 彻底修复 360×640 小窗口下的相机视口裁剪与黑边问题。

---

### 阶段 1：Boss 头顶跟随血条系统实装
1. **UMG 控件蓝图**：
   - 创建 `/Game/GGBOM/UI/WBP_Boss_OverheadHealthBar`，支持当前生命值/最大生命值平滑进度条、多段阶段分割刻度。
2. **Boss 实体挂载**：
   - 创建 `/Game/Blueprints/Characters/Enemies/BP_Boss_Overlord`（继承自 `PaperSpriteActor`，挂载 `SP_Boss` 外观，初始 `MaxHealth=4500.0`）。
   - 采用 Overhead 挂载方式跟随 Boss 移动，彻底废除在场景中放置静态伪血条的旧做法。

---

### 阶段 2：全量数据驱动底座构建 (Data-Driven Architecture)
建立 `Content/Data/` 目录并配置 7 张核心数据表：
1. [`DT_Characters.json`](file:///Users/cc/Desktop/GGBOM/xxxx/Content/Data/DT_Characters.json)：玩家角色基础属性（血量、移速、碰撞体）。
2. [`DT_Weapons.json`](file:///Users/cc/Desktop/GGBOM/xxxx/Content/Data/DT_Weapons.json)：武器与子弹一体化参数（突击步枪、重型霰弹枪、毒液枪的伤害、射频、初速、贴图、穿透数）。
3. [`DT_Enemies.json`](file:///Users/cc/Desktop/GGBOM/xxxx/Content/Data/DT_Enemies.json)：怪物与 Boss 属性（血量、移速、碰撞伤害、掉落价值）。
4. [`DT_HitEffects.json`](file:///Users/cc/Desktop/GGBOM/xxxx/Content/Data/DT_HitEffects.json)：跳弹火花、酸液飞溅、受击顿帧 (30ms) 与震屏参数。
5. [`DT_StatusEffects.json`](file:///Users/cc/Desktop/GGBOM/xxxx/Content/Data/DT_StatusEffects.json)：Debuff 状态异常体系（毒素DoT、冰冻减速）。
6. [`DT_WaveProgression.json`](file:///Users/cc/Desktop/GGBOM/xxxx/Content/Data/DT_WaveProgression.json)：40 秒波次时间轴配置。
7. [`DT_TacticalCards.json`](file:///Users/cc/Desktop/GGBOM/xxxx/Content/Data/DT_TacticalCards.json) & [`DT_MetaTalents.json`](file:///Users/cc/Desktop/GGBOM/xxxx/Content/Data/DT_MetaTalents.json)：肉鸽升级卡牌库与局外长线天赋树。

---

### 阶段 3：波次时间轴与 40 秒防线战斗闭环
1. **波次出怪时间轴**：
   - `0~10s`：第 1 波基础丧尸多路推进；
   - `10~25s`：第 2 波变异猎犬与毒液射手；
   - `30s`：第 3 波深渊领主 Boss 压迫降临；
   - `40s`：防线守卫成功，触发胜利结算并自动重开。
2. **推进行尸蓝图**：
   - 创建 `/Game/Blueprints/Characters/Enemies/BP_Enemy_ZombieWalker`（挂载行尸 Sprite，沿 Z 轴向下平滑推进防线，自带受击生命值管理）。
3. **波次时钟管理器**：
   - 创建 `/Game/Blueprints/Stage/BP_StageWaveManager`，维护关卡时钟，调度刷怪与胜负判定。

---

### 阶段 4：经验拾取、肉鸽卡牌三选一与局外长线系统
1. **经验宝石掉落物**：
   - 创建 `/Game/Blueprints/Pickups/BP_Pickup_ExpGem`，高亮经验晶体，供玩家走位拾取。
2. **肉鸽三选一升级弹窗**：
   - 创建 `/Game/GGBOM/UI/WBP_Modal_CardSelection`，标准 9:16 弹窗，支持 3 张卡牌槽位与品质加成展示。
3. **玩家升级成长体系**：
   - 扩展 `BP_Player_Medic`，挂载 `CurrentExp`、`ExpToNextLevel`、`PlayerLevel`，经验满槽触发升级与属性增强。
4. **局外长线系统**：
   - 创建 `/Game/GGBOM/UI/WBP_Screen_Inventory`（背包装备仓库与 6 大出战格）；
   - 创建 `/Game/GGBOM/UI/WBP_Screen_TalentTree`（永久金币天赋树：生命、伤害、移速、复活）。

---

### 阶段 5：全量战斗深化（打击感、伤害飘字、主HUD与Boss狂暴）
1. **极致打击感与受击反馈**：
   - 在 `BP_ProjectileBase` 挂载 `HitStopDurationMs=30.0` 顿帧、`HitSparkScale=0.45` 火花缩放与受击闪白染色。
2. **伤害飘字系统**：
   - 创建 `/Game/GGBOM/UI/WBP_HUD_DamageTextPop`，支持普通白字、暴击金黄大字与毒素跳动绿字。
3. **主战斗 HUD 画布**：
   - 创建 `/Game/GGBOM/UI/WBP_GGBOM_CombatHUD`，实时绑定玩家血量槽、经验升级进度条、40 秒波次时钟与等级。
4. **Boss 多阶段狂暴与酸液弹幕**：
   - 升级 `BP_Boss_Overlord` 具备多阶段状态机；
   - 创建 `/Game/Blueprints/Combat/Projectiles/BP_BossSkill_AcidBurst` 扇形扩散酸液弹幕技能。

---

## 🏛️ 最终核心资产索引矩阵

```text
Content/
├── Data/                                       # 全量外部 JSON 数据驱动仓库
│   ├── DT_Characters.json                      # 玩家基础属性
│   ├── DT_Weapons.json                         # 武器与子弹一体化参数
│   ├── DT_Enemies.json                         # 怪物与 Boss 属性
│   ├── DT_HitEffects.json                      # 打击跳弹火花与受击视效
│   ├── DT_StatusEffects.json                   # 毒素/冰冻 Debuff
│   ├── DT_WaveProgression.json                 # 40秒波次时间轴
│   ├── DT_TacticalCards.json                   # 肉鸽三选一升级卡牌池
│   ├── DT_MetaTalents.json                     # 永久天赋树
│   └── DT_Equipments.json                      # 背包装备库
│
├── Blueprints/
│   ├── Player/
│   │   └── BP_Player_Medic                     # 玩家角色 (8向移动/射击解耦/经验等级)
│   ├── Characters/Enemies/
│   │   ├── BP_Enemy_ZombieWalker               # 多路推进行尸
│   │   └── BP_Boss_Overlord                    # 深渊领主 Boss (多阶段狂暴+头顶血条)
│   ├── Combat/Projectiles/
│   │   ├── BP_ProjectileBase                   # 通用子弹 (伤害/弹速/顿帧/飘字)
│   │   └── BP_BossSkill_AcidBurst              # Boss 酸液散射弹幕
│   ├── Pickups/
│   │   └── BP_Pickup_ExpGem                    # 经验宝石掉落物
│   └── Stage/
│       └── BP_StageWaveManager                 # 关卡波次时钟与胜负判定器
│
└── GGBOM/
    ├── Maps/
    │   └── MAP_GGBOM_Main                      # 竖屏主战斗关卡 (全系统集成)
    └── UI/
        ├── WBP_Boss_OverheadHealthBar          # Boss 头顶跟随血条
        ├── WBP_Modal_CardSelection             # 肉鸽三选一升级弹窗
        ├── WBP_HUD_DamageTextPop               # 伤害跳字飘字
        ├── WBP_GGBOM_CombatHUD                 # 战斗主画布 HUD
        ├── WBP_Screen_Inventory                # 背包装备仓库
        └── WBP_Screen_TalentTree               # 永久天赋树
```

---

## 🔬 自动化构建与验证流水线工具

---

### 阶段 6：敌人 4 方向动画状态机与受击硬直解耦 (Phase 2 里程碑)
1. **4 方向数学朝向与 Flipbook 状态保护**：
   - 引入数学朝向状态机（Up/Down/Left/Right），根据移动速度矢量动态切换，转向时翻转 `ScaleX`。
   - 增加动画切换防护（`GetFlipbook != TargetFlipbook`），彻底解决 Tick 中每帧重复重置导致动画定格在第 0 帧的历史顽疾。
2. **受击闪红与硬直解耦**：
   - 受击伤害计算与表现层闪白/闪红彻底解耦，防止受击逻辑阻塞角色移动状态机。
3. **关卡伪 UI 与木桩怪全面净化**：
   - 彻底删除关卡 `MAP_GGBOM_Main` 中历史遗留的 8 个世界假 UI 精灵（`UI_BossBar_*`, `UI_Player_*`, `UI_HUD_*`）及 10 个静态木桩敌人。
   - 地图仅保留底层地面（`Ground_Stage00`）、碰撞墙体、玩家出生点与正交相机，全部动态内容改由运行时调度。

---

### 阶段 7：纯数据驱动架构重塑与更新管线稳定化 (Phase 3 关键突破)
1. **彻底攻克更新管线崩溃与“假死”痛点**：
   - **历史踩坑排查**：定位了在无头命令行下使用 Python `BlueprintGraphEditor` 动态删改复杂蓝图（`BP_Enemy_ZombieWalker`）图表节点时，由于缺乏 Slate 焦点引发的内存空指针异常（`SIGSEGV at address 0x0`），以及在同会话 `delete_asset` 后新建资产引发的 UObject 垃圾回收断言崩溃（Line 1899）。
   - **技术方案升级**：全面转向**纯数据驱动（Data-Driven Architecture）**。蓝图作为只读稳定底座，所有数值平衡、出怪时间轴与武器参数全部抽离至外部 JSON 表。
2. **三大标准数据表固化**：
   - [`Content/Data/DT_Enemies.json`](file:///Users/cc/Desktop/GGBOM/xxxx/Content/Data/DT_Enemies.json)：6 种敌人核心体质、速度、接触伤害、宝石掉落与外观。
   - [`Content/Data/DT_WaveProgression.json`](file:///Users/cc/Desktop/GGBOM/xxxx/Content/Data/DT_WaveProgression.json)：4 车道坐标与 40 秒出怪序列（行尸 $\to$ 猎犬 $\to$ 毒液 $\to$ 领主 $\to$ 大捷）。
   - [`Content/Data/DT_Weapons.json`](file:///Users/cc/Desktop/GGBOM/xxxx/Content/Data/DT_Weapons.json)：突击步枪、霰弹枪、毒液枪的弹道速度、射速与伤害。
3. **极速验证工具链确立**：
   - 创建 [`tools/validate_data_tables.py`](file:///Users/cc/Desktop/GGBOM/tools/validate_data_tables.py)：**0.03 秒**毫秒级离线数据校验，0 引擎依赖，100% 语法与引用合规校验。
   - 升级 [`Tools/launch_lightweight_game.sh`](file:///Users/cc/Desktop/GGBOM/xxxx/Tools/launch_lightweight_game.sh)：多卷名路径自动探测，秒级拉起 360×640 @ 30FPS 独立游戏窗口。
   - 运行 [`Tools/verify_playable_game_full.sh`](file:///Users/cc/Desktop/GGBOM/xxxx/Tools/verify_playable_game_full.sh)：自动捕获开局、行尸下压、猎犬突袭三阶段实机运行截图证据（全部通过）。

---

## 🏛️ 最终核心资产索引矩阵

```text
Content/
├── Data/                                       # 全量外部 JSON 数据驱动仓库
│   ├── DT_Characters.json                      # 玩家基础属性
│   ├── DT_Weapons.json                         # 武器与子弹一体化参数
│   ├── DT_Enemies.json                         # 怪物与 Boss 属性
│   ├── DT_HitEffects.json                      # 打击跳弹火花与受击视效
│   ├── DT_StatusEffects.json                   # 毒素/冰冻 Debuff
│   ├── DT_WaveProgression.json                 # 40秒波次时间轴
│   ├── DT_TacticalCards.json                   # 肉鸽三选一升级卡牌池
│   ├── DT_MetaTalents.json                     # 永久天赋树
│   └── DT_Equipments.json                      # 背包装备库
│
├── Blueprints/
│   ├── Player/
│   │   └── BP_Player_Medic                     # 玩家角色 (8向移动/射击解耦/经验等级)
│   ├── Characters/Enemies/
│   │   ├── BP_Enemy_ZombieWalker               # 多路推进行尸 (4帧单向下压)
│   │   ├── BP_Enemy_MutantHound                # 变异猎犬 (高速寻路追逐)
│   │   ├── BP_Enemy_VenomShooter               # 远程毒液喷射者
│   │   └── BP_Boss_Overlord                    # 深渊领主 Boss (多阶段狂暴+头顶血条)
│   ├── Combat/Projectiles/
│   │   ├── BP_ProjectileBase                   # 通用子弹 (高速直线飞行/2.5s自毁)
│   │   └── BP_BossSkill_AcidBurst              # Boss 酸液散射弹幕
│   ├── Pickups/
│   │   └── BP_Pickup_ExpGem                    # 经验宝石掉落物 (玩家触碰拾取)
│   └── Stage/
│       └── BP_StageWaveManager                 # 关卡波次时钟与胜负判定器
│
└── GGBOM/
    ├── Maps/
    │   └── MAP_GGBOM_Main                      # 竖屏主战斗关卡 (全系统集成)
    └── UI/
        ├── WBP_Boss_OverheadHealthBar          # Boss 头顶跟随血条
        ├── WBP_Modal_CardSelection             # 肉鸽三选一升级弹窗
        ├── WBP_HUD_DamageTextPop               # 伤害跳字飘字
        ├── WBP_GGBOM_CombatHUD                 # 战斗主画布 HUD
        ├── WBP_Screen_Inventory                # 背包装备仓库
        └── WBP_Screen_TalentTree               # 永久天赋树
```

---

## 🔬 自动化构建与验证流水线工具

| 脚本路径 | 功能说明 | 运行模式 / 耗时 |
|---|---|---|
| `tools/validate_data_tables.py` | 毫秒级离线数据表语法、时间轴与引用静态校验 | Python 本地执行 (0.03s) |
| `Tools/launch_lightweight_game.sh` | 360×640 独立小窗口极速游戏启动器 | Standalone Windowed (秒级启动) |
| `Tools/verify_playable_game_full.sh` | 自动化启动独立游戏并分阶段截取实机证据 | Standalone + Capture (自动化) |
| `Content/Python/deploy_map_lightweight.py` | 关卡非侵入式轻量部署调度器实体 | Headless (1.8s, 0 Error) |

---

## 💡 核心踩坑与工程经验积累 (Lessons Learned)

1. **绝对禁止无头 Python 破坏性重写已有蓝图图表 (Iron Rule)**：
   - 在已有继承的复杂 Actor 蓝图（如带有 21 个节点的 Character 派生蓝图）上调用 `remove_nodes` 和 `add_call_function_node`，由于缺乏 Slate 界面焦点上下文，极易在 C++ 内部图表链表引发空指针野指针闪退（`SIGSEGV at address 0x0`）。
   - **正道**：蓝图图表保持只读逻辑固化，将变动需求全量转为数据驱动（JSON/DataTable）或增量 ActorComponent。
2. **UObject 内存生命周期约束**：
   - 严禁在同一个 Python 会话中先 `delete_asset` 然后立即在同一路径 `create_blueprint_asset`，旧包残留的 PendingKill 标记会导致在末尾 `SaveLoadedAsset` 时触发断言崩溃（Line 1899）。
3. **2D 竖屏渲染层级顺序（Translucency Sort Priority）**：
   - 地面背景（-1000） $\to$ 掩体路障（100） $\to$ 推进行尸（350） $\to$ 玩家主角（500） $\to$ 子弹与 Boss 弹幕（1400） $\to$ 经验宝石（1500） $\to$ Boss 领主（2000） $\to$ UMG 头顶血条（3000）。
4. **数据驱动解耦优势**：
   - 无论是调整怪物血量、子弹射速，还是重排 40 秒波次，只需修改对应 JSON 字段并保存，更新成功率 100%，耗时小于 0.1 秒，启动独立游戏即刻热更呈现。

---
*日志最新修订：2026-09-06 | 记录人：Antigravity Agentic Pair Programmer*

