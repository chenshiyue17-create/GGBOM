# 02 Blueprint父子关系与组件化

## 角色标准继承
AMSCharacterBase
├─ BP_CHR_PlayerBase
│  ├─ BP_CHR_Assault
│  ├─ BP_CHR_Sniper
│  ├─ BP_CHR_Heavy
│  └─ BP_CHR_Medic
├─ BP_CHR_EnemyBase
│  ├─ BP_ENE_Shambler
│  ├─ BP_ENE_Runner
│  └─ BP_ENE_Shooter
└─ BP_CHR_BossBase
   └─ BP_BOSS_*

## 继承深度
建议 Native Base → Category Base → Concrete Blueprint，通常 <=3~4层。

## Concrete Blueprint
默认 Data Only：
- Parent
- Definition
- 极少真正对象特有 Assembly

禁止重复实现：移动、受伤、死亡、方向计算、动画选择、通用武器、通用技能、UI。

## Component ownership
Character Base 典型：
- CharacterCore
- StatsComponent
- StateComponent
- MovementComponent
- VisualComponent
- Animation2DComponent
- ExtensionHost

Player Base：
- InputAdapter
- AutoAimComponent
- WeaponHostComponent
- AbilityHostComponent

Enemy Base：
- TargetComponent
- AIComponent

Boss Base：
- BossPhaseComponent
- BossPatternComponent

## Cardinality
Stats / Animation2D / WeaponHost / AbilityHost 等典型 Host 组件默认 0..1 或 1；重复直接 FAIL。

## Blueprint Creation Guard
创建 BP 前必须检查：
1. 同 Stable ID 是否存在
2. 是否已有合适 Parent
3. 是否可完全数据驱动而无需子 BP
4. 是否已有同能力 Component
5. 是否会产生重复逻辑
6. 是否会使继承过深

## Duplicate Logic Validator
扫描多个 Blueprint 的高度相似 Graph。若 Assault/Sniper/Heavy 都有同一方向计算图，必须迁入 MSAnimation2DComponent，ARCHITECTURE=FAIL 直到修复。
