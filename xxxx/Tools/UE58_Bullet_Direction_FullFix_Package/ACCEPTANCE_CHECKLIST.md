# Acceptance Checklist

## Visual Size

- [ ] SIZE-001 BulletFlipbook normal bullet Scale no longer 0.13.
- [ ] SIZE-002 Initial normal bullet Scale is around 0.03.
- [ ] SIZE-003 Normal projectile visible length <= ~15% player body width.
- [ ] SIZE-004 Collision size remains independent of visual scale.
- [ ] SIZE-005 Boss projectile visual size is not forced to normal bullet scale.

## Core Direction

- [ ] DIR-001 W -> projectile velocity +Z.
- [ ] DIR-002 A -> projectile velocity +X.
- [ ] DIR-003 S -> projectile velocity -Z.
- [ ] DIR-004 D -> projectile velocity -X.
- [ ] DIR-005 WA -> normalized (+X,+Z).
- [ ] DIR-006 WD -> normalized (-X,+Z).
- [ ] DIR-007 SA -> normalized (+X,-Z).
- [ ] DIR-008 SD -> normalized (-X,-Z).

## Last Aim

- [ ] AIM-001 Start default LastAimDirection matches initial idle direction.
- [ ] AIM-002 Move W then release -> LastAimDirection stays +Z.
- [ ] AIM-003 Move A then release -> LastAimDirection stays +X.
- [ ] AIM-004 Move S then release -> LastAimDirection stays -Z.
- [ ] AIM-005 Move D then release -> LastAimDirection stays -X.
- [ ] AIM-006 Diagonal release preserves diagonal direction.
- [ ] AIM-007 Input zero never sets LastAimDirection to zero.

## Physics

- [ ] PHY-001 ProjectileMovement default Velocity is not fixed +X.
- [ ] PHY-002 Actual trajectory comes from world Velocity.
- [ ] PHY-003 GravityScale=0.
- [ ] PHY-004 Actor Rotation does not determine trajectory.
- [ ] PHY-005 Direction is normalized before multiplying by speed.
- [ ] PHY-006 Cardinal speed and diagonal speed differ by <1%.

## Visual Direction

- [ ] VIS-001 BulletFlipbook visually points along TravelDirection.
- [ ] VIS-002 Visual rotation can be corrected with BulletVisualAngleOffset.
- [ ] VIS-003 Changing BulletVisualAngleOffset does not alter real trajectory.
- [ ] VIS-004 Projectile Actor rotation is not used to correct sprite orientation.

## Blueprint Cleanup

- [ ] CLEAN-001 br_shoot_up old trajectory branch removed/disconnected.
- [ ] CLEAN-002 br_shoot_down old trajectory branch removed/disconnected.
- [ ] CLEAN-003 pitch_val_side old trajectory logic removed/disconnected.
- [ ] CLEAN-004 rot_up/rot_down/rot_side no longer control movement.
- [ ] CLEAN-005 Only one unified projectile spawn/fire path remains.

## Spawn

- [ ] SPAWN-001 Muzzle uses LastAimDirection.
- [ ] SPAWN-002 Muzzle uses one formula instead of per-direction offsets.
- [ ] SPAWN-003 Projectile.InitializeProjectile receives same direction used by muzzle.
- [ ] SPAWN-004 No projectile spawns with zero direction.

## Runtime Matrix

- [ ] TEST-W-MOVE
- [ ] TEST-W-STOP
- [ ] TEST-WA-MOVE
- [ ] TEST-WA-STOP
- [ ] TEST-A-MOVE
- [ ] TEST-A-STOP
- [ ] TEST-SA-MOVE
- [ ] TEST-SA-STOP
- [ ] TEST-S-MOVE
- [ ] TEST-S-STOP
- [ ] TEST-SD-MOVE
- [ ] TEST-SD-STOP
- [ ] TEST-D-MOVE
- [ ] TEST-D-STOP
- [ ] TEST-WD-MOVE
- [ ] TEST-WD-STOP

## Compile

- [ ] COMPILE-001 BP_Player_Medic compiles.
- [ ] COMPILE-002 BP_ProjectileBase compiles.
- [ ] COMPILE-003 Both assets saved.
- [ ] COMPILE-004 No new Blueprint compile warnings caused by fix.

## Regression

- [ ] REG-001 Player movement still works.
- [ ] REG-002 Idle animation still works.
- [ ] REG-003 Run animation still works.
- [ ] REG-004 Attack animation still works.
- [ ] REG-005 Projectile collision still works.
- [ ] REG-006 Projectile lifetime still works.
