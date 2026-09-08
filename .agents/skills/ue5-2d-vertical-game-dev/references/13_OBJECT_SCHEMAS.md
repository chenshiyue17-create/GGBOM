# 13 对象字段结构

## Character Definition
基础信息：CharacterID, DisplayName, CharacterType, Tags
生存：MaxHealth, MaxShield, Defense, HealthRegen
移动：MoveSpeed, Acceleration, Deceleration
战斗：DamageMultiplier, CritChance, CritMultiplier, PickupRadius
装备：PrimaryWeapon, SecondaryWeapon, AbilitySet
视觉：Portrait, Icon, AnimationProfile
表现：HitVFX, DeathVFX, LevelUpVFX
声音：HurtSFX, DeathSFX, MoveSFX

## Weapon Definition
基础：WeaponID, DisplayName, WeaponType
战斗：Damage, FireRate, ProjectileCount, Spread, Pierce, Knockback
弹药：MagazineSize, ReloadTime
范围：ProjectileSpeed, Range
美术：WorldSprite, Icon, WeaponVisualMode, IdleFlipbook, FireFlipbook
弹丸：ProjectileDefinition
VFX：MuzzleVFX, ImpactVFX
SFX：FireSFX, ReloadSFX, EmptySFX
派生：TheoreticalDPS, ExpectedDPS

## Projectile Definition
Speed, LifeTime, CollisionRadius, Pierce, Bounce, Homing, DamageProfile, StaticSprite, FlightFlipbook, Trail, ImpactVFX, ImpactSFX

## Ability Definition
AbilityID, DisplayName, Cooldown, Damage, Range, Duration, CastTime, CharacterAnimationKey, Icon, Projectile, WorldVisual, CastVFX, TravelVFX, ImpactVFX, CastSFX, ImpactSFX, UpgradeProfile, Description

## Enemy Definition
EnemyID, DisplayName, EnemyType, MaxHealth, Damage, MoveSpeed, AttackInterval, AttackRange, CollisionRadius, KnockbackResistance, ExpReward, CurrencyReward, EliteWeight, AIProfile, AnimationProfile, HitVFX, DeathVFX, DropTable

## Wave Row
WaveID, StartTime, EndTime, EnemyID, SpawnRate, MaxAlive, HealthMultiplier, DamageMultiplier, SpeedMultiplier, EliteChance, SpawnArea, DropMultiplier

## Upgrade Definition
UpgradeID, DisplayName, Category, MaxLevel, LevelValues[], Rarity, Weight, Requirement, Icon, Description

## UI Theme
HealthBarBG/Fill, ExpBarBG/Fill, JoystickBase/Thumb, SkillSlotNormal/Pressed/Disabled, CooldownMaterial, UpgradeCardCommon/Rare/Epic, BossBar, Buttons, Panels, Fonts
