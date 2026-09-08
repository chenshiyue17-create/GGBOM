# Weapon Data Specification

## ST_WeaponData

字段必须统一：

```text
WeaponID                Name
DisplayName             Text

BaseDamage              Float
FireRate                Float
ProjectileSpeed         Float

MagazineSize            Integer
ReloadTime              Float

SpreadAngle             Float
ProjectileCount         Integer

CritChance              Float
CritMultiplier          Float

PierceCount             Integer
Knockback               Float

AttackRange             Float

ProjectileClass         Actor Class

bAutomatic              Boolean
bExplosive              Boolean

ExplosionRadius         Float

WeaponLevel             Integer
```

## 单位约定

```text
BaseDamage
= 单颗弹丸基础伤害

FireRate
= 每秒射击次数

ProjectileSpeed
= Unreal Units / Second

ReloadTime
= 秒

SpreadAngle
= Degree

CritChance
= 0~1

CritMultiplier
= 倍率

AttackRange
= Unreal Units

Knockback
= 推力强度

PierceCount
= 允许额外穿透的目标数量
```

Fire Interval：

```text
FireInterval = 1 / FireRate
```

例如：

```text
FireRate = 6
FireInterval ≈ 0.1667 sec
```

---

# 默认武器数值

## AR-01

```text
WeaponID = AR01
BaseDamage = 18
FireRate = 6.0
ProjectileSpeed = 2400
MagazineSize = 30
ReloadTime = 1.5
SpreadAngle = 2
ProjectileCount = 1
CritChance = 0.05
CritMultiplier = 1.5
PierceCount = 0
Knockback = 20
AttackRange = 1800
bAutomatic = true
bExplosive = false
ExplosionRadius = 0
WeaponLevel = 1
```

理论基础 DPS：

```text
18 × 6 = 108
```

## SMG-01

```text
WeaponID = SMG01
BaseDamage = 11
FireRate = 10
ProjectileSpeed = 2200
MagazineSize = 40
ReloadTime = 1.3
SpreadAngle = 5
ProjectileCount = 1
CritChance = 0.05
CritMultiplier = 1.5
PierceCount = 0
Knockback = 10
AttackRange = 1500
bAutomatic = true
bExplosive = false
```

## SG-01

```text
WeaponID = SG01
BaseDamage = 12
FireRate = 1.4
ProjectileSpeed = 1900
MagazineSize = 8
ReloadTime = 2.0
SpreadAngle = 14
ProjectileCount = 6
CritChance = 0.05
CritMultiplier = 1.5
PierceCount = 0
Knockback = 35
AttackRange = 1100
bAutomatic = true
bExplosive = false
```

理论贴脸单次：

```text
12 × 6 = 72
```

## SR-01

```text
WeaponID = SR01
BaseDamage = 70
FireRate = 0.8
ProjectileSpeed = 3500
MagazineSize = 5
ReloadTime = 2.2
SpreadAngle = 0.5
ProjectileCount = 1
CritChance = 0.10
CritMultiplier = 1.75
PierceCount = 2
Knockback = 50
AttackRange = 2600
bAutomatic = true
bExplosive = false
```

## GL-01

```text
WeaponID = GL01
BaseDamage = 55
FireRate = 0.65
ProjectileSpeed = 1300
MagazineSize = 6
ReloadTime = 2.4
SpreadAngle = 2
ProjectileCount = 1
CritChance = 0
CritMultiplier = 1
PierceCount = 0
Knockback = 60
AttackRange = 1700
bAutomatic = true
bExplosive = true
ExplosionRadius = 260
```

---

# 敌人初始血量建议

```text
Fast Enemy      HP = 28
Shambler        HP = 45
Tank Enemy      HP = 140
Elite           HP = 550
Boss            HP = 6000~9000
```

基于 AR01：

```text
Shambler ≈ 3 shots
Tank ≈ 8 shots
```

---

# 运行时升级属性

不能直接修改 DataTable 原始值。

推荐变量：

```text
RuntimeDamageMultiplier              Float Default 1.0
RuntimeFireRateMultiplier            Float Default 1.0
RuntimeProjectileSpeedMultiplier     Float Default 1.0
RuntimeCritChanceBonus               Float Default 0.0
RuntimeProjectileCountBonus          Integer Default 0
RuntimePierceBonus                   Integer Default 0
```

最终数值：

```text
FinalDamage =
BaseDamage
*
RuntimeDamageMultiplier

FinalFireRate =
FireRate
*
RuntimeFireRateMultiplier

FinalProjectileSpeed =
ProjectileSpeed
*
RuntimeProjectileSpeedMultiplier

FinalCritChance =
Clamp(
    CritChance + RuntimeCritChanceBonus,
    0,
    1
)

FinalProjectileCount =
ProjectileCount
+
RuntimeProjectileCountBonus

FinalPierce =
PierceCount
+
RuntimePierceBonus
```

---

# 推荐升级

## Firepower I

```text
RuntimeDamageMultiplier *= 1.15
```

## Rapid Fire I

```text
RuntimeFireRateMultiplier *= 1.12
```

## Armor Piercing

```text
RuntimePierceBonus += 1
```

## Double Shot

```text
RuntimeProjectileCountBonus += 1
```

## Critical Upgrade

```text
RuntimeCritChanceBonus += 0.08
```

---

# DPS 成长目标

```text
Early Game:
~108 DPS

Mid Game:
180~300 DPS

Late Game:
400~700 DPS
```

避免几分钟内膨胀到数千 DPS，否则敌人血量会同步失控。
