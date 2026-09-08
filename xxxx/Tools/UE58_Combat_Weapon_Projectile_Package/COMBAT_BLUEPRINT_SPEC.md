# Combat Blueprint Full Specification

# 1. BPC_WeaponComponent

职责：

- 管理 CurrentWeapon
- 定时寻找目标
- 自动瞄准
- 请求射击
- 切换武器
- 运行时升级属性
- 向 HUD 广播弹药和武器状态

## Variables

```text
CurrentWeapon : BP_WeaponBase Reference
CurrentTarget : Actor Reference

TargetSearchInterval : Float Default 0.15
FireRequestInterval  : Float Default 0.05

RuntimeDamageMultiplier          Float Default 1.0
RuntimeFireRateMultiplier        Float Default 1.0
RuntimeProjectileSpeedMultiplier Float Default 1.0
RuntimeCritChanceBonus           Float Default 0.0
RuntimeProjectileCountBonus      Integer Default 0
RuntimePierceBonus               Integer Default 0
```

## Dispatchers

```text
OnWeaponChanged
OnAmmoChanged
OnReloadStarted
OnReloadFinished
OnWeaponFired
```

Recommended `OnAmmoChanged` parameters:

```text
CurrentAmmo : Integer
MagazineSize : Integer
```

## BeginPlay

Use Timer, never permanent target-search Tick.

```text
BeginPlay
→ Set Timer FindBestTarget
  Looping = true
  Time = TargetSearchInterval

→ Set Timer TryAutoFire
  Looping = true
  Time = FireRequestInterval
```

---

# 2. FindBestTarget

Forbidden:

```text
Event Tick
→ GetAllActorsOfClass
```

Required approach:

```text
SphereOverlapActors
Radius = CurrentWeapon.AttackRange
Object Type / Class Filter = Enemy
```

Filter:

```text
IsValid
Alive
Damageable
Inside attack range
```

MVP priority:

```text
Nearest Enemy
```

Set:

```text
CurrentTarget
```

No target:

```text
CurrentTarget = None
```

---

# 3. TryAutoFire

```text
If CurrentWeapon invalid
    Return

If CurrentTarget invalid
    Return

If target outside CurrentWeapon.AttackRange
    Return

CurrentWeapon.TryFire(CurrentTarget)
```

Do not spawn bullets without a valid target.

---

# 4. BP_WeaponBase Variables

```text
WeaponData       : ST_WeaponData
OwnerCharacter   : BP_PlayerCharacter Reference
WeaponComponent  : BPC_WeaponComponent Reference

CurrentAmmo      : Integer
bCanFire         : Boolean
bReloading       : Boolean

MuzzleTransform / MuzzleSceneComponent
```

---

# 5. InitializeWeapon

Inputs:

```text
WeaponData
OwnerCharacter
WeaponComponent
```

Logic:

```text
Set WeaponData
Set OwnerCharacter
Set WeaponComponent

CurrentAmmo = WeaponData.MagazineSize

bCanFire = true
bReloading = false

Broadcast OnAmmoChanged
```

DataTable must be read during weapon setup/equip, not every shot.

---

# 6. TryFire

Input:

```text
TargetActor
```

Validation order:

```text
Owner valid?
Weapon Component valid?
Target valid?
bReloading == false?
bCanFire == true?
CurrentAmmo > 0?
```

If:

```text
CurrentAmmo <= 0
```

Then:

```text
Reload()
Return
```

Else:

```text
Fire(TargetActor)
```

---

# 7. Fire

Execution:

```text
Set bCanFire = false

CurrentAmmo -= 1
Broadcast OnAmmoChanged

Calculate Aim Direction

Calculate Final Weapon Stats

Spawn Projectile(s)

Play Muzzle VFX
Play Fire SFX

Broadcast OnWeaponFired

FireInterval =
1 / Max(FinalFireRate, 0.01)

Set Timer
→ ResetCanFire
after FireInterval
```

Use Timer instead of Delay where practical.

---

# 8. Spread

For single projectile:

```text
AimDirection
→ Apply random yaw within SpreadAngle
```

For 2.5D top-down project:

Primarily use yaw spread.

Do not add unnecessary pitch variance unless gameplay requires it.

---

# 9. ProjectileCount / Shotgun

```text
FinalProjectileCount =
WeaponData.ProjectileCount
+
RuntimeProjectileCountBonus
```

If > 1:

```text
ForLoop 0 → FinalProjectileCount - 1
→ Generate independent spread
→ Spawn one projectile
```

---

# 10. Reload

Conditions:

```text
CurrentAmmo < MagazineSize
bReloading == false
```

Start:

```text
bReloading = true
bCanFire = false

Broadcast OnReloadStarted
```

Timer:

```text
WeaponData.ReloadTime
```

Finish:

```text
CurrentAmmo = WeaponData.MagazineSize

bReloading = false
bCanFire = true

Broadcast OnAmmoChanged
Broadcast OnReloadFinished
```

