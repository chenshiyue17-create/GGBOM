# P11 NODE RECIPES

PlayerStatus Construct:
缓存Pawn/Components一次
Bind Health.OnHealthChanged→SetHealth
Bind XP.OnXPChanged→SetXP
无Tick

WeaponBar:
HorizontalBox 4 slots,每个SizeBox132x202
槽间Spacer8
OnWeaponChanged/AmmoChanged事件更新

Item Drag:
OnMouseDown→DetectDragIfPressed
OnDragDetected→Create DragVisual96→Payload ItemID→Placement.Begin
GameHUD OnDragOver→PointerEvent.ScreenSpacePosition→Placement.Update
OnDrop→Placement.Commit
Cancelled→Cancel

CardModal:
Open→Populate3
Select→CardManager.Apply→Remove→Unpause
Reroll→重新Draw3
Skip→Remove→Unpause

BossHUD:
BossSpawn event时Bind Health Dispatcher
禁止Tick GetAllActors
