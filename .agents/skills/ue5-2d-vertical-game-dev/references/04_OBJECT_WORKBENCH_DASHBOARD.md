# 04 对象工作台 Dashboard 具体结构

## 左侧对象导航
项目总览
角色
武器
弹丸
技能
敌人
Boss
升级
拾取物
波次
关卡
UI
性能
架构
验证

不要按“图片/动画/VFX”割裂对象。

## 角色工作台
顶部：StableID / 中文名 / Blueprint / Parent / Definition / READY状态。
Tabs：基础 | 属性 | 装备 | 美术 | 动画 | VFX/SFX | 平衡 | 依赖 | 验证 | 变更历史

### 属性页
直接编辑真实 Character Definition。
右侧实时角色对比：HP、Shield、Defense、MoveSpeed、Expected Output 等。

### 装备页
主武器/副武器/AbilitySet 可直接配置并跳转关联对象。

### 美术页
Portrait / Icon / AnimationProfile / HitVFX / DeathVFX 直接配置。

### 动画页
固定 5方向矩阵：S / SE / E / NE / N。
动作行：Idle / Run / Attack / Hurt / Dead / 可选动作。
单元格显示：Flipbook、SpriteCount、FPS、Loop、Pivot、Source、验证状态，并支持预览/打开/重新导入/验证。

### 依赖页
显示 Definition→AnimationProfile→Flipbooks→Sprites、Weapon→Projectile、AbilitySet→Abilities 等正向依赖，以及谁引用该对象的反向依赖。

## 武器工作台
Tabs：属性 | 美术 | 弹丸 | 动画 | VFX/SFX | 升级 | 平衡 | 依赖 | 验证 | 变更历史
实时指标：Damage / FireRate / DPS / ExpectedDPS / Range / Reload。
固定图：Expected DPS柱状图、Range vs DPS散点、等级DPS成长曲线。

## 敌人与波次
固定时间轴图：SpawnRate、MaxAlive、TotalEnemyHP、DamagePressure。
DamagePressure = Σ(当前敌人数 × 敌人单体DPS)。

## 成长升级
固定图：累计XP、Player DPS Growth、Enemy HP Growth、Upgrade Benefit、TTK。
TTK = EnemyHP / PlayerExpectedDPS。

## 项目总览
角色/武器/敌人/技能完成率、美术Runtime完成率、Blueprint通过率、PIE通过率、Android通过率均从真实 Registry/Validation 派生，禁止手填百分比。

## 架构页
每个 Blueprint 显示：Parent、Definition、继承深度、自定义业务节点数、Component数、DuplicateLogic、状态。

## 对象健康
Stable ID重复 / Component重复 / Event重复 / Ability重复 / Animation映射重复 / Definition重复，任何 >0 → FAIL。
