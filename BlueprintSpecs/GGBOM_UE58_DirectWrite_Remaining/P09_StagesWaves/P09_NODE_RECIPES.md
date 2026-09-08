# P09 NODE RECIPES

StartStage:
StageState=Combat
KillCount=0 Elapsed=0 VenomKills=0
Timer1s→Elapsed++→CheckClearCondition
WaveSpawner.StartWave

NotifyEnemyKilled:
KillCount++
Venom→VenomKills++
Hound→AliveHounds=max(0,-1)
CheckClearCondition

Check:
START Kill>=20
Z1 Elapsed>=90 && VenomKills>=3
Z2 TerminalDestroyed && AliveHounds<=0
Z3 Kill>=150
BOSS BossDefeated
若true且State==Combat→CompleteStage

Complete:
State=Clear→StopSpawner→Reward→State=ExitOpen→Exit.Unlock
