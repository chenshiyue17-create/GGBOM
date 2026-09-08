# P10 NODE RECIPES

HealthChanged:
Pct=CurrentHP/MaxHP
if Pct<=.30 && Phase!=Phase3→EnterPhase3
else if Pct<=.70 && Phase==Phase1→EnterPhase2

EnterPhase:
Health.Invulnerable=true
StopAI
Play Enrage
Set Phase
Delay animation duration
Health.Invulnerable=false
ResumeAI

SkillBase:
Start→ShowTelegraph→Timer→WindUp→ActivateDamage→ActiveDuration→DisableDamage→Recover→Cleanup

BioShield:
Spawn3 crystals
Boss invulnerable=true
Crystal death count++
>=3→invulnerable=false

Death:
Phase_Defeated→StopTimers→NoCollision→PlayDeath→StageManager BossDefeated
