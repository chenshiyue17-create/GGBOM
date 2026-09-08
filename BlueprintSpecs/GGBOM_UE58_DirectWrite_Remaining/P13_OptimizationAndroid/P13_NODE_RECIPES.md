# P13 NODE RECIPES

Pool Map<Class,Array<Actor>>

Acquire(Class):
Find inactive
found→ActivateFromPool→return
not found→Spawn→Activate→return

Release:
ClearAllTimersForObject
DeactivateToPool
Hidden=true
Collision=false
Tick=false
AddUnique inactive array

Projectile Impact/LifeEnd→Pool.Release
VFX animation finished→Release
Pickup consumed→Release
Enemy death完成→Release

Stress记录：
AvgFPS
GameThread ms
GPU ms
Memory MB
Actor counts
无真机启动证据不得PASS
