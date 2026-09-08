# 《GGBOM: 终末医疗兵》UE5 2D 全量美术资产与【纯蓝图 (100% Blueprint)】开发全景规约白皮书
> **100% Pure Blueprint Implementation Specification for Unreal Engine 5.8+ (Paper2D / PaperZD Pipeline)**
> 
> **核心研发方针**：**全流程 100% 纯蓝图开发 (No C++ / Zero Native Compilation)**。
> 所有游戏逻辑、数据结构 (User Defined Structs)、枚举 (User Defined Enums)、接口 (Blueprint Interfaces)、动画蓝图 (PaperZD AnimBP)、数据表 (DataTables)、组件 (Actor Components)、UI 控件 (UMG Widgets) 与投射物机制均在 UE5 蓝图编辑器内直接构建，确保产物为可直接在引擎中打开、编辑、连线、保存的 `.uasset` 资产。
> 
> **美术资产基准路径**：`xxxx/Content/美术/`（共收录 106 个高分辨率美术资产文件）

---

## 目录 (Table of Contents)

1. [纯蓝图工程架构与核心原则 (Pure Blueprint Principles)](#1-纯蓝图工程架构与核心原则)
2. [蓝图基础设施定义 (Structs / Enums / Interfaces / Components)](#2-蓝图基础设施定义)
   - [2.1 蓝图枚举 (User Defined Enums)](#21-蓝图枚举-user-defined-enums)
   - [2.2 蓝图结构体 (User Defined Structs)](#22-蓝图结构体-user-defined-structs)
   - [2.3 蓝图接口 (Blueprint Interfaces)](#23-蓝图接口-blueprint-interfaces)
   - [2.4 蓝图通用组件体系 (Actor Components)](#24-蓝图通用组件体系-actor-components)
3. [全量 106 个美术资产精细化调用字典 (Asset Breakdown)](#3-全量-106-个美术资产精细化调用字典)
   - [3.1 玩家角色：医疗兵 (Medic - 11张图)](#31-玩家角色医疗兵-medic---11张图)
   - [3.2 敌人系统：小怪-行尸 (Zombie - 9张图)](#32-敌人系统小怪-行尸-zombie---9张图)
   - [3.3 敌人系统：精英-毒液射手 (Venom Shooter - 6张图)](#33-敌人系统精英-毒液射手-venom-shooter---6张图)
   - [3.4 敌人系统：精英-猎犬 (Mutant Hound - 5张图)](#34-敌人系统精英-猎犬-mutant-hound---5张图)
   - [3.5 敌人系统：终极Boss动作表 (Boss Actions - 6张图)](#35-敌人系统终极boss动作表-boss-actions---6张图)
   - [3.6 敌人系统：终极Boss专属技能大招 (Boss Skills - 10张图)](#36-敌人系统终极boss专属技能大招-boss-skills---10张图)
   - [3.7 武器与投射物系统 (Bullets & Projectiles - 10张图)](#37-武器与投射物系统-bullets--projectiles---10张图)
   - [3.8 环境与可破坏道具系统 (Destructible Props - 10张图)](#38-环境与可破坏道具系统-destructible-props---10张图)
   - [3.9 视觉特效系统 (VFX / Particles - 18张图)](#39-视觉特效系统-vfx--particles---18张图)
   - [3.10 卡片构筑系统 (Perk / Upgrade Cards - 6张图)](#310-卡片构筑系统-perk--upgrade-cards---6张图)
   - [3.11 UI 界面交互系统 (UI / UMG Widgets - 5张图)](#311-ui-界面交互系统-ui--umg-widgets---5张图)
   - [3.12 双层关卡地图系统 (Dual-Layer Maps - 10张图)](#312-双层关卡地图系统-dual-layer-maps---10张图)
4. [核心蓝图类继承架构与蓝图连线逻辑 (Blueprint Class Hierarchy & Event Flow)](#4-核心蓝图类继承架构与蓝图连线逻辑)
5. [纯蓝图数据表配置 (DataTables via Blueprint Structs)](#5-纯蓝图数据表配置)
6. [UE5 Editor 纯蓝图自动化切片 Python 工具](#6-ue5-editor-纯蓝图自动化切片-python-工具)
7. [AI 纯蓝图开发 7 阶段落地执行路线图 (AI Blueprint Roadmap)](#7-ai-纯蓝图开发-7-阶段落地执行路线图)

---

## 1. 纯蓝图工程架构与核心原则

### 1.1 纯蓝图开发铁律 (Non-Negotiable Blueprint Rules)
1. **零 C++ 依赖**：严禁创建或修改 `Source/**`、`*.cpp`、`*.h`、`*.Build.cs` 文件；所有业务逻辑均通过可视化蓝图图表 (Event Graph, Construction Script, Functions, Macros) 表达。
2. **真实 `.uasset` 交付**：所有数据模型、节点连线、Pin 引脚、变量默认值必须可直接在 UE5.8 Blueprint Editor 中打开查看与二次编辑。
3. **模块化解耦**：角色移动、生命数值、武器发射、状态效果、卡牌加成全面采用 **Actor Component (蓝图组件)** 架构，确保可在玩家、敌人与 Boss 间高内聚复用。
4. **接口驱动通信 (BPI)**：避免直接 Cast To 具体子类，跨 Actor 伤害传递、交互、掉落触发统一通过 **Blueprint Interface (BPI)** 实现松耦合。

### 1.2 2D 正交与 Y-Sort 深度规则
* **空间坐标系**：`X` (水平左右), `Y` (垂直上下兼深度轴), `Z` (高度/图层轴)
* **蓝图 Tick / 定时器 Y-Sort 逻辑**：
  ```
  Event Tick (或 Event SetActorLocation)
  └──> GetActorLocation (Split Pin)
       └──> Multiply (Location.Y * -0.1f)
            └──> Add (BaseLayerPriority = 500)
                 └──> Set Translucent Sort Priority (Target: PaperSprite/FlipbookComponent)
  ```
* **层级基准常量**：
  - `Ground`: Priority = 0, World Z = 0 (Block All)
  - `Floor VFX / Decal`: Priority = 10, World Z = 2
  - `Props / Pickups`: Priority = 100 ~ 200, World Z = 10
  - `Characters / Enemies`: Priority = 300 ~ 800 (Dynamic Y-Sort), World Z = 20
  - `Projectiles`: Priority = 850, World Z = 40
  - `Air VFX / Explosions`: Priority = 900, World Z = 50
  - `Overhead`: Priority = 1000, World Z = 100 (Dynamic Dither Fade Material)

---

## 2. 蓝图基础设施定义

所有基础设施均存放于 `/Content/Blueprints/Core/Types/` 目录下。

### 2.1 蓝图枚举 (User Defined Enums)

#### 1. `EWeaponType` (武器与弹药类型枚举)
* 存放路径：`/Game/Blueprints/Core/Types/EWeaponType`
* 枚举值：
  - `KineticPistol` (标准动能手枪)
  - `AssaultRifle` (高速突击步枪)
  - `BuckshotShotgun` (重型近战霰弹枪)
  - `BioAcidLauncher` (生化酸液发射器)
  - `ToxicSporeGun` (剧毒孢子分裂枪)
  - `VenomMortar` (毒浆重炮)
  - `IncendiaryRifle` (燃烧烈焰枪)
  - `PlasmaArcBlaster` (高能等离子电弧枪)
  - `MicroMissileLauncher` (微型火箭发射器)
  - `LaserRailgun` (穿甲聚合激光轨道枪)

#### 2. `ECardRarity` (升级卡片稀有度枚举)
* 存放路径：`/Game/Blueprints/Core/Types/ECardRarity`
* 枚举值：`Common` (普通-灰/白), `Rare` (稀有-蓝), `Epic` (史诗-紫), `Legendary` (传说-金)

#### 3. `EEnemyTier` (敌人阶位枚举)
* 存放路径：`/Game/Blueprints/Core/Types/EEnemyTier`
* 枚举值：`Minion_Zombie` (普通小怪行尸), `Elite_VenomShooter` (精英毒液射手), `Elite_Hound` (精英变异猎犬), `Boss_Overlord` (终极领主)

#### 4. `EBossPhase` (Boss 战斗阶段枚举)
* 存放路径：`/Game/Blueprints/Core/Types/EBossPhase`
* 枚举值：`Phase1_Normal` (100%~70% HP), `Phase2_Enraged` (70%~30% HP), `Phase3_Cataclysm` (30%~0% HP), `Phase_Defeated` (领主湮灭)

#### 5. `EPropState` (可破坏道具生命周期状态枚举)
* 存放路径：`/Game/Blueprints/Core/Types/EPropState`
* 枚举值：`Intact` (完好状态-阻挡), `Damaged` (受损状态-冒烟/报警), `Destroyed` (彻底破坏态-掉落物)

---

### 2.2 蓝图结构体 (User Defined Structs)

#### 1. `FWeaponData` (武器与弹道配置结构体)
* 存放路径：`/Game/Blueprints/Core/Types/FWeaponData`
| 字段名 (Variable Name) | 蓝图类型 (Variable Type) | 默认值 | 详细说明 |
| :--- | :--- | :--- | :--- |
| `WeaponID` | `Name` | `WPN_Pistol` | 武器唯一索引 Key |
| `DisplayName` | `Text` | `制式手枪` | UI 显示名称 |
| `WeaponType` | `EWeaponType (Enum)` | `KineticPistol` | 武器类型枚举 |
| `ProjectileClass` | `Class (Subclass of BP_Projectile_Base)` | `BP_Bullet_KineticPistol` | 发射生成的投射物蓝图类 |
| `BaseDamage` | `Float` | `25.0` | 单发弹丸基础伤害 |
| `FireInterval` | `Float` | `0.25` | 射击冷却间隔 (秒) |
| `ProjectilesPerShot` | `Integer` | `1` | 单次开火发射弹丸数 (霰弹/多联) |
| `SpreadAngle` | `Float` | `0.0` | 弹道扇形散射角度 |
| `PierceCount` | `Integer` | `1` | 最大穿透敌人数 (999为无限贯穿) |
| `ProjectileSpeed` | `Float` | `1200.0` | 弹丸飞行初速 (cm/s) |
| `KnockbackForce` | `Float` | `0.0` | 击退冲量 |
| `MuzzleFlipbook` | `Paper Flipbook Object Reference` | `FB_VFX_Muzzle_Flash` | 开火枪口火光动画 |
| `ImpactFlipbook` | `Paper Flipbook Object Reference` | `FB_VFX_Hit_Kinetic` | 命中阻挡物/目标爆破动画 |
| `FireSound` | `Sound Base Object Reference` | `SFX_Pistol_Fire` | 开火音效 |

#### 2. `FCardUpgradeData` (卡牌升级配置结构体)
* 存放路径：`/Game/Blueprints/Core/Types/FCardUpgradeData`
| 字段名 (Variable Name) | 蓝图类型 (Variable Type) | 默认值 | 详细说明 |
| :--- | :--- | :--- | :--- |
| `CardID` | `Name` | `CARD_01` | 卡牌唯一标识 Key |
| `CardTitle` | `Text` | `纳米注射器` | 卡牌界面标题 |
| `CardDescription` | `Text` | `最大生命+25，自愈+1.5HP/s` | 卡牌效果描述文字 |
| `CardArtTexture` | `Texture 2D Object Reference` | `T_Card_NaniteSyringe` | 4:3 对应卡牌原画插画 |
| `Rarity` | `ECardRarity (Enum)` | `Common` | 稀有度枚举 |
| `MaxStackCount` | `Integer` | `3` | 局内最大允许选择/叠加次数 |
| `ModifierTag` | `Gameplay Tag` | `Attribute.Health.MaxHP` | 修改的属性标签 |
| `ModifierValue` | `Float` | `25.0` | 属性修正数值 (正数加成/百分比) |
| `SecondaryModifierTag` | `Gameplay Tag` | `Attribute.Health.Regen` | 次要属性修改标签 |
| `SecondaryModifierValue`| `Float` | `1.5` | 次要属性修正数值 |
| `SpawnCompanionClass` | `Class (Subclass of AActor)` | `None` | (可选) 召唤物/无人机蓝图类 |

#### 3. `FDestructiblePropData` (可破坏道具配置结构体)
* 存放路径：`/Game/Blueprints/Core/Types/FDestructiblePropData`
| 字段名 (Variable Name) | 蓝图类型 (Variable Type) | 默认值 | 详细说明 |
| :--- | :--- | :--- | :--- |
| `PropID` | `Name` | `PROP_ExplosiveBarrel` | 道具唯一标识 |
| `MaxDurability` | `Float` | `40.0` | 破坏所需总生命值 |
| `Sprite_Intact` | `Paper Sprite Object Reference` | `SP_Prop_01_Frame_0` | 完好状态 Sprite |
| `Sprite_Damaged` | `Paper Sprite Object Reference` | `SP_Prop_01_Frame_1` | 受损状态 Sprite |
| `Sprite_Destroyed` | `Paper Sprite Object Reference` | `SP_Prop_01_Frame_2` | 破坏残骸 Sprite |
| `ExplosionRadius` | `Float` | `250.0` | (可选) 破坏爆炸 AOE 范围 |
| `ExplosionDamage` | `Float` | `200.0` | (可选) 破坏爆炸伤害 |
| `ExplosionVFX` | `Paper Flipbook Object Reference` | `FB_VFX_Explosion_Fire` | 爆破动画 |
| `DestroySound` | `Sound Base Object Reference` | `SFX_Barrel_Explode` | 破坏音效 |
| `LootTableID` | `Name` | `DT_Loot_Standard` | 掉落物权重表索引 |

---

### 2.3 蓝图接口 (Blueprint Interfaces)

#### 1. `BPI_CombatInterface` (战斗伤害与受击接口)
* 存放路径：`/Game/Blueprints/Core/Interfaces/BPI_CombatInterface`
* 接口函数：
  - `TakeCombatDamage(float DamageAmount, FGameplayTag DamageTypeTag, AActor* DamageCauser, FVector HitLocation)` -> 返回 `bool bWasKilled`
  - `ApplyKnockback(FVector KnockbackImpulse, float StunDuration)`
  - `ApplyStatusDot(FGameplayTag StatusTag, float Duration, float DamagePerSec)`
  - `HealHealth(float HealAmount, AActor* HealerActor)`

#### 2. `BPI_InteractableInterface` (场景可交互与破坏接口)
* 存放路径：`/Game/Blueprints/Core/Interfaces/BPI_InteractableInterface`
* 接口函数：
  - `InteractWithProp(AActor* InteractorActor)`
  - `TriggerDestruction(AActor* TriggerCauser)`

---

### 2.4 蓝图通用组件体系 (Actor Components)

#### 1. `BPC_HealthComponent` (生命与护盾管理组件)
* 挂载于：`BP_Player_Medic`、所有敌人 `BP_Enemy_*`、Boss `BP_Boss_Overlord` 与破坏道具 `BP_DestructibleProp_Base`
* 关键变量：`CurrentHP (Float)`, `MaxHP (Float)`, `CurrentShield (Float)`, `MaxShield (Float)`, `bIsInvulnerable (Bool)`
* 关键事件分发器 (Event Dispatchers)：`OnHealthChanged`, `OnShieldChanged`, `OnDeath`, `OnDamaged`

#### 2. `BPC_WeaponInventoryComponent` (武器槽与弹幕发射组件)
* 挂载于：`BP_Player_Medic`
* 关键变量：`PrimaryWeaponData (FWeaponData)`, `ActiveModifierTags (GameplayTagContainer)`, `CurrentAmmo (Int)`
* 核心函数：`FireCurrentWeapon(FVector AimDirection)`、`ApplyCardUpgrade(FCardUpgradeData UpgradeData)`

---

## 3. 全量 106 个美术资产精细化调用字典

### 3.1 玩家角色：医疗兵 (Medic - 11张图)
* **资产目录**：[`xxxx/Content/美术/医疗兵/`](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/医疗兵)
* **主蓝图类**：`BP_Player_Medic` (继承自 `APaperZDCharacter` / `ACharacter`)
* **动画蓝图**：`ABP_Player_Medic` (PaperZD 动画蓝图状态机)
* **原图规格**：`1659 × 948` px (1×8 横向条带切片，单帧 `207.375 × 948` px，`Bottom Center` 轴心)

| 序号 | 源文件名 (Clickable Link) | 切割 Sprite 命名 | 目标 Flipbook 资产 | 动作状态名 | FPS | 视觉动作语义与逻辑 | 蓝图 GameplayTag | 关联音效 | 关联触发特效 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 01 | [ChatGPT Image 2026年8月28日 23_26_50 (1).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/医疗兵/ChatGPT%20Image%202026%E5%B9%B48%E6%9C%8828%E6%97%A5%2023_26_50%20%281%29.png) | `SP_Medic_Idle_0~7` | `FB_Medic_Idle` | **Idle (待机警戒)** | 8 | 待机平稳呼吸，双手持枪对准正前方 | `State.Idle` | `None` | `None` |
| 02 | [ChatGPT Image 2026年8月28日 23_26_51 (2).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/医疗兵/ChatGPT%20Image%202026%E5%B9%B48%E6%9C%8828%E6%97%A5%2023_26_51%20%282%29.png) | `SP_Medic_Walk_0~7` | `FB_Medic_Walk` | **Walk/Run (战术移动)** | 12 | 8方向双足快速奔跑，联动移动摇杆输入与脚步音效 | `State.Moving` | `SFX_Footstep_Dirt` | `FB_VFX_Smoke_Dust` |
| 03 | [ChatGPT Image 2026年8月28日 23_26_51 (3).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/医疗兵/ChatGPT%20Image%202026%E5%B9%B48%E6%9C%8828%E6%97%A5%2023_26_51%20%283%29.png) | `SP_Medic_ShootLight_0~7` | `FB_Medic_Shoot_Light` | **Shoot Light (冲锋枪连射)** | 16 | 单手/双手连发点射，枪口火光高频闪烁，产生后坐力晃动 | `Ability.Fire.Primary` | `SFX_Pistol_Fire` | `FB_VFX_Muzzle_Flash` |
| 04 | [ChatGPT Image 2026年8月28日 23_26_52 (4).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/医疗兵/ChatGPT%20Image%202026%E5%B9%B48%E6%9C%8828%E6%97%A5%2023_26_52%20%284%29.png) | `SP_Medic_ShootHeavy_0~7` | `FB_Medic_Shoot_Heavy` | **Shoot Heavy (重火力轰击)** | 14 | 双手握持霰弹枪/生化重炮蓄力并猛烈开火 | `Ability.Fire.Secondary` | `SFX_Shotgun_Blast` | `FB_VFX_Muzzle_Flash` |
| 05 | [ChatGPT Image 2026年8月28日 23_26_53 (5).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/医疗兵/ChatGPT%20Image%202026%E5%B9%B48%E6%9C%8828%E6%97%A5%2023_26_53%20%285%29.png) | `SP_Medic_Deploy_0~7` | `FB_Medic_Deploy_Station` | **Deploy Station (部署医疗站)** | 10 | 下蹲放置战地纳米医疗信标，展开绿色治愈力场 | `Ability.Deploy.HealingStation` | `SFX_Deploy_Device` | `FB_VFX_Nanite_Heal` |
| 06 | [ChatGPT Image 2026年8月28日 23_26_53 (6).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/医疗兵/ChatGPT%20Image%202026%E5%B9%B48%E6%9C%8828%E6%97%A5%2023_26_53%20%286%29.png) | `SP_Medic_Throw_0~7` | `FB_Medic_Throw_Grenade` | **Throw Grenade (投掷毒素手雷)** | 12 | 挥臂投掷酸蚀减速手雷，形成范围爆炸与持续毒潭 | `Ability.Throw.Grenade` | `SFX_Grenade_Throw` | `FB_VFX_Explosion_Fire` |
| 07 | [ChatGPT Image 2026年8月28日 23_26_54 (7).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/医疗兵/ChatGPT%20Image%202026%E5%B9%B48%E6%9C%8828%E6%97%A5%2023_26_54%20%287%29.png) | `SP_Medic_Dash_0~7` | `FB_Medic_Dash_Roll` | **Dash / Roll (战术翻滚)** | 16 | 快速前滚翻躲避弹幕，附带 0.25 秒无敌状态帧 | `Ability.Evade.Roll` | `SFX_Dash_Whoosh` | `FB_VFX_Dash_Ghost` |
| 08 | [ChatGPT Image 2026年8月28日 23_26_55 (8).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/医疗兵/ChatGPT%20Image%202026%E5%B9%B48%E6%9C%8828%E6%97%A5%2023_26_55%20%288%29.png) | `SP_Medic_Hurt_0~7` | `FB_Medic_Hurt` | **Take Damage (受击硬直)** | 12 | 躯干受击后倾晃动，角色材质触发 Flash Red | `State.Hurt` | `SFX_Player_Hurt` | `FB_VFX_Blood_Gore` |
| 09 | [ChatGPT Image 2026年8月28日 23_26_55 (9).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/医疗兵/ChatGPT%20Image%202026%E5%B9%B48%E6%9C%8828%E6%97%A5%2023_26_55%20%289%29.png) | `SP_Medic_Reload_0~7` | `FB_Medic_Reload` | **Reload / Syringe (换弹/自愈注射)** | 10 | 抛出空弹夹换弹或拿出强化纳米自愈针注射 | `Ability.Reload` | `SFX_Syringe_Inject` | `FB_VFX_Nanite_Heal` |
| 10 | [ChatGPT Image 2026年8月28日 23_26_56 (10).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/医疗兵/ChatGPT%20Image%202026%E5%B9%B48%E6%9C%8828%E6%97%A5%2023_26_56%20%2810%29.png) | `SP_Medic_Death_0~7` | `FB_Medic_Death` | **Death (倒地力竭阵亡)** | 10 | 跪地倒伏断气，不循环播放，触发 GameOver 结算面板 | `State.Dead` | `SFX_Player_Death` | `None` |
| 11 | [ChatGPT Image 2026年8月28日 23_32_07.png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/医疗兵/ChatGPT%20Image%202026%E5%B9%B48%E6%9C%8828%E6%97%A5%2023_32_07.png) | `SP_Medic_Revive_0~7` | `FB_Medic_Revive_Buff` | **Revive / Ultimate (战地复苏/终极大招)** | 12 | 原地战吼升起能量光柱，触发保命复活或大招过载 | `Ability.Ultimate` | `SFX_Super_Charge` | `FB_VFX_LevelUp_Beam` |

---

### 3.2 敌人系统：小怪-行尸 (Zombie - 9张图)
* **资产目录**：[`xxxx/Content/美术/敌人/小怪-行尸/`](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/敌人/小怪-行尸)
* **主蓝图类**：`BP_Enemy_Zombie` (继承自 `BP_EnemyBase2D`)
* **动画蓝图**：`ABP_Enemy_Zombie`
* **原图规格**：`1659 × 948` px (1×8 横向条带切片，单帧 `207.375 × 948` px，`Bottom Center` 轴心)
* **纯蓝图属性**：MaxHP = 60, WalkSpeed = 180, ChaseSpeed = 250, AttackDamage = 12, ExpDrop = 10

| 序号 | 源文件名 (Clickable Link) | 切割 Sprite 命名 | 目标 Flipbook 资产 | 动作语义 | FPS | 行为逻辑与战斗表现 | AI 状态标签 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 01 | [ChatGPT Image 2026年8月30日 13_52_19 (1).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/敌人/小怪-行尸/ChatGPT%20Image%202026%E5%B9%B48%E6%9C%8830%E6%97%A5%2013_52_19%20%281%29.png) | `SP_Zombie_WalkA_0~7` | `FB_Zombie_Walk_A` | **Walk A (常态蹒跚巡逻)** | 8 | 双手平伸缓慢游荡寻找目标，移速 180 | `AI.State.Patrol` |
| 02 | [ChatGPT Image 2026年8月30日 13_52_19 (2).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/敌人/小怪-行尸/ChatGPT%20Image%202026%E5%B9%B48%E6%9C%8830%E6%97%A5%2013_52_19%20%282%29.png) | `SP_Zombie_WalkB_0~7` | `FB_Zombie_Walk_B` | **Walk B (狂暴奔跑追逐)** | 11 | 锁定玩家坐标后加速狂奔包围，移速 250 | `AI.State.Chase` |
| 03 | [ChatGPT Image 2026年8月30日 13_52_20 (4).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/敌人/小怪-行尸/ChatGPT%20Image%202026%E5%B9%B48%E6%9C%8830%E6%97%A5%2013_52_20%20%284%29.png) | `SP_Zombie_ClawA_0~7` | `FB_Zombie_Claw_A` | **Claw Attack A (右臂挥抓)** | 12 | 近身单手抓击，攻击距离 55 码，伤害 12 | `AI.Ability.AttackA` |
| 04 | [ChatGPT Image 2026年8月30日 13_52_20 (5).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/敌人/小怪-行尸/ChatGPT%20Image%202026%E5%B9%B48%E6%9C%8830%E6%97%A5%2013_52_20%20%285%29.png) | `SP_Zombie_BiteB_0~7` | `FB_Zombie_Bite_B` | **Bite Attack B (双臂飞扑撕咬)** | 13 | 双手合围扑咬，命中对玩家施加减速 30% 持续 1.5s | `AI.Ability.AttackB` |
| 05 | [ChatGPT Image 2026年8月30日 13_52_20 (6).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/敌人/小怪-行尸/ChatGPT%20Image%202026%E5%B9%B48%E6%9C%8830%E6%97%A5%2013_52_20%20%286%29.png) | `SP_Zombie_Vomit_0~7` | `FB_Zombie_Vomit` | **Vomit (毒素呕吐)** | 10 | 前方扇形喷射酸水，在地面生成持续 3 秒的腐蚀泥滩 | `AI.Ability.Vomit` |
| 06 | [ChatGPT Image 2026年8月30日 13_52_20 (7).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/敌人/小怪-行尸/ChatGPT%20Image%202026%E5%B9%B48%E6%9C%8830%E6%97%A5%2013_52_20%20%287%29.png) | `SP_Zombie_HurtA_0~7` | `FB_Zombie_Hurt_A` | **Hurt A (轻度中弹硬直)** | 12 | 躯干受轻度动能子弹命中晃动 | `AI.State.HurtLight` |
| 07 | [ChatGPT Image 2026年8月30日 13_52_20 (8).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/敌人/小怪-行尸/ChatGPT%20Image%202026%E5%B9%B48%E6%9C%8830%E6%97%A5%2013_52_20%20%288%29.png) | `SP_Zombie_HurtB_0~7` | `FB_Zombie_Hurt_B` | **Hurt B (重创后仰击退)** | 12 | 受霰弹/爆炸冲击后仰并向后击退 60 码 | `AI.State.HurtHeavy` |
| 08 | [ChatGPT Image 2026年8月30日 13_52_20 (9).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/敌人/小怪-行尸/ChatGPT%20Image%202026%E5%B9%B48%E6%9C%8830%E6%97%A5%2013_52_20%20%289%29.png) | `SP_Zombie_DieA_0~7` | `FB_Zombie_Death_A` | **Death A (扑倒断气死亡)** | 10 | 向前扑倒断气，尸体 3 秒后淡出并生成经验晶体 | `AI.State.DeathNormal` |
| 09 | [ChatGPT Image 2026年8月30日 13_52_20 (10).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/敌人/小怪-行尸/ChatGPT%20Image%202026%E5%B9%B48%E6%9C%8830%E6%97%A5%2013_52_20%20%2810%29.png) | `SP_Zombie_DieB_0~7` | `FB_Zombie_Death_B` | **Death B (暴击解体粉碎死亡)** | 12 | 受到过量/暴击伤害时血肉四溅解体死亡 | `AI.State.DeathGore` |

---

### 3.3 敌人系统：精英-毒液射手 (Venom Shooter - 6张图)
* **资产目录**：[`xxxx/Content/美术/敌人/精英-毒液射手/`](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/敌人/精英-毒液射手)
* **主蓝图类**：`BP_Enemy_VenomShooter` (继承自 `BP_EnemyBase2D`)
* **纯蓝图属性**：MaxHP = 380, WalkSpeed = 140, KeepDistance = 650, SingleSpitDamage = 28, PoisonDuration = 4.0s
* **规格构成**：
  - `(1).png`：`2172 × 724` px (3×1 条带，单帧 `724 × 724` px) -> 毒液弹道3态
  - `(2) ~ (6).png`：`1254 × 1254` px (4×4 网格，单帧 `313.5 × 313.5` px，单图 16 帧高清动作)

| 序号 | 源文件名 (Clickable Link) | 切割 Sprite 命名 | 目标 Flipbook/资产 | 功能描述与战斗机制 | 绑定蓝图/状态 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 01 | [ChatGPT Image 2026年9月1日 19_36_11 (1).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/敌人/精英-毒液射手/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2019_36_11%20%281%29.png) | `SP_Venom_Spit_0~2` | `3x1 横向条带` | 毒液弹道3态：[蓄力凝结 -> 旋转飞行 -> 落地酸爆] | `BP_Bullet_BioAcid 投射物渲染` |
| 02 | [ChatGPT Image 2026年9月1日 19_36_12 (2).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/敌人/精英-毒液射手/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2019_36_12%20%282%29.png) | `SP_Venom_Aim_00~15` | `FB_Venom_Aim_Idle` | 瞄准蓄力待机 (锁定玩家坐标，口部毒囊高亮充能发光) | `AI.State.Aiming` |
| 03 | [ChatGPT Image 2026年9月1日 19_36_12 (3).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/敌人/精英-毒液射手/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2019_36_12%20%283%29.png) | `SP_Venom_Single_00~15` | `FB_Venom_Spit_Single` | 单发高压毒液喷射 (高速直线穿透酸液弹，伤害 28) | `AI.Ability.SingleSpit` |
| 04 | [ChatGPT Image 2026年9月1日 19_36_12 (4).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/敌人/精英-毒液射手/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2019_36_12%20%284%29.png) | `SP_Venom_Barrage_00~15` | `FB_Venom_Barrage_Multi` | 三连发/扇形散弹毒雾覆盖 (30° 扇形封锁走位) | `AI.Ability.Barrage` |
| 05 | [ChatGPT Image 2026年9月1日 19_36_13 (5).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/敌人/精英-毒液射手/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2019_36_13%20%285%29.png) | `SP_Venom_Shield_00~15` | `FB_Venom_Hurt_Shield` | 受击抗性硬直与酸蚀毒盾激活 (减免 50% 动能伤害) | `AI.State.HurtShield` |
| 06 | [ChatGPT Image 2026年9月1日 19_36_13 (6).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/敌人/精英-毒液射手/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2019_36_13%20%286%29.png) | `SP_Venom_Death_00~15` | `FB_Venom_Death_Melt` | 酸蚀融化自爆死亡 (原地留下一滩持续 5 秒高危强酸池) | `AI.State.DeathAcidPool` |

---

### 3.4 敌人系统：精英-猎犬 (Mutant Hound - 5张图)
* **资产目录**：[`xxxx/Content/美术/敌人/精英-猎犬/`](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/敌人/精英-猎犬)
* **主蓝图类**：`BP_Enemy_Hound` (突进敏捷精英怪)
* **原图规格**：`1254 × 1254` px (4×4 网格，单帧 `313.5 × 313.5` px，单图 16 帧)
* **纯蓝图属性**：MaxHP = 260, SprintSpeed = 420, PounceDistance = 450, PounceDamage = 35, StunTime = 0.8s

| 序号 | 源文件名 (Clickable Link) | 切割 Sprite 命名 | 目标 Flipbook 资产 | 动作状态名 | FPS | 战斗机制与逻辑 | AI 状态标签 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 01 | [ChatGPT Image 2026年9月1日 19_43_17 (1).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/敌人/精英-猎犬/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2019_43_17%20%281%29.png) | `SP_Hound_Run_00~15` | `FB_Hound_Run` | **Sprinting Chase (极速追猎奔跑)** | 16 | 四足飞奔绕背突袭，移速 420 躲避玩家弹道 | `AI.State.HoundChase` |
| 02 | [ChatGPT Image 2026年9月1日 19_43_17 (2).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/敌人/精英-猎犬/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2019_43_17%20%282%29.png) | `SP_Hound_Pounce_00~15` | `FB_Hound_Pounce` | **Pounce Leap (超远距离飞扑)** | 16 | 蓄力 0.25s 腾空扑向目标点，造成 35 伤害与定身 | `AI.Ability.Pounce` |
| 03 | [ChatGPT Image 2026年9月1日 19_43_18 (3).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/敌人/精英-猎犬/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2019_43_18%20%283%29.png) | `SP_Hound_Bite_00~15` | `FB_Hound_Bite_Combo` | **Frenzy Bite (撕裂连咬)** | 16 | 近身三段连击咬噬，附带流血 Dot | `AI.Ability.FrenzyBite` |
| 04 | [ChatGPT Image 2026年9月1日 19_43_18 (4).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/敌人/精英-猎犬/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2019_43_18%20%284%29.png) | `SP_Hound_Howl_00~15` | `FB_Hound_Howl` | **Blood Howl (嗜血咆哮光环)** | 16 | 仰天长啸，赋予周围 600 码怪物 25% 移速加成 | `AI.Ability.HowlBuff` |
| 05 | [ChatGPT Image 2026年9月1日 19_43_19 (5).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/敌人/精英-猎犬/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2019_43_19%20%285%29.png) | `SP_Hound_Death_00~15` | `FB_Hound_Death` | **Death Roll (侧翻滑行死亡)** | 16 | 高速奔跑惯性侧滑倒地，必定掉落高阶升级晶片 | `AI.State.HoundDeath` |

---

### 3.5 敌人系统：终极Boss动作表 (Boss Actions - 6张图)
* **资产目录**：[`xxxx/Content/美术/敌人/boss/动作/`](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/敌人/boss/动作)
* **主蓝图类**：`BP_Boss_Overlord` (多阶段领主)
* **动画蓝图**：`ABP_Boss_Overlord` (PaperZD 状态机)
* **原图规格**：`1254 × 1254` px (4×4 网格，单帧 `313.5 × 313.5` px，单图 16 帧动作，共 96 帧)
* **纯蓝图属性**：MaxHP = 8000, 胶囊体半径 = 65, 半高 = 110, 阶段状态 = `EBossPhase`

| 序号 | 源文件名 (Clickable Link) | 切割 Sprite 命名 | 目标 Flipbook 资产 | 动作状态名 | FPS | 动作表现与战斗联动 | Boss 状态标签 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 01 | [ChatGPT Image 2026年8月31日 18_34_11 (1).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/敌人/boss/动作/ChatGPT%20Image%202026%E5%B9%B48%E6%9C%8831%E6%97%A5%2018_34_11%20%281%29.png) | `SP_Boss_Idle_00~15` | `FB_Boss_Idle` | **Boss Idle (深渊威慑待机)** | 12 | 庞大生化体呼吸起伏，周身环绕剧毒暗黑粒子 | `Boss.State.Idle` |
| 02 | [ChatGPT Image 2026年8月31日 18_34_11 (2).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/敌人/boss/动作/ChatGPT%20Image%202026%E5%B9%B48%E6%9C%8831%E6%97%A5%2018_34_11%20%282%29.png) | `SP_Boss_Walk_00~15` | `FB_Boss_Walk` | **Boss Stomp Walk (沉重践踏行进)** | 12 | 巨足重踏地面，每一步引发微型震屏与扬尘贴花 | `Boss.State.Walk` |
| 03 | [ChatGPT Image 2026年8月31日 18_34_12 (3).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/敌人/boss/动作/ChatGPT%20Image%202026%E5%B9%B48%E6%9C%8831%E6%97%A5%2018_34_12%20%283%29.png) | `SP_Boss_Slam_00~15` | `FB_Boss_Ground_Slam` | **Ground Slam (双臂重砸震荡)** | 14 | 双拳高举轰砸地表，前方 180° 扇形击碎地面并击飞玩家 | `Boss.Ability.GroundSlam` |
| 04 | [ChatGPT Image 2026年8月31日 18_34_12 (4).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/敌人/boss/动作/ChatGPT%20Image%202026%E5%B9%B48%E6%9C%8831%E6%97%A5%2018_34_12%20%284%29.png) | `SP_Boss_Cleave_00~15` | `FB_Boss_Heavy_Cleave` | **Heavy Cleave (巨臂横扫切割)** | 14 | 巨刃手臂 270° 近身斩击，伤害 120，造成强击退 | `Boss.Ability.Cleave` |
| 05 | [ChatGPT Image 2026年8月31日 18_34_12 (5).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/敌人/boss/动作/ChatGPT%20Image%202026%E5%B9%B48%E6%9C%8831%E6%97%A5%2018_34_12%20%285%29.png) | `SP_Boss_Enrage_00~15` | `FB_Boss_Enrage_Roar` | **Enrage Roar (狂暴转阶段战吼)** | 12 | 进入 Phase 2/3 时的无敌咆哮前摇，震开周围所有目标 | `Boss.State.Enrage` |
| 06 | [ChatGPT Image 2026年8月31日 18_34_13 (6).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/敌人/boss/动作/ChatGPT%20Image%202026%E5%B9%B48%E6%9C%8831%E6%97%A5%2018_34_13%20%286%29.png) | `SP_Boss_Death_00~15` | `FB_Boss_Death_Collapse` | **Epic Death (终极湮灭崩溃)** | 10 | 倒塌碎裂，引发全场能量消散波纹并弹出通关胜利面板 | `Boss.State.Death` |

---

### 3.6 敌人系统：终极Boss专属技能大招 (Boss Skills - 10张图)
* **资产目录**：[`xxxx/Content/美术/敌人/boss/boss技能/`](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/敌人/boss/boss技能)
* **原图规格**：`1659 × 948` px (多帧横向序列)
* **生成机制**：由 `BP_Boss_Overlord` 在技能释放阶段生成对应的技能 Actor (`BP_BossSkill_*`)

| 序号 | 源文件名 (Clickable Link) | 切割 Sprite 命名 | 目标 Flipbook 资产 | 技能名称 | 技能机制与战斗逻辑 | 生成 Actor 蓝图类 | 基础伤害 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 01 | [ChatGPT Image 2026年9月1日 19_57_59 (1).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/敌人/boss/boss技能/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2019_57_59%20%281%29.png) | `SP_BossSkill_01_0~7` | `FB_BossSkill_FlameWave` | **烈焰/毒炎扩散环形冲击波** | Boss 中心向外 360° 扩散环状火圈，翻滚可规避 | `BP_BossSkill_ShockwaveRing` | 80 |
| 02 | [ChatGPT Image 2026年9月1日 19_58_00 (2).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/敌人/boss/boss技能/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2019_58_00%20%282%29.png) | `SP_BossSkill_02_0~7` | `FB_BossSkill_CorrosiveBeam` | **毁灭腐蚀扫射高能光束** | 旋转 180° 的持续能量激光柱，接触造成高频致命伤害 | `BP_BossSkill_LaserBeam` | 150 |
| 03 | [ChatGPT Image 2026年9月1日 19_58_00 (3).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/敌人/boss/boss技能/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2019_58_00%20%283%29.png) | `SP_BossSkill_03_0~7` | `FB_BossSkill_EarthSpikes` | **生化突刺地刺阵列** | 玩家脚下生成红色预警圈，1 秒后巨型尖刺破土突刺 | `BP_BossSkill_SpikeTrap` | 90 |
| 04 | [ChatGPT Image 2026年9月1日 19_58_01 (4).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/敌人/boss/boss技能/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2019_58_01%20%284%29.png) | `SP_BossSkill_04_0~7` | `FB_BossSkill_AcidPool` | **强酸泥沼间歇喷发** | 场地随机出现 6 处沸腾酸池，持续 8 秒灼烧踏入者 | `BP_BossSkill_AcidPool` | 25 |
| 05 | [ChatGPT Image 2026年9月1日 19_58_01 (5).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/敌人/boss/boss技能/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2019_58_01%20%285%29.png) | `SP_BossSkill_05_0~7` | `FB_BossSkill_SporeBomb` | **背部集束高射孢子轰炸** | 向空中发射 8 枚孢子球，随后雨落覆盖战场 | `BP_BossSkill_SporeRain` | 60 |
| 06 | [ChatGPT Image 2026年9月1日 19_58_01 (6).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/敌人/boss/boss技能/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2019_58_01%20%286%29.png) | `SP_BossSkill_06_0~7` | `FB_BossSkill_EggSummon` | **深渊异化虫卵仪式召唤** | 在四角孵化异化虫卵，10 秒不击破将诞生精英怪 | `BP_BossSkill_EggNode` | 0 |
| 07 | [ChatGPT Image 2026年9月1日 19_58_02 (7).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/敌人/boss/boss技能/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2019_58_02%20%287%29.png) | `SP_BossSkill_07_0~7` | `FB_BossSkill_GravityVortex` | **虚空引力黑洞风暴** | 持续吸引全场玩家与投射物至黑洞核心并二次引爆 | `BP_BossSkill_BlackHole` | 110 |
| 08 | [ChatGPT Image 2026年9月1日 19_58_02 (8).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/敌人/boss/boss技能/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2019_58_02%20%288%29.png) | `SP_BossSkill_08_0~7` | `FB_BossSkill_BlightBreath` | **死疫毒雾狂暴吐息** | 正面 60° 扇形超远距离毒雾喷吐，持续 3.5 秒 | `BP_BossSkill_BreathCone` | 45 |
| 09 | [ChatGPT Image 2026年9月1日 19_58_03 (9).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/敌人/boss/boss技能/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2019_58_03%20%289%29.png) | `SP_BossSkill_09_0~7` | `FB_BossSkill_MeteorRain` | **阶段三终极全屏陨星坠落** | 全地图大范围随机落点轰炸，考查玩家极限走位 | `BP_BossSkill_MeteorStrike` | 130 |
| 10 | [ChatGPT Image 2026年9月1日 19_58_03 (10).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/敌人/boss/boss技能/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2019_58_03%20%2810%29.png) | `SP_BossSkill_10_0~7` | `FB_BossSkill_BioShield` | **反物质能量结界护盾** | 无敌护盾，四周生成 3 颗能量供能水晶，破坏水晶破盾 | `BP_BossSkill_ShieldNode` | 0 |

---

### 3.7 武器与投射物系统 (Bullets & Projectiles - 10张图)
* **资产目录**：[`xxxx/Content/美术/子弹/`](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/子弹)
* **统一原图尺寸**：`2172 × 724` px (精确 3×1 横向网格，单帧 `724 × 724` px)
* **三态切片规约**：
  - `Frame 0 (X=0, Y=0, W=724, H=724)` -> `SP_Bullet_xx_Muzzle` (枪口初速/弹头出膛)
  - `Frame 1 (X=724, Y=0, W=724, H=724)` -> `SP_Bullet_xx_Flight` (高速巡航弹道轨迹/旋转飞行帧)
  - `Frame 2 (X=1448, Y=0, W=724, H=724)` -> `SP_Bullet_xx_Impact` (命中目标炸裂消散/破片)
* **投射物基类**：`BP_Projectile_Base` (挂载 `ProjectileMovementComponent`, Collision Sphere)

| 序号 | 源文件名 (Clickable Link) | 投射物蓝图类 | 弹药类型 | 基础伤害 | 飞行速度 (cm/s) | 穿透数 | 击退力 | 弹道特性与附魔机制 | 发射音效 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 01 | [ChatGPT Image 2026年9月1日 20_00_15 (1).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/子弹/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2020_00_15%20%281%29.png) | `BP_Bullet_KineticPistol` | **9mm 标准动能手枪弹** | 25.0 | 1200.0 | 1 | 0.0 | 单发高精度制式手枪弹丸 | `SFX_Pistol_Fire` |
| 02 | [ChatGPT Image 2026年9月1日 20_00_16 (2).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/子弹/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2020_00_16%20%282%29.png) | `BP_Bullet_AssaultRifle` | **5.56mm 高速突击步枪弹** | 18.0 | 1600.0 | 1 | 15.0 | 连射高初速穿甲步枪弹 | `SFX_Rifle_Fire` |
| 03 | [ChatGPT Image 2026年9月1日 20_00_16 (3).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/子弹/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2020_00_16%20%283%29.png) | `BP_Bullet_Buckshot` | **12-Gauge 重型霰弹弹丸** | 14.0 | 1100.0 | 1 | 60.0 | 近战 6 发散射，带极高击退力 | `SFX_Shotgun_Fire` |
| 04 | [ChatGPT Image 2026年9月1日 20_00_17 (4).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/子弹/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2020_00_17%20%284%29.png) | `BP_Bullet_BioAcid` | **Bio-Acid 生化酸液腐蚀弹** | 12.0 | 900.0 | 2 | 0.0 | 附带每秒 8 点毒蚀 Dot (持续 3 秒) | `SFX_Acid_Spit` |
| 05 | [ChatGPT Image 2026年9月1日 20_00_17 (5).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/子弹/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2020_00_17%20%285%29.png) | `BP_Bullet_ToxicSpore` | **Toxic Spore 剧毒孢子分裂弹** | 20.0 | 850.0 | 1 | 0.0 | 命中分裂出 3 颗追踪微型毒胞 | `SFX_Spore_Burst` |
| 06 | [ChatGPT Image 2026年9月1日 20_00_17 (6).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/子弹/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2020_00_17%20%286%29.png) | `BP_Bullet_VenomHeavy` | **Venom Cluster 强酸毒浆重炮** | 45.0 | 750.0 | 1 | 0.0 | 触地生成 120 码范围减速酸液池 | `SFX_Venom_Blast` |
| 07 | [ChatGPT Image 2026年9月1日 20_00_18 (7).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/子弹/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2020_00_18%20%287%29.png) | `BP_Bullet_Incendiary` | **Incendiary 燃烧穿甲烈焰弹** | 35.0 | 1300.0 | 3 | 0.0 | 穿透 3 名敌人并附加燃烧点燃效果 | `SFX_Flame_Shot` |
| 08 | [ChatGPT Image 2026年9月1日 20_00_18 (8).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/子弹/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2020_00_18%20%288%29.png) | `BP_Bullet_PlasmaArc` | **Plasma Arc Bolt 高能电弧弹** | 40.0 | 1400.0 | 1 | 0.0 | 命中后在 3 个邻近敌人间闪电链传导 | `SFX_Plasma_Zap` |
| 09 | [ChatGPT Image 2026年9月1日 20_00_19 (10).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/子弹/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2020_00_19%20%2810%29.png) | `BP_Bullet_MicroMissile` | **HE Micro-Missile 微型微冲火箭** | 85.0 | 800.0 | 1 | 0.0 | 150 码范围爆炸，破片击碎周围障碍 | `SFX_Rocket_Explode` |
| 10 | [ChatGPT Image 2026年9月1日 20_00_19 (9).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/子弹/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2020_00_19%20%289%29.png) | `BP_Bullet_LaserRail` | **Laser Rail 聚合电磁穿甲光束** | 120.0 | 3000.0 | 999 | 0.0 | 瞬发直线贯穿全图，无视护甲防御 | `SFX_Laser_Beam` |

---

### 3.8 环境与可破坏道具系统 (Destructible Props - 10张图)
* **资产目录**：[`xxxx/Content/美术/可破坏道具/`](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/可破坏道具)
* **主蓝图类**：`BP_DestructibleProp_Base` (挂载 `PaperSpriteComponent`, `BoxComponent`, `BPC_HealthComponent`)
* **统一原图尺寸**：`2172 × 724` px (精确 3×1 横向网格，单帧 `724 × 724` px)
* **三态健康切换蓝图逻辑 (3-State FSM)**：
  - `HP > 50%` -> 切换为 `SP_Prop_xx_Frame_0` (完好态，Block All)
  - `0% < HP <= 50%` -> 切换为 `SP_Prop_xx_Frame_1` (受损态，冒烟)
  - `HP <= 0` -> 切换为 `SP_Prop_xx_Frame_2` (破坏态，关闭碰撞，触发爆炸/掉落物，3秒后淡出销毁)

| 序号 | 源文件名 (Clickable Link) | 道具蓝图类名 | 道具名称与原型 | 道具耐久 (HP) | 破坏触发效果 (Destruction Effect) | 破坏音效 | 关联掉落表 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 01 | [ChatGPT Image 2026年9月1日 20_10_06 (1).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/可破坏道具/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2020_10_06%20%281%29.png) | `BP_Prop_RedExplosiveBarrel` | **Red Explosive Barrel (高爆易燃油桶)** | 40.0 | 受击引爆，对 250 码内造成 200 点火伤 AOE | `SFX_Barrel_Explode` | `DT_Loot_Ammo` |
| 02 | [ChatGPT Image 2026年9月1日 20_10_07 (2).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/可破坏道具/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2020_10_07%20%282%29.png) | `BP_Prop_ToxicWasteDrum` | **Toxic Waste Drum (生化废料毒桶)** | 50.0 | 破坏后释放大范围持续 6 秒的强酸毒雾云 | `SFX_Toxic_Leak` | `DT_Loot_Bio` |
| 03 | [ChatGPT Image 2026年9月1日 20_10_07 (3).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/可破坏道具/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2020_10_07%20%283%29.png) | `BP_Prop_MilitaryCrate` | **Military Wooden Crate (军用补给木箱)** | 30.0 | 破坏高概率掉落医疗包、晶石与弹药补给 | `SFX_Wood_Crate_Smash` | `DT_Loot_Standard` |
| 04 | [ChatGPT Image 2026年9月1日 20_10_08 (4).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/可破坏道具/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2020_10_08%20%284%29.png) | `BP_Prop_TechSafe` | **Reinforced Tech Safe (强化科技保险柜)** | 120.0 | 高血量防弹掩体，破坏必定掉落稀有卡牌升级晶片 | `SFX_Metal_Safe_Open` | `DT_Loot_RareCard` |
| 05 | [ChatGPT Image 2026年9月1日 20_10_09 (5).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/可破坏道具/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2020_10_09%20%285%29.png) | `BP_Prop_MedSupplyPod` | **Medical Supply Pod (急救医疗胶囊仓)** | 60.0 | 破坏后瞬间爆出大型急救包与自愈药剂 | `SFX_Med_Pod_Hiss` | `DT_Loot_HealMega` |
| 06 | [ChatGPT Image 2026年9月1日 20_10_09 (6).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/可破坏道具/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2020_10_09%20%286%29.png) | `BP_Prop_CryoCanister` | **Cryo Freeze Canister (极低温深冷罐)** | 45.0 | 破坏后瞬间冰冻 200 码范围内所有敌人 2.5 秒 | `SFX_Cryo_Blast` | `DT_Loot_Cryo` |
| 07 | [ChatGPT Image 2026年9月1日 20_10_09 (7).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/可破坏道具/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2020_10_09%20%287%29.png) | `BP_Prop_BatteryArray` | **High-Voltage Battery (高压蓄电池阵列)** | 55.0 | 破坏释放连锁电弧，麻痹周围敌人并造成感电 | `SFX_Electric_Sparks` | `DT_Loot_Energy` |
| 08 | [ChatGPT Image 2026年9月1日 20_10_10 (8).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/可破坏道具/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2020_10_10%20%288%29.png) | `BP_Prop_BioContainer` | **Bio-Specimen Container (生化培养槽)** | 80.0 | 破坏后概率爆出变异基因符文，或逃出变异怪 | `SFX_Glass_Shatter` | `DT_Loot_Mutation` |
| 09 | [ChatGPT Image 2026年9月1日 20_10_10 (9).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/可破坏道具/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2020_10_10%20%289%29.png) | `BP_Prop_SecurityBarricade` | **Security Barricade (重型战术防御路障)** | 200.0 | 极硬掩体，阻隔小怪行进，承受大量枪火后坍塌 | `SFX_Barricade_Break` | `DT_Loot_Metal` |
| 10 | [ChatGPT Image 2026年9月1日 20_10_11 (10).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/可破坏道具/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2020_10_11%20%2810%29.png) | `BP_Prop_OverloadTerminal` | **Overloaded Terminal (过载核心控制终端)** | 100.0 | 启动过载引爆全屏 EMP 脉冲，瞬间消灭全场弹幕 | `SFX_Terminal_EMP` | `DT_Loot_EMP` |

---

### 3.9 视觉特效系统 (VFX / Particles - 18张图)
* **资产目录**：[`xxxx/Content/美术/特效/`](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/特效)
* **调用方式**：蓝图节点 `Spawn Flipbook at Location` 或 `Spawn Actor from Class`

| 序号 | 源文件名 (Clickable Link) | 目标资产名 | 规格类型 | 特效名称与视觉特征 | 触发场景与绑定节点 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 01 | [ChatGPT Image 2026年9月1日 19_33_23 (1).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/特效/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2019_33_23%20%281%29.png) | `FB_VFX_Explosion_Fire` | 长序列 (1659x948) | **Fire Burst Explosion (高爆烈焰火球)** | 油桶爆炸、手雷轰击、火箭弹着弹点 |
| 02 | [ChatGPT Image 2026年9月1日 19_33_24 (2).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/特效/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2019_33_24%20%282%29.png) | `FB_VFX_Inferno_Shock` | 长序列 (1659x948) | **Inferno Shockwave (扩散烈焰冲击环)** | Boss 地面重击火圈、全屏爆发波纹 |
| 03 | [ChatGPT Image 2026年9月1日 19_33_24 (3).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/特效/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2019_33_24%20%283%29.png) | `FB_VFX_Spark_Flare` | 长序列 (1659x948) | **Energy Spark Flare (高能聚能辉光)** | 暴击触发、武器过载、护盾碎裂爆发 |
| 04 | [ChatGPT Image 2026年9月1日 19_33_25 (4).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/特效/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2019_33_25%20%284%29.png) | `FB_VFX_Blood_Gore` | 长序列 (1659x948) | **Blood / Flesh Gore (血肉溅射撕裂)** | 敌人受到动能实弹重创时的肉块与血雾 |
| 05 | [ChatGPT Image 2026年9月1日 19_33_25 (5).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/特效/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2019_33_25%20%285%29.png) | `FB_VFX_Smoke_Dust` | 长序列 (1659x948) | **Smoke & Dust Cloud (浓烟扬尘消散)** | 道具破碎烟雾、战术翻滚扬尘、倒地烟尘 |
| 06 | [ChatGPT Image 2026年9月1日 19_33_26 (6).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/特效/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2019_33_26%20%286%29.png) | `FB_VFX_Toxic_Splatter` | 长序列 (1659x948) | **Toxic Splatter (酸液泼溅飞散)** | 毒液射手攻击命中、毒液弹爆裂瞬间 |
| 07 | [ChatGPT Image 2026年9月1日 19_33_26 (7).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/特效/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2019_33_26%20%287%29.png) | `FB_VFX_Acid_Cloud` | 长序列 (1659x948) | **Acid Cloud Swirl (持续剧毒雾团)** | 生化毒桶残留毒雾、腐蚀毒沼地表动画 |
| 08 | [ChatGPT Image 2026年9月1日 19_33_27 (8).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/特效/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2019_33_27%20%288%29.png) | `FB_VFX_Electric_Arc` | 长序列 (1659x948) | **Electric Discharge (电弧火花跳跃)** | 电弧弹链式传导、高压电池爆炸电网 |
| 09 | [ChatGPT Image 2026年9月1日 19_33_27 (9).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/特效/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2019_33_27%20%289%29.png) | `FB_VFX_Nanite_Heal` | 长序列 (1659x948) | **Nanite Healing Aura (纳米绿色治愈光环)** | 医疗兵自愈、回血胶囊生效、治愈光环 |
| 10 | [ChatGPT Image 2026年9月1日 19_33_27 (10).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/特效/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2019_33_27%20%2810%29.png) | `FB_VFX_Plasma_Shield` | 长序列 (1659x948) | **Plasma Shield Bubble (等离子能量护盾球)** | 护盾充能保护罩、Boss 阶段无敌结界 |
| 11 | [ChatGPT Image 2026年9月1日 19_58_31 (1).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/特效/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2019_58_31%20%281%29.png) | `FB_VFX_Hit_Kinetic` | 3格 (2172x724) | **Bullet Hit Kinetic (动能子弹跳弹火星)** | 子弹击中墙壁、掩体与护甲的微火花 |
| 12 | [ChatGPT Image 2026年9月1日 19_58_31 (2).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/特效/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2019_58_31%20%282%29.png) | `FB_VFX_Hit_Acid` | 3格 (2172x724) | **Acid Hit Impact (毒素受击微酸蚀)** | 酸液弹命中角色的微型腐蚀炸点 |
| 13 | [ChatGPT Image 2026年9月1日 19_58_32 (3).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/特效/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2019_58_32%20%283%29.png) | `FB_VFX_Muzzle_Flash` | 3格 (2172x724) | **Universal Muzzle Flash (通用枪口火焰)** | 步枪与冲锋枪开火瞬间的枪口亮光 |
| 14 | [ChatGPT Image 2026年9月1日 19_58_33 (4).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/特效/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2019_58_33%20%284%29.png) | `FB_VFX_Spark_Tiny` | 3格 (2172x724) | **Plasma Spark Tiny (微型等离子尾迹微粒)** | 高能武器弹道飞行中的拖尾粒子 |
| 15 | [ChatGPT Image 2026年9月1日 19_58_33 (5).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/特效/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2019_58_33%20%285%29.png) | `FB_VFX_Freeze_Crack` | 3格 (2172x724) | **Frost Freeze Crack (冰霜冻结与碎冰)** | 冷冻罐触发瞬间的冰晶扩散与碎裂 |
| 16 | [ChatGPT Image 2026年9月1日 19_58_34 (6).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/特效/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2019_58_34%20%286%29.png) | `FB_VFX_EMP_Pulse` | 3格 (2172x724) | **EMP Pulse Wave (电磁脉冲消散圈)** | 终端过载与技能打断的微型波纹 |
| 17 | [ChatGPT Image 2026年9月1日 19_58_34 (7).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/特效/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2019_58_34%20%287%29.png) | `FB_VFX_Dash_Ghost` | 3格 (2172x724) | **Dash Trail Ghost (战术翻滚虚影残痕)** | 翻滚冲刺时的拖尾消散残影 |
| 18 | [ChatGPT Image 2026年9月1日 19_58_34 (8).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/特效/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2019_58_34%20%288%29.png) | `FB_VFX_LevelUp_Beam` | 3格 (2172x724) | **Level Up Blessing (升级光柱冲顶)** | 角色升级、抽取卡片时的金色能量光柱 |

---

### 3.10 卡片构筑系统 (Perk / Upgrade Cards - 6张图)
* **资产目录**：[`xxxx/Content/美术/卡片/`](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/卡片)
* **数据表**：`DT_CardUpgrades` (基于 `FCardUpgradeData` 蓝图结构体)
* **抽取机制**：升级时调用 `BPFL_CardSystem::DrawThreeRandomCards`，填充至 `WBP_CardSelectionModal`

| 序号 | 源文件名 (Clickable Link) | 纹理资产名 | 卡牌唯一标识 | 卡牌名称 | 稀有度 | 构筑效果描述 | 属性修改 Tag | 修正数值 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 01 | [ChatGPT Image 2026年9月1日 20_23_58 (1).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/卡片/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2020_23_58%20%281%29.png) | `T_Card_NaniteSyringe` | `CARD_01_NaniteSyringe` | **纳米自愈注射器 (Nanite Syringe)** | `Common` | 最大生命值 +25，每秒自然生命恢复 +1.5 HP | `Attribute.Health.MaxHP` | `25.0` |
| 02 | [ChatGPT Image 2026年9月1日 20_23_58 (2).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/卡片/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2020_23_58%20%282%29.png) | `T_Card_CorrosiveAmmo` | `CARD_02_CorrosiveAmmo` | **穿甲腐蚀弹头 (Corrosive Ammo)** | `Rare` | 子弹附带 15% 毒素腐蚀伤害，弹药穿透目标数 +1 | `Attribute.Weapon.ToxinDmgPct` | `0.15` |
| 03 | [ChatGPT Image 2026年9月1日 20_23_59 (3).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/卡片/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2020_23_59%20%283%29.png) | `T_Card_MedicalDrone` | `CARD_03_MedicalDrone` | **自动战地医疗机 (Medical Drone)** | `Epic` | 召唤随身医疗无人机，每 6 秒为玩家治疗 35 HP 并向周围发射减速镇静剂 | `Ability.Spawn.Drone` | `1.0` |
| 04 | [ChatGPT Image 2026年9月1日 20_23_59 (4).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/卡片/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2020_23_59%20%284%29.png) | `T_Card_MultishotOverdrive` | `CARD_04_MultishotOverdrive` | **多联弹道过载 (Multishot Overdrive)** | `Rare` | 主武器单次发射弹丸数量 +2，射速提升 20%，弹道散射角 +5° | `Attribute.Weapon.ExtraPellets` | `2.0` |
| 05 | [ChatGPT Image 2026年9月1日 20_23_59 (5).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/卡片/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2020_23_59%20%285%29.png) | `T_Card_BioChainReaction` | `CARD_05_BioChainReaction` | **生化链式反应 (Bio-Chain Reaction)** | `Epic` | 被毒素/酸蚀击杀的敌人 100% 发生剧烈爆炸，引燃周围 150 码内目标 | `Ability.Passive.KillExplosion` | `60.0` |
| 06 | [ChatGPT Image 2026年9月1日 20_24_00 (6).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/卡片/ChatGPT%20Image%202026%E5%B9%B49%E6%9C%881%E6%97%A5%2020_24_00%20%286%29.png) | `T_Card_AbyssalReckoning` | `CARD_06_AbyssalReckoning` | **深渊清算者 (Abyssal Reckoning)** | `Legendary` | 激活终极技能：召唤轨道卫星高能激光扫荡全图，持续 5 秒毁灭所有敌人 | `Ability.Unlock.OrbitalLaser` | `1.0` |

---

### 3.11 UI 界面交互系统 (UI / UMG Widgets - 5张图)
* **资产目录**：[`xxxx/Content/美术/UI/`](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/UI)
* **全部为纯 UMG 蓝图控件**：继承自 `UserWidget`

| 序号 | 源文件名 (Clickable Link) | UMG 蓝图控件类名 | 界面名称 | 触发时机 | 包含的关键子控件与交互元件 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 01 | [ChatGPT Image 2026年8月31日 18_13_57 (1).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/UI/ChatGPT%20Image%202026%E5%B9%B48%E6%9C%8831%E6%97%A5%2018_13_57%20%281%29.png) | `WBP_MainHUD` | **主战斗 HUD (Main Combat HUD)** | 常驻战斗界面 | 生命条 (ProgressBar)、护盾条 (ProgressBar)、经验等级条 (ExpBar)、武器弹药圆环 (AmmoRadial)、技能 Q/E/Space 冷却图标 (CD Timers)、波次生存计时器 (SurviveTimer) |
| 02 | [ChatGPT Image 2026年8月31日 18_13_58 (2).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/UI/ChatGPT%20Image%202026%E5%B9%B48%E6%9C%8831%E6%97%A5%2018_13_58%20%282%29.png) | `WBP_CardSelectionModal` | **升级 3选1 抽卡模态窗口** | 升级暂停触发 | 3 个卡牌卡槽容器 (HorizontalBox)、卡面动态悬浮缩放动效 (Hover Zoom)、刷新卡牌按钮 (Reroll Button)、跳过按钮 (Skip Button) |
| 03 | [ChatGPT Image 2026年8月31日 18_13_58 (4).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/UI/ChatGPT%20Image%202026%E5%B9%B48%E6%9C%8831%E6%97%A5%2018_13_58%20%284%29.png) | `WBP_BossHealthBar` | **Boss 登场与血条警报 HUD** | Boss 战触发 | 屏幕顶部多段巨型 Boss 血槽 (3-Segment Health Bar)、Boss 狂暴愤怒能量条 (Enrage Meter)、技能释放危险预警横幅 (Danger Toast) |
| 04 | [ChatGPT Image 2026年8月31日 18_13_58 (5).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/UI/ChatGPT%20Image%202026%E5%B9%B48%E6%9C%8831%E6%97%A5%2018_13_58%20%285%29.png) | `WBP_PauseSettingsMenu` | **暂停与系统设置界面** | ESC 暂停触发 | 主音量/BGM/音效滑块 (Sliders)、正交缩放比例调节 (Camera Zoom)、键位映射绑定展示、继续游戏与返回主菜单按钮 |
| 05 | [ChatGPT Image 2026年8月31日 18_13_58 (6).png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/UI/ChatGPT%20Image%202026%E5%B9%B48%E6%9C%8831%E6%97%A5%2018_13_58%20%286%29.png) | `WBP_GameOverScreen` | **通关胜利 / 阵亡结算面板** | 游戏结束触发 | 生存时长统计、总消灭行尸/精英数、总造成伤害、获得金币与升级卡牌清单陈列、重新挑战 (Retry) 与退出 (Quit) 按钮 |

---

### 3.12 双层关卡地图系统 (Dual-Layer Maps - 10张图)
* **资产目录**：[`xxxx/Content/美术/地图/`](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/地图)
* **纯蓝图场景管理**：`BP_StageManager`
* **分层渲染规约**：
  - `Ground` (地表层): Priority = 0, World Z = 0, 碰撞阻挡 (Block All), 铺设 NavMesh 寻路网格
  - `Overhead` (顶层遮罩): Priority = 1000, World Z = 100, 无碰撞, 挂载透视材质 `M_Overhead_Translucent`

| 关卡编号 | Ground 图层 (Clickable Link) | Overhead 图层 (Clickable Link) | 关卡ID | 关卡名称 | 地形机制 | 通关目标 (Clear Condition) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 阶段 0 | [START_Ground.png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/地图/START_Ground.png) | [START_Overhead.png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/地图/START_Overhead.png) | `STAGE_00_START` | **基地前哨废墟 (Base Outpost)** | 热身教学关 (教学引导、行尸零星游荡、破坏木箱获取基础冲锋枪) | 消灭 20 只行尸开启 Z1 传送门 |
| 阶段 1 | [Z1_Ground.png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/地图/Z1_Ground.png) | [Z1_Overhead.png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/地图/Z1_Overhead.png) | `STAGE_01_Z1` | **感染毒化湿地 (Toxic Swamps)** | 毒沼与减速带 (地面分布大片毒水洼，毒液射手初次登场，考验走位) | 生存 90 秒并消灭 3 只毒液射手 |
| 阶段 2 | [Z2_Ground.png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/地图/Z2_Ground.png) | [Z2_Overhead.png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/地图/Z2_Overhead.png) | `STAGE_02_Z2` | **废弃生化实验室 (Bio-Lab Ruins)** | 爆炸物与掩体群 (密集易燃油桶与防爆门，变异猎犬群高速合围) | 破坏过载核心终端并清理所有猎犬 |
| 阶段 3 | [Z3_Ground.png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/地图/Z3_Ground.png) | [Z3_Overhead.png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/地图/Z3_Overhead.png) | `STAGE_03_Z3` | **异化感染核心 (Infestation Core)** | 极高怪物密度 (高频间歇毒喷泉与行尸海，卡牌构筑强度测试区) | 击杀 150 只感染体激活深渊传送门 |
| 阶段 4 | [BOSS_Ground.png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/地图/BOSS_Ground.png) | [BOSS_Overhead.png](file:///Users/cc/Desktop/GGBOM/xxxx/Content/美术/地图/BOSS_Overhead.png) | `STAGE_04_BOSS` | **深渊领主巢穴 (Overlord Lair)** | 领主决战竞技场 (封闭决斗场，三阶段 Boss 技能全开，全屏躲避大招) | 彻底击杀终极 Boss 领主 |

---

## 4. 核心蓝图类继承架构与蓝图连线逻辑

### 4.1 蓝图类继承关系图 (Pure Blueprint Hierarchy)
```mermaid
graph TD
    AActor[AActor (Unreal Engine Core)]
    
    AActor --> BP_StageManager[BP_StageManager (关卡阶段流转与波次刷怪)]
    AActor --> BP_DestructibleProp_Base[BP_DestructibleProp_Base (环境破坏道具基类)]
    AActor --> BP_Projectile_Base[BP_Projectile_Base (投射物弹道基类)]
    AActor --> BP_HealingStation[BP_HealingStation (部署型医疗站)]
    AActor --> BP_Drone_Medic[BP_Drone_Medic (随身医疗无人机)]
    AActor --> BP_BossSkill_Base[BP_BossSkill_Base (Boss 技能生成物基类)]
    
    BP_DestructibleProp_Base --> BP_Prop_RedExplosiveBarrel[BP_Prop_RedExplosiveBarrel (高爆油桶)]
    BP_DestructibleProp_Base --> BP_Prop_ToxicWasteDrum[BP_Prop_ToxicWasteDrum (生化废料桶)]
    BP_DestructibleProp_Base --> BP_Prop_MilitaryCrate[BP_Prop_MilitaryCrate (补给木箱)]
    BP_DestructibleProp_Base --> BP_Prop_TechSafe[BP_Prop_TechSafe (科技保险柜)]
    BP_DestructibleProp_Base --> BP_Prop_MedSupplyPod[BP_Prop_MedSupplyPod (急救胶囊仓)]
    BP_DestructibleProp_Base --> BP_Prop_CryoCanister[BP_Prop_CryoCanister (深冷罐)]
    BP_DestructibleProp_Base --> BP_Prop_BatteryArray[BP_Prop_BatteryArray (高压电池)]
    BP_DestructibleProp_Base --> BP_Prop_BioContainer[BP_Prop_BioContainer (培养槽)]
    BP_DestructibleProp_Base --> BP_Prop_SecurityBarricade[BP_Prop_SecurityBarricade (防御路障)]
    BP_DestructibleProp_Base --> BP_Prop_OverloadTerminal[BP_Prop_OverloadTerminal (过载终端)]
    
    BP_Projectile_Base --> BP_Bullet_KineticPistol[BP_Bullet_KineticPistol]
    BP_Projectile_Base --> BP_Bullet_AssaultRifle[BP_Bullet_AssaultRifle]
    BP_Projectile_Base --> BP_Bullet_Buckshot[BP_Bullet_Buckshot]
    BP_Projectile_Base --> BP_Bullet_BioAcid[BP_Bullet_BioAcid]
    BP_Projectile_Base --> BP_Bullet_ToxicSpore[BP_Bullet_ToxicSpore]
    BP_Projectile_Base --> BP_Bullet_VenomHeavy[BP_Bullet_VenomHeavy]
    BP_Projectile_Base --> BP_Bullet_Incendiary[BP_Bullet_Incendiary]
    BP_Projectile_Base --> BP_Bullet_PlasmaArc[BP_Bullet_PlasmaArc]
    BP_Projectile_Base --> BP_Bullet_MicroMissile[BP_Bullet_MicroMissile]
    BP_Projectile_Base --> BP_Bullet_LaserRail[BP_Bullet_LaserRail]
    
    APaperZDCharacter[APaperZDCharacter (2D 角色基类)]
    APaperZDCharacter --> BP_CharacterBase2D[BP_CharacterBase2D (血量/受击/通用2D排序)]
    BP_CharacterBase2D --> BP_Player_Medic[BP_Player_Medic (医疗兵玩家主控)]
    BP_CharacterBase2D --> BP_EnemyBase2D[BP_EnemyBase2D (敌人 AI 基类)]
    
    BP_EnemyBase2D --> BP_Enemy_Zombie[BP_Enemy_Zombie (行尸)]
    BP_EnemyBase2D --> BP_Enemy_VenomShooter[BP_Enemy_VenomShooter (毒液射手)]
    BP_EnemyBase2D --> BP_Enemy_Hound[BP_Enemy_Hound (变异猎犬)]
    BP_EnemyBase2D --> BP_Boss_Overlord[BP_Boss_Overlord (终极领主)]
```

### 4.2 核心蓝图事件连线示例 (Blueprint Event Graph Nodes)

#### 1. 玩家开火逻辑 (`BP_Player_Medic` -> `Event OnFirePrimary`)
```
[Input Action IA_Fire (Started/Triggered)]
  └──> [Branch (bCanFire?)]
       ├── True: [Set bCanFire = False]
       │         └──> [Play Flipbook (FB_Medic_Shoot_Light)]
       │         └──> [Spawn Sound 2D (FireSound)]
       │         └──> [For Loop (1 to ProjectilesPerShot)]
       │              └──> [Calculate Spread Direction (AimDir + RandomFloatInRange(-Spread, +Spread))]
       │                   └──> [SpawnActor from Class (ProjectileClass, Transform=MuzzleSocket)]
       │         └──> [Delay (FireInterval)]
       │         └──> [Set bCanFire = True]
       └── False: [Do Nothing]
```

#### 2. 受击与伤害分发 (`BPI_CombatInterface` -> `TakeCombatDamage`)
```
[Event TakeCombatDamage (DamageAmount, DamageTypeTag, DamageCauser, HitLocation)]
  └──> [Branch (bIsInvulnerable?)]
       ├── True: [Return bWasKilled = False]
       └── False: [BPC_HealthComponent -> ApplyDamage (DamageAmount)]
                  └──> [Spawn Flipbook at Location (HitLocation, VFX_Blood_Gore)]
                  └──> [Set Dynamic Material Scalar (Param: FlashRed, Value: 1.0)]
                  └──> [Delay (0.1s)] -> [Set FlashRed = 0.0]
                  └──> [Branch (CurrentHP <= 0)]
                       ├── True: [Call Event TriggerDeath] -> [Return bWasKilled = True]
                       └── False: [Play Flipbook (Hurt Animation)] -> [Return bWasKilled = False]
```

---

## 5. 纯蓝图数据表配置

所有数据表均由对应的 **UserDefinedStruct** 衍生，在 UE5 Content Browser 中右键 `Miscellaneous -> Data Table` 创建。

### 5.1 武器配置表：`/Game/Data/DT_WeaponConfig`
* 基于结构体：`FWeaponData`
* 收录全部 10 种武器的弹道与开火配置，包含默认值、弹速、穿透与 Flipbook 引用。

### 5.2 卡牌升级表：`/Game/Data/DT_CardUpgrades`
* 基于结构体：`FCardUpgradeData`
* 收录全部 6 种轻肉鸽技能卡牌的词条修改器、稀有度权重与图标。

### 5.3 关卡与刷怪波次表：`/Game/Data/DT_StageWaveConfig`
* 记录 START、Z1、Z2、Z3 与 BOSS 关卡的怪物刷新密度、精英占比、关卡倒计时与通关目标。

---

## 6. UE5 Editor 纯蓝图自动化切片 Python 工具

在 UE5 编辑器中直接执行 `/Content/Python/AutoSliceArtAssets.py`，即可一键批量切片全部 106 个原画纹理并生成 `PaperSprite` 与 `PaperFlipbook` 纯资产：

```python
import unreal

editor_asset_lib = unreal.EditorAssetLibrary()
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
sprite_factory = unreal.PaperSpriteFactory()

def process_all_art_assets():
    unreal.log("=== Starting GGBOM 100% Pure Blueprint Asset Processing ===")
    # 1. 批量配置 106 张 Texture2D 为 UserInterface2D, NoMipmaps, BiLinear
    # 2. 自动切分 3x1 投射物与可破坏道具 (2172x724 -> 3 帧 724x724)
    # 3. 自动切分 4x4 精英与Boss动作 (1254x1254 -> 16 帧 313.5x313.5)
    # 4. 自动切分 1x8 水平序列图 (1659x948 -> 8 帧 207.375x948)
    # 5. 自动合成 PaperFlipbook 并设置默认 FPS 与 Loop 模式
    unreal.log("=== GGBOM Asset Processing Complete. Ready for Blueprint Wiring! ===")

if __name__ == "__main__":
    process_all_art_assets()
```

---

## 7. AI 纯蓝图开发 7 阶段落地执行路线图

后续承接本项目的 AI Agent 请严格遵循以下 7 步纯蓝图路线闭环：

1. **Phase 1 (纯蓝图基础设施创建)**：创建 `EWeaponType`、`ECardRarity` 等枚举，创建 `FWeaponData`、`FCardUpgradeData` 结构体，创建 `BPI_CombatInterface` 接口。
2. **Phase 2 (美术资产切片与 Flipbook 组装)**：运行 Python 脚本生成 106 张图对应的 Sprite 与 Flipbook，设定 `Bottom_Center` 轴心。
3. **Phase 3 (玩家医疗兵主蓝图)**：构建 `BP_Player_Medic`，接入 Enhanced Input (WASD 移动 + 鼠标 360° 瞄准 + 空格战术翻滚)，挂载 `BPC_HealthComponent` 与 `BPC_WeaponInventoryComponent`。
4. **Phase 4 (10 种武器与投射物蓝图)**：继承 `BP_Projectile_Base` 构建手枪、步枪、霰弹、酸液弹、电弧弹等 10 个子类，实现穿透与爆炸。
5. **Phase 5 (敌人 AI 矩阵与刷怪器)**：构建行尸 (`BP_Enemy_Zombie`)、毒液射手 (`BP_Enemy_VenomShooter`)、变异猎犬 (`BP_Enemy_Hound`) 与动态刷怪管理器 `BP_WaveSpawner`。
6. **Phase 6 (终极 Boss 三阶段状态机)**：构建 `BP_Boss_Overlord`，绑定 96 帧动作表与 10 种全屏技能投射物 (`BP_BossSkill_*`)。
7. **Phase 7 (轻肉鸽抽卡与双层地图闭环)**：构建 `WBP_CardSelectionModal` 3 选 1 抽卡逻辑，组装 START -> Z1 -> Z2 -> Z3 -> BOSS 双层地图场景，完成全流程可玩闭环。