Recommended game rule:

```text
Infinite reserve ammo
+
Magazine reload rhythm
```

No reserve-ammo inventory required for MVP.

---

# 11. BP_ProjectileBase Components

```text
SceneRoot
├── Visual (Sprite / Flipbook / Mesh)
├── SphereCollision
└── ProjectileMovement
```

ProjectileMovement handles movement.

Do not manually move projectile via Event Tick unless absolutely necessary.

---

# 12. BP_ProjectileBase Variables

```text
Damage              Float
Speed               Float
OwnerActor          Actor Reference

PierceRemaining     Integer

CritChance          Float
CritMultiplier      Float

Knockback           Float

bExplosive          Boolean
ExplosionRadius     Float

HitActors            Actor Array
```

`HitActors` prevents the same projectile repeatedly damaging the same actor in overlap edge cases.

---

# 13. InitializeProjectile

Inputs:

```text
Damage
Speed
OwnerActor
PierceCount
CritChance
CritMultiplier
Knockback
bExplosive
ExplosionRadius
```

Logic:

```text
Set variables

ProjectileMovement.InitialSpeed = Speed
ProjectileMovement.MaxSpeed = Speed
```

---

# 14. Projectile Spawn

Spawn Transform:

```text
Location = Weapon Muzzle Location
Rotation = AimDirection.Rotation
```

After Spawn:

```text
InitializeProjectile(...)
```

Do not create separate projectile subclasses only to hard-code different damage numbers.

---

# 15. BPI_Damageable

Function:

```text
ReceiveDamage
```

Inputs:

```text
DamageAmount      Float
DamageType        Name / Enum
InstigatorActor   Actor
HitLocation       Vector
KnockbackForce    Float
bCritical         Boolean
```

All damageable targets implement this:

```text
Normal Enemy
Elite
Boss
Breakable Prop
Explosive Barrel
```

Projectile must never directly mutate enemy CurrentHealth.

---

# 16. Projectile Hit

On SphereCollision overlap:

```text
OtherActor == OwnerActor?
    Ignore

Already in HitActors?
    Ignore

Does Implement BPI_Damageable?
    Continue
```

Add to:

```text
HitActors
```

If explosive:

```text
Explode()
Destroy projectile
```

Otherwise:

```text
CalculateFinalDamage
→ BPI_Damageable.ReceiveDamage
```

Then process PierceRemaining.

---

# 17. Critical

```text
RandomFloat 0..1
```

If:

```text
Random <= CritChance
```

Then:

```text
bCritical = true
FinalDamage = Damage * CritMultiplier
```

Else:

```text
bCritical = false
FinalDamage = Damage
```

Example:

```text
Damage = 18
CritMultiplier = 1.5
→ Crit Damage = 27
```

---

# 18. Pierce

Definition:

```text
PierceCount =
number of EXTRA targets allowed after first valid hit
```

After each valid non-explosive hit:

```text
If PierceRemaining > 0
    PierceRemaining -= 1
    Continue flying
Else
    Destroy Actor
```

Example:

```text
PierceCount = 2

Target 1 hit
→ remaining 1

Target 2 hit
→ remaining 0

Target 3 hit
→ projectile destroyed
```

This means total possible valid targets = 3.

---

# 19. Explosive Projectile

On impact:

```text
SphereOverlapActors
Radius = ExplosionRadius
Filter damageable enemies
```

For each unique target:

```text
ReceiveDamage
```

MVP:

```text
100% damage throughout radius
```

Optional later:

```text
Multiplier =
Clamp(
    1 - Distance / ExplosionRadius,
    0.3,
    1
)
```

---

# 20. Damage Pipeline

Keep MVP damage formula simple:

```text
Weapon BaseDamage
        ×
RuntimeDamageMultiplier
        ↓
Projectile Damage
        ↓
Critical Roll
        ↓
Target DamageTakenMultiplier
        ↓
FinalDamage
        ↓
BPI_Damageable.ReceiveDamage
```

Do not introduce armor, penetration, elemental resistances, level suppression, random damage ranges, etc. before MVP is validated.

---

# 21. Ammo UI Event Flow

```text
Weapon fires/reloads
→ OnAmmoChanged
→ WBP_GameHUD
→ WBP_SkillBar / Ammo Widget
→ Update text
```

Forbidden:

```text
UMG Event Tick
→ Get Weapon
→ Get CurrentAmmo
```

Forbidden:

```text
Text / Progress Property Binding for ammo
```

---

# 22. Performance Contract

Mandatory:

```text
Target search via Timer
ProjectileMovement handles movement
Weapon data cached on equip
UI event-driven
```

Forbidden:

```text
GetAllActorsOfClass every frame
Projectile target search every frame
Weapon DataTable row lookup every shot
UMG Tick polling ammo
Projectile Tick manual movement unless justified
```
