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

| 脚本路径 | 功能说明 | 运行模式 |
|---|---|---|
| `Content/Python/integrate_combat_damage_loop.py` | 验证 5 张核心数据表并注入蓝图默认值 | Headless (NullRHI) |
| `Content/Python/integrate_stage_wave_manager.py` | 构建波次时间轴出怪管理器与推进行尸 | Headless (NullRHI) |
| `Content/Python/integrate_exp_and_card_upgrade.py` | 构建经验掉落与三选一卡牌弹窗 | Headless (NullRHI) |
| `Content/Python/integrate_meta_inventory_and_talents.py` | 构建背包装备仓库与永久天赋树 | Headless (NullRHI) |
| `Content/Python/implement_all_combat_depth.py` | 构建打击感、伤害跳字、主HUD与Boss狂暴弹幕 | Headless (NullRHI) |
| `Tools/launch_lightweight_game.sh` | 360×640 独立小窗口极速游戏启动器 | Standalone Windowed |
| `Tools/verify_all_combat_depth.sh` | 自动化启动独立游戏并截屏验收 | Standalone + Capture |

---

## 💡 核心踩坑与工程经验积累 (Lessons Learned)
1. **UE5.8 纯蓝图变量安全增删**：
   - 向 Blueprint 添加变量时，严禁直接调用不可靠的私有反射 API，应使用 `unreal.BlueprintGraphEditor.get_graph_editor(BPLIB.find_event_graph(bp)).add_member_variable(name, pin_type, default)`；当变量存在时先 `remove_member_variable` 再安全添加，避免类型覆盖异常。
2. **2D 竖屏渲染层级顺序（Translucency Sort Priority）**：
   - 地面背景（-1000） $\to$ 掩体路障（100） $\to$ 推进行尸（350） $\to$ 玩家主角（500） $\to$ 子弹与 Boss 弹幕（1400） $\to$ 经验宝石（1500） $\to$ Boss 领主（2000） $\to$ UMG 头顶血条（3000）。
3. **数据驱动解耦优势**：
   - 武器与子弹一体化后，换武器只需读取 `DT_Weapons.json` 修改贴图与数值，无需派生海量冗余子弹蓝图，极大精简了工程体积与维护成本。

---
*日志编写完成于：2026-09-03 | 编写人：Antigravity Agentic Pair Programmer*
