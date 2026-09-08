# P03 NODE RECIPES

## Health.ApplyDamage
Entry DamageAmount,DamageCauser
→ Branch(bIsInvulnerable OR bDeathTriggered OR DamageAmount<=0)
True→Return 0
False:
Remaining=DamageAmount
If CurrentShield>0:
  Absorb=Min(CurrentShield,Remaining)
  CurrentShield-=Absorb
  Remaining-=Absorb
  OnShieldChanged
Applied=Min(CurrentHP,Remaining)
CurrentHP=Clamp(CurrentHP-Applied,0,MaxHP)
OnHealthChanged
OnDamaged(Applied,DamageCauser)
If CurrentHP<=0 AND !bDeathTriggered:
  bDeathTriggered=true
  OnDeath(DamageCauser)
Return Applied

## Experience.AddXP
CurrentXP+=Max(0,Amount)
While CurrentXP>=XPToNext:
 CurrentXP-=XPToNext
 Level+=1
 XPToNext=Round(100*Pow(GrowthMultiplier,Level-1))
 OnLevelChanged
 OnLevelUpRequested
OnXPChanged

## Test
Health Init(100,20)
Damage30 => Shield0 HP90
Damage90 => HP0 DeathCount1
Damage10 => DeathCount仍1
AddXP250 => Level>=2
Inventory Add TEST 5, Consume2 =>3
Nanite卡 MaxStack3，前3次true，第4次false
全真→PrintString P03_COMPONENTS_OK，否则P03_COMPONENTS_FAIL
