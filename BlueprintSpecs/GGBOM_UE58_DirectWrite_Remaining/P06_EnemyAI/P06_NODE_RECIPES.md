# P06 NODE RECIPES

EnemyBase BeginPlay:
Health.Initialize(Data.MaxHP,0)
SetTimer AIThink 0.20 looping

Zombie:
Distance>AttackRange→Chase/AddMovementInput
else且!Cooldown→TakeCombatDamage(Target,12)→Cooldown Timer

Venom:
Dist>750→靠近
Dist<550→后退
否则Aim
Cooldown ready→Spawn BioAcid toward player，Damage28，Poison4s

Hound:
Dist<=450且Cooldown ready→快速位移/Pounce→Overlap Damage35 + Stun0.8
否则Sprint chase 420

BPI_Targetable:
CanBeTargeted=!Dead
Location=ActorLocation
Priority按JSON

Death:
OnDeath→State Dead→NoCollision→Clear AI Timer→PlayDeath→LootDrop.Request→Delay3→Destroy
