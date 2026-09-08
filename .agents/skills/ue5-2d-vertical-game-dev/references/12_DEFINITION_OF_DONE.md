# 12 Definition of Done

## Character
ARCHITECTURE: Parent / Depth / DuplicateLogic / Components
DATA: Definition / 中文属性 / Range
ART: Portrait / Icon
ANIMATION: Source / Sprites / Flipbooks / Profile / Mirror
GAMEPLAY: Movement / Weapon / Ability / Damage / Death
PRESENTATION: HitVFX / DeathVFX / SFX / UI
BALANCE: Dashboard / Charts
RUNTIME: Compile / PIE
全部关键项 PASS → READY。

## Weapon
Definition / 中文属性 / Damage-FireRate-Magazine / WorldSprite / Icon / WeaponAnim可选 / Projectile / MuzzleVFX / ImpactVFX / FireSFX / ReloadSFX / DPS Charts / Compile / PIE。

## Enemy
Definition / Parent / AI Profile / Stats / SourceArt / Sprite / Flipbook / AnimationProfile / HitVFX / DeathVFX / Drop / Spawn / Compile / PIE。

## Ability
Definition / 参数 / Icon / CharacterCastAnimation映射 / Projectile或WorldVisual / CastVFX / ImpactVFX / SFX / Cooldown UI / Upgrade / Runtime Test。

## UI
Theme / Layout / Art / Event Binding / 9:16 Safe Area / No Tick polling / Runtime。

## Level
EnvironmentProfile / Ground / Obstacles / Bounds / CameraBounds / SpawnZones / EncounterZones / BossArea / LevelDirector / WaveData / Runtime / Performance。

## Final Report
若任何必需项 MISSING / FAILED / PLACEHOLDER / NOT EXECUTED，则 FINAL=INCOMPLETE。
