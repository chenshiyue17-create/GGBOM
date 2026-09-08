# P12 NODE RECIPES

StartNewRun:
FlowState=Loading
CurrentStageID=START
RunCoins=0
bReviveAvailable=true
OpenLevel Start

Player BeginPlay:
Health.RestoreFull
Experience.ResetRunXP
CardModifiers.ClearRunCards
Inventory.Clear
WeaponRuntimeModifiers.Reset
GI.FlowState=Playing

AdvanceStage:
START→Z1→Z2→Z3→BOSS→HandleVictory

Death:
if ReviveAvailable→ShowRevive
else→HandleGameOver
AcceptRevive→ReviveAvailable=false→恢复HP→HandleRevive→Playing

Save:
DoesSaveGameExist Profile_0
Load else Create
Victory时只写persistent字段
SaveGameToSlot
