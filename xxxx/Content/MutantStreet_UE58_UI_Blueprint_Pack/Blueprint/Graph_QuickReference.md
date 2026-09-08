# Blueprint Graph Quick Reference

## WBP_ItemSlot.OnDragDetected
CurrentCount > 0
→ Create WBP_DragVisual
→ SetIcon
→ CreateDragDropOperation
→ Payload = ItemData
→ DefaultDragVisual = DragVisual
→ Pivot = CenterCenter
→ PlacementManager.BeginPlacement(ItemData)
→ Return

## WBP_GameHUD.OnDragOver
Operation Cast
→ PointerEvent.ScreenSpacePosition
→ PlacementManager.UpdatePlacement(ScreenPosition)
→ Return True

## WBP_GameHUD.OnDrop
Operation Cast
→ ScreenSpacePosition
→ PlacementManager.CommitPlacement(ItemID, ScreenPos)
→ Branch Success
→ Inventory.ConsumeItem(ItemID,1)
→ PlacementBar.RefreshItemCount
→ PlacementManager.EndPlacement
→ Return Success

## BP_PlacementManager.UpdatePlacement
Deproject ScreenPosition To World
→ LineTrace Ground
→ HitLocation + ZOffset
→ Optional XY Grid Snap
→ Validate GroundSlope
→ BoxOverlap Footprint
→ Set Preview Transform
→ SetValidState

## CommitPlacement
UpdatePlacement
→ bCurrentValid
→ Inventory.HasItem
→ SpawnActor
→ BPI_Placeable.OnPlaced
→ Return true
