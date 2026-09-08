# P05 NODE RECIPES

WeaponInventory.RequestFire:
Branch bCanFire&&CurrentAmmo>0
True→bCanFire=false→Ammo-1→OnAmmoChanged→OnFireRequested(AimDir,Data)
→SetTimer(FireInterval/Max(.1,FireRateMultiplier))→bCanFire=true

Player OnFireRequested:
ForLoop 0..(PPS+BonusProjectiles-1)
→RandomSpread
→SpawnActorDeferred ProjectileClass
→Build RuntimeData(Damage*Multiplier, Speed*Multiplier, Pierce+BonusPierce, DamageTag...)
→InitializeProjectile→FinishSpawn

Projectile Initialize:
SetFlipbook Flight
Movement Speed
Velocity Forward*Speed
SetLifeSpan3

Overlap:
若Other已在HitActors return
若Implements BPI_Combat:
 TakeCombatDamage
 Add HitActors
 PierceRemaining--
 ExplosionRadius>0→SphereOverlap去重AOE
 Pierce<=0→Impact→Destroy

TestDummy:
TakeCombatDamage→HP-=Damage→bKilled=HP<=0
Pistol 4 shots on HP100 =>0
