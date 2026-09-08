# IDE Agent Task — UE5.8 Combat System

## Mission

Implement the real attack / weapon / projectile system directly inside the UE5.8 project.

Do not merely generate instructions.
Do not create fake placeholder assets.
Do not claim completion without inspecting and validating the actual project.

## Required Assets

Create or integrate equivalent real project assets:

```text
/Content/Blueprints/Combat/Components/BPC_WeaponComponent
/Content/Blueprints/Combat/Interfaces/BPI_Damageable
/Content/Blueprints/Combat/Weapons/BP_WeaponBase
/Content/Blueprints/Combat/Projectiles/BP_ProjectileBase
/Content/Blueprints/Combat/Data/ST_WeaponData
/Content/Blueprints/Combat/Data/DT_Weapons
```

Weapon child Blueprints may be created if useful:

```text
BP_Weapon_AR01
BP_Weapon_SMG01
BP_Weapon_SG01
BP_Weapon_SR01
BP_Weapon_GL01
```

Do not duplicate child Blueprints merely to hard-code different damage values if the base weapon + DataTable already handles those differences.

## Active Player Requirement

Locate the actual pawn/character used by the current GameMode.

Attach or integrate:

```text
BPC_WeaponComponent
```

Do not modify an unused template character and report success.

## Enemy Requirement

Locate the actual enemy base class used in gameplay.

Implement:

```text
BPI_Damageable
```

Integrate with the existing real health/death pipeline.

Do not create a parallel fake enemy health system.

## Required ST_WeaponData Fields

```text
WeaponID
DisplayName
BaseDamage
FireRate
ProjectileSpeed
MagazineSize
ReloadTime
SpreadAngle
ProjectileCount
CritChance
CritMultiplier
PierceCount
Knockback
AttackRange
ProjectileClass
bAutomatic
bExplosive
ExplosionRadius
WeaponLevel
```

## Required Weapon Rows

```text
AR01
SMG01
SG01
SR01
GL01
```

Use values from WEAPON_DATA_SPEC.md.

## Required BPC_WeaponComponent Functions

```text
FindBestTarget
TryAutoFire
EquipWeapon
```

## Required BP_WeaponBase Functions

```text
InitializeWeapon
TryFire
Fire
Reload
FinishReload
ResetCanFire
```

## Required BP_ProjectileBase Functions

```text
InitializeProjectile
CalculateFinalDamage
Explode
```

## Required Interface

```text
BPI_Damageable.ReceiveDamage
```

Inputs:

```text
DamageAmount
DamageType
InstigatorActor
HitLocation
KnockbackForce
bCritical
```

## Required Dispatchers

```text
OnWeaponChanged
OnAmmoChanged
OnReloadStarted
OnReloadFinished
OnWeaponFired
```

## Hard Rules

1. No permanent target-search Event Tick.
2. No GetAllActorsOfClass every frame.
3. No DataTable lookup every shot.
4. No projectile direct mutation of enemy CurrentHealth.
5. No projectile damage to OwnerActor.
6. No ammo UI Property Binding.
7. No ammo UI Tick polling.
8. No direct DataTable mutation for runtime upgrades.
9. Preserve XP/death integration already present.
10. Use the actual player and actual enemy Blueprints.
11. Do not claim completion based only on asset existence.
12. Compile modified Blueprints.
13. Save modified assets.
14. Run runtime validation where possible.

## Required Runtime Validation

Must validate:

```text
AR01:
Damage = 18
FireRate = 6
FireInterval ≈ 0.1667
Magazine = 30
Reload = 1.5 sec

Crit:
18 × 1.5 = 27

SG01:
ProjectileCount = 6

SR01:
PierceCount = 2
Total possible valid target hits = 3

GL01:
ExplosionRadius = 260
```

## Required Completion Report

Return:

```text
[CREATED]
Exact asset paths

[MODIFIED]
Exact asset paths

[ACTIVE PLAYER]
Resolved class/path

[ACTIVE ENEMY]
Resolved base class/path

[WEAPON DATA]
Rows + key values

[FUNCTIONS]
Created/modified functions

[DISPATCHERS]
Created/modified dispatchers

[INTERFACE]
Damage path

[RUNTIME TEST RESULTS]
Targeting
Fire rate
Damage
Crit
Ammo
Reload
Shotgun
Pierce
Explosion
Runtime upgrade

[PERFORMANCE AUDIT]
Target search Tick = 0
GetAllActorsOfClass per-frame = 0
DataTable lookup per shot = 0
Ammo UI polling Tick = 0
Ammo Property Binding = 0

[BLUEPRINT COMPILE]
Pass / Fail per asset

[FAILURES]
Every unverified or failed requirement
```

Any unverified requirement must be marked NOT VERIFIED, never silently treated as complete.
