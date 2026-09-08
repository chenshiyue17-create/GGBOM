# Combat / Weapon / Projectile Acceptance Checklist

## Targeting

- [ ] COMBAT-001 Player automatically finds a valid enemy target.
- [ ] COMBAT-002 No projectile is spawned with no valid target.
- [ ] COMBAT-003 Target outside AttackRange is not fired at.
- [ ] COMBAT-004 Target search does not use GetAllActorsOfClass every frame.
- [ ] COMBAT-005 Target search runs from Timer or equivalent controlled cadence.

## Fire Rate

- [ ] FIRE-001 AR01 FireRate=6 produces ~0.1667 sec fire interval.
- [ ] FIRE-002 Fire cooldown prevents duplicate shots above intended rate.
- [ ] FIRE-003 FinalFireRate respects RuntimeFireRateMultiplier.
- [ ] FIRE-004 Weapon cannot fire during reload.

## Ammo

- [ ] AMMO-001 AR01 starts with 30 ammo.
- [ ] AMMO-002 One shot reduces CurrentAmmo by 1.
- [ ] AMMO-003 CurrentAmmo never goes below 0.
- [ ] AMMO-004 CurrentAmmo=0 triggers reload.
- [ ] AMMO-005 Reload ends with CurrentAmmo=MagazineSize.
- [ ] AMMO-006 OnAmmoChanged broadcasts after shot and reload.
- [ ] AMMO-007 Ammo UI is event-driven.

## Projectile

- [ ] PROJECTILE-001 Projectile spawns at real muzzle location.
- [ ] PROJECTILE-002 Projectile moves in calculated aim direction.
- [ ] PROJECTILE-003 Projectile speed matches initialized runtime speed.
- [ ] PROJECTILE-004 Projectile does not damage OwnerActor.
- [ ] PROJECTILE-005 Same projectile does not repeatedly damage same actor due to overlap jitter.
- [ ] PROJECTILE-006 Projectile calls BPI_Damageable instead of changing enemy health directly.

## Damage

- [ ] DAMAGE-001 Damage=18, no crit, target multiplier=1 -> 18 final damage.
- [ ] DAMAGE-002 Damage=18, CritMultiplier=1.5 -> 27 critical damage.
- [ ] DAMAGE-003 RuntimeDamageMultiplier modifies projectile damage.
- [ ] DAMAGE-004 Target health is clamped by target health system.
- [ ] DAMAGE-005 Death occurs through existing enemy death flow.

## Pierce

- [ ] PIERCE-001 PierceCount=0 allows one valid target hit.
- [ ] PIERCE-002 PierceCount=2 permits up to 3 valid target hits.
- [ ] PIERCE-003 PierceRemaining decrements only on valid damageable hits.
- [ ] PIERCE-004 Projectile destroys after final allowed hit.

## Explosion

- [ ] EXPLOSION-001 GL projectile calls Explode on impact.
- [ ] EXPLOSION-002 Explosion uses ExplosionRadius.
- [ ] EXPLOSION-003 Each valid enemy is damaged at most once per explosion.
- [ ] EXPLOSION-004 Owner is excluded.
- [ ] EXPLOSION-005 Projectile is destroyed after explosion.

## Shotgun

- [ ] SHOTGUN-001 SG01 spawns 6 projectiles before runtime bonuses.
- [ ] SHOTGUN-002 Each pellet receives independent spread.
- [ ] SHOTGUN-003 Spread is primarily yaw-based for 2.5D top-down combat.
- [ ] SHOTGUN-004 RuntimeProjectileCountBonus works.

## Data

- [ ] DATA-001 ST_WeaponData contains required fields.
- [ ] DATA-002 AR01 / SMG01 / SG01 / SR01 / GL01 rows exist.
- [ ] DATA-003 Weapon DataTable is cached on equip/setup.
- [ ] DATA-004 DataTable row is not fetched every shot.
- [ ] DATA-005 Runtime upgrades do not modify source DataTable.

## Performance

- [ ] PERF-COMBAT-001 No target-search Event Tick.
- [ ] PERF-COMBAT-002 No GetAllActorsOfClass every frame.
- [ ] PERF-COMBAT-003 No projectile target-search Tick.
- [ ] PERF-COMBAT-004 ProjectileMovement handles standard movement.
- [ ] PERF-COMBAT-005 No HP/Ammo UI polling Tick.
- [ ] PERF-COMBAT-006 No Ammo Property Binding.
- [ ] PERF-COMBAT-007 No DataTable lookup every shot.

## Regression Scenario

1. Spawn player with AR01.
2. Spawn one Shambler at valid range.
3. Confirm auto target acquisition.
4. Confirm AR01 fires automatically.
5. Confirm first hit deals 18 damage when not critical.
6. Confirm Shambler HP 45 requires ~3 normal hits.
7. Confirm ammo decreases.
8. Fire until magazine is empty.
9. Confirm reload starts.
10. Confirm reload completes after 1.5 sec.
11. Confirm ammo returns to 30.
12. Equip SG01.
13. Confirm 6 projectiles spawn per shot.
14. Equip SR01.
15. Confirm PierceCount=2 behavior.
16. Equip GL01.
17. Confirm radius damage.
18. Apply +15% damage upgrade.
19. Confirm source DataTable stays unchanged.
20. Confirm runtime damage reflects multiplier.
