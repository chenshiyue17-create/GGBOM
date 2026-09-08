# UI / Placement QA Checklist

## Layout
- [ ] Reference viewport 1080×1920 matches JSON.
- [ ] All CanvasSlot positions and sizes are integers.
- [ ] All icons sit inside fixed SizeBox.
- [ ] No negative padding exists in reusable slots.
- [ ] No individual icon has RenderTranslation correction.
- [ ] Selected weapon does not change slot size.
- [ ] Item bar does not overlap weapon bar at 1080×1920.

## Drag & Drop
- [ ] Mouse drag begins on left click.
- [ ] Touch drag begins on touch.
- [ ] DragVisual pivot is CenterCenter.
- [ ] World preview uses raw ScreenSpacePosition.
- [ ] No AbsoluteToLocal conversion is applied before Deproject.
- [ ] Drop performs final trace and final overlap validation.
- [ ] Invalid placement does not consume inventory.
- [ ] Cancel drag destroys/hides preview.
- [ ] Successful placement consumes exactly 1 item.

## World Validation
- [ ] Ground trace ignores Player and Preview.
- [ ] Footprint overlap ignores Preview.
- [ ] Cannot place inside WorldStatic.
- [ ] Cannot place on enemy/pawn.
- [ ] ZOffset comes from DataTable.
- [ ] RotationStep comes from DataTable.

## Event Driven HUD
- [ ] Health updates through dispatcher.
- [ ] XP/Level updates through dispatcher.
- [ ] Ammo updates through dispatcher.
- [ ] Weapon selection updates through dispatcher.
- [ ] Item count updates through dispatcher.
- [ ] Boss health updates through dispatcher.
- [ ] Zone progression updates through dispatcher.
- [ ] No UMG property Tick Binding remains.

## Resolution
- [ ] 720×1280
- [ ] 1080×1920
- [ ] 1440×2560
- [ ] 1080×2400
- [ ] SafeZone device preview
