# P07 NODE RECIPES

Pickup:
进入Magnet范围→TargetPlayer=Player,bMagnet=true
Tick only if bMagnet→VInterpConstantTo→SetLocation
玩家Overlap→Experience.AddXP(XPAmount)→Destroy

DrawThree:
GetRows→Filter CanApplyCard→Weighted rarity→Random candidate→AddUnique→Remove candidate→直到3

Nanite:
Health.MaxHP+=25
Health.CurrentHP+=25
RegenModifier+=1.5

Corrosive:
ToxinDmgPct+=0.15
BonusPierce+=1

Multishot:
BonusProjectiles+=2
FireRateMultiplier*=1.20
SpreadBonus+=5

Test:
消费Zombie XP10
人工AddXP触发升级
Draw3必须Unique
Force Nanite→MaxHP125
全真→P07_XP_CARD_OK
