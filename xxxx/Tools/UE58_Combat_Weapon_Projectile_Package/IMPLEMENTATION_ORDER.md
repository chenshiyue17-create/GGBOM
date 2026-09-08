# Implementation Order

## Phase 1 — Data Foundation

Create:

```text
ST_WeaponData
DT_Weapons
BPI_Damageable
```

Populate initial weapons:

```text
AR01
SMG01
SG01
SR01
GL01
```

---

## Phase 2 — Projectile

Create:

```text
BP_ProjectileBase
```

Implement:

- InitializeProjectile
- ProjectileMovement
- overlap validation
- critical
- damage interface call
- piercing
- explosion
- unique hit tracking

Validate projectile independently.

---

## Phase 3 — Weapon

Create:

```text
BP_WeaponBase
```

Implement:

- InitializeWeapon
- TryFire
- Fire
- Reload
- projectile spawn
- shotgun projectile loop
- fire cooldown timer

---

## Phase 4 — Weapon Component

Create:

```text
BPC_WeaponComponent
```

Implement:

- CurrentWeapon
- CurrentTarget
- Timer based FindBestTarget
- Timer based TryAutoFire
- runtime modifiers
- weapon event dispatchers

---

## Phase 5 — Player Integration

Attach:

```text
BPC_WeaponComponent
```

to the actual player pawn/character used by GameMode.

Equip AR01 by default.

---

## Phase 6 — Enemy Integration

Modify real enemy base Blueprint:

```text
Implement BPI_Damageable
```

Route:

```text
ReceiveDamage
→ Enemy health system
→ death
```

Do not duplicate a second health system if one already exists.

---

## Phase 7 — UI Integration

Bind:

```text
OnAmmoChanged
OnReloadStarted
OnReloadFinished
OnWeaponChanged
```

to WBP_GameHUD / WBP_SkillBar.

No Tick/property binding.

---

## Phase 8 — Gameplay Validation

Run all tests from:

```text
ACCEPTANCE_CHECKLIST.md
```

Do not claim completion unless required validation evidence is present.
