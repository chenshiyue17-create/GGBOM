# 03 数据所有权与属性汉化

## 单一真相源
DataAsset：一个具体游戏对象的完整 Definition 与复杂资源引用。
DataTable：批量平衡、成长、波次、掉落、性能预算、统计比较。
Dashboard：View + Editor，不保存第二套业务数据。

## 数据所有权
- 角色美术 → Character Definition / Animation Profile
- 武器美术 → Weapon Definition
- 弹丸美术 → Projectile Definition
- 技能美术 → Ability Definition
- 敌人美术 → Enemy Definition / Animation Profile
- Boss美术 → Boss Definition
- Pickup美术 → Pickup Definition
- UI美术 → UI Theme
- 场景美术 → Environment Profile

全局 Art Registry 只扫描/统计/验证，不作为配置源。

## 属性汉化硬规则
内部：英文 Stable Key。
对人：中文 DisplayName / Category / ToolTip。

每个可调参数至少定义：
- InternalName
- DisplayName
- Category
- Tooltip
- Unit
- HardMin/HardMax
- RecommendedMin/RecommendedMax

例：CritChance
- 中文：暴击率
- Category：战斗属性
- Unit：%
- Hard Range：0~1
- Recommended：0~0.5

AI 创建新 UPROPERTY 缺少中文 DisplayName/Category/Tooltip → VALIDATION FAIL。
