# MutantStreet — UE5.8 竖屏战斗 HUD / 拖拽道具蓝图完整实现规范

## 0. 目标与硬约束

设计基准：`1080 × 1920`，9:16。
实现要求：

- UI 只用 Anchor + Alignment + 固定局部 SizeBox；禁止用负 Padding 修位置。
- 图标必须放在固定尺寸 `SizeBox` 中，`Horizontal Alignment=Center`、`Vertical Alignment=Center`。
- 所有外层 CanvasSlot 的 Position / Size 都使用整数值，避免半像素偏移。
- HUD 不使用 Tick Property Binding；全部由 Event Dispatcher 推送。
- 拖拽落点以 `PointerEvent.ScreenSpacePosition` 为唯一坐标源，DragVisual 不参与世界坐标换算。
- 任何道具预览都由独立 `BP_PlacementManager` 管理，UI 只发送 ItemID + 屏幕坐标。
- 移动端触摸与鼠标共用同一 DragDrop 流程。
- Scene 放置前必须做地面 Trace + Footprint Overlap 双重验收。
- UI Icon 和世界预览绝不使用同一个 Transform；避免图标位置影响世界落点。

---

# 1. 必建蓝图资产

## UI
- `WBP_GameHUD`
- `WBP_BossHUD`
- `WBP_ZoneRail`
- `WBP_ZoneNode`
- `WBP_TopRightCounters`
- `WBP_PlayerStatus`
- `WBP_WeaponBar`
- `WBP_WeaponSlot`
- `WBP_ItemPlacementBar`
- `WBP_ItemSlot`
- `WBP_DragVisual`
- `WBP_PlacementHint`

## Gameplay
- `BP_PlacementManager`
- `BP_PlacementPreview`
- `BPI_Placeable`
- `BPC_PlayerInventory`
- `BPC_WeaponSystem`
- `BPC_PlayerStats`
- `BPC_EncounterState`

## Struct
`ST_PlacementItemData`
- ItemID : Name
- DisplayName : Text
- Icon : Texture2D
- PlaceActorClass : Class<Actor>
- Footprint : Vector2D
- ZOffset : Float
- RotationStep : Float

`ST_WeaponHUDData`
- WeaponID : Name
- DisplayName : Text
- Icon : Texture2D
- CurrentAmmo : Int
- ReserveAmmo : Int
- Level : Int
- bSelected : Bool

---

# 2. WBP_GameHUD — 精准布局树

Root:
`CanvasPanel_Root`
- Visibility = Visible
- RenderTransform = Identity
- Padding = 0
- Clipping = ClipToBounds

## 2.1 BossHUD
Anchor = `(0.5, 0.0)`
Alignment = `(0.5, 0.0)`
Position = `(0, 18)`
Size = `(560, 86)`
ZOrder = 20

## 2.2 ZoneRail
Anchor = `(0.0, 0.5)`
Alignment = `(0.0, 0.5)`
Position = `(18, -10)`
Size = `(112, 1050)`
ZOrder = 15

## 2.3 TopRightCounters
Anchor = `(1.0, 0.0)`
Alignment = `(1.0, 0.0)`
Position = `(-18, 18)`
Size = `(212, 182)`
ZOrder = 25

## 2.4 PlayerStatus
Anchor = `(0.0, 1.0)`
Alignment = `(0.0, 1.0)`
Position = `(18, -18)`
Size = `(224, 202)`
ZOrder = 25

## 2.5 WeaponBar
Anchor = `(0.5, 1.0)`
Alignment = `(0.5, 1.0)`
Position = `(-22, -18)`
Size = `(552, 218)`
ZOrder = 25

## 2.6 ItemPlacementBar
Anchor = `(1.0, 0.5)`
Alignment = `(1.0, 0.5)`
Position = `(-18, 120)`
Size = `(238, 790)`
ZOrder = 30

说明：所有 CanvasSlot 的 SizeToContent = false。

---

# 3. WBP_WeaponSlot — 图标绝不偏移

固定 Size：`132 × 202`

Widget Tree:
`Overlay_Root`
1. `IMG_Frame` — Fill
2. `IMG_SelectedGlow` — Fill，默认 Collapsed
3. `VerticalBox_Content`
   - `SizeBox_Icon` = `112 × 112`
       - `Overlay_Icon`
         - `IMG_Weapon`
   - `TXT_Ammo`
   - `TXT_Name`

`IMG_Weapon`：
- HAlign = Center
- VAlign = Center
- Brush DrawAs = Image
- Desired Size 不直接写；尺寸由 SizeBox 统一控制。
- RenderTransform Pivot = `(0.5,0.5)`
- Translation = `(0,0)`
- Scale = `(1,1)`

函数 `SetWeaponData(Data)`：
1. `IMG_Weapon.SetBrushFromTexture(Data.Icon, MatchSize=false)`
2. `TXT_Name.SetText(Data.DisplayName)`
3. `TXT_Ammo.SetText(Format "{Current}/{Reserve}")`
4. `IMG_SelectedGlow.SetVisibility(Data.bSelected ? HitTestInvisible : Collapsed)`

绝对禁止：
- SetRenderTranslation 修正图标
- 负 Padding
- 每把武器单独调 Position
- MatchSize=true

---

# 4. WBP_ItemPlacementBar

Size：`238 × 790`

Tree:
`Border_BG`
  `VerticalBox`
   - `TXT_Title`  Height=42
   - `ScrollBox_Items`
      - 动态添加 `WBP_ItemSlot`

Construct:
1. `Inventory.GetPlaceableItems()`
2. ForEach ItemData:
   - CreateWidget `WBP_ItemSlot`
   - `InitItem(ItemData, Count)`
   - Bind `OnDragBegin`
   - Bind `OnDragCancel`
   - AddChild to ScrollBox

---

# 5. WBP_ItemSlot — 鼠标/触摸拖拽

Size：`206 × 138`

Tree:
`Overlay`
- `IMG_Frame`
- `HorizontalBox`
  - `SizeBox_Icon` = `92 × 92`
      - `IMG_ItemIcon`
  - `VerticalBox`
      - `TXT_ItemName`
      - `TXT_Count`
- `IMG_DisabledOverlay`

Icon Contract:
- `SizeBox_Icon.WidthOverride=92`
- `HeightOverride=92`
- IMG H/V = Center
- Translation = 0
- Scale = 1

变量:
- `ItemData : ST_PlacementItemData`
- `CurrentCount : int`

## Override OnMouseButtonDown
Nodes:

`OnMouseButtonDown(MyGeometry, MouseEvent)`
→ `GetEffectingButton`
→ Equal `LeftMouseButton`
→ Branch
→ True:
`DetectDragIfPressed(MouseEvent, Self, LeftMouseButton)`
→ Return

## Override OnTouchStarted
`OnTouchStarted(MyGeometry, TouchEvent)`
→ `DetectDragIfPressed(TouchEvent, Self, LeftMouseButton)`
→ Return

## Override OnDragDetected
1. Branch `CurrentCount > 0`
2. CreateWidget `WBP_DragVisual`
3. `DragVisual.SetIcon(ItemData.Icon)`
4. CreateDragDropOperation `BP_DragDropOperation`
5. Payload:
   - ItemID
   - ItemData
6. DefaultDragVisual = DragVisual
7. Pivot = CenterCenter
8. Offset = `(0,0)`
9. `GetPlacementManager -> BeginPlacement(ItemData)`
10. Return Operation

重要：不要把鼠标起点减去 Widget Absolute Position。UE DragDrop 自己维护 DragVisual；世界坐标始终直接读取 PointerEvent.ScreenSpacePosition。

---

# 6. WBP_DragVisual

固定 Size：`96 × 96`

Tree:
`SizeBox 96×96`
  `Overlay`
   - `IMG_Glow`
   - `IMG_Icon`

设置：
- Visibility = HitTestInvisible
- Pivot = `(0.5,0.5)`
- RenderTranslation = 0
- Icon H/V Center

---

# 7. WBP_GameHUD DragOver / Drop

## OnDragOver
Inputs: MyGeometry, PointerEvent, Operation

1. Cast Operation → `BP_DragDropOperation`
2. `PointerEvent.GetScreenSpacePosition`
3. `PlacementManager.UpdatePlacement(ScreenPos)`
4. Return true

不要执行：
- `AbsoluteToLocal`
- DPI 除法
- ViewportScale 除法

原因：PlayerController 的 `DeprojectScreenPositionToWorld` 需要的是 Viewport Screen Space；保持同一坐标体系。

## OnDrop
1. Cast Operation
2. ScreenPos = PointerEvent.ScreenSpacePosition
3. `PlacementManager.CommitPlacement(ItemID, ScreenPos)`
4. Branch Success
5. True:
   - `Inventory.ConsumeItem(ItemID,1)`
   - `ItemPlacementBar.RefreshItemCount(ItemID)`
6. `PlacementManager.EndPlacement()`
7. Return Success

## OnDragCancelled
→ `PlacementManager.CancelPlacement()`

---

# 8. BP_PlacementManager

建议由 PlayerController 创建并持有引用。

变量：
- `PC : PlayerController`
- `PreviewActor : BP_PlacementPreview`
- `ActiveItemData`
- `bPlacementActive`
- `bCurrentValid`
- `CurrentWorldLocation`
- `CurrentYaw`
- `TraceDistance = 100000`
- `GroundTraceChannel = Visibility`（正式项目建议单独 PlacementGround Channel）

---

# 9. BeginPlacement(ItemData)

Nodes:
1. Set ActiveItemData
2. If IsValid PreviewActor → Destroy
3. SpawnActorDeferred `BP_PlacementPreview`
4. Preview.SetSourceClass(ItemData.PlaceActorClass)
5. FinishSpawning
6. Set bPlacementActive=true
7. Set CurrentYaw=0

Preview Actor：
- Collision Enabled = NoCollision
- Actor Hidden In Game = false
- 禁止参与任何 Overlap 校验

---

# 10. ScreenToWorldPlacement(ScreenPos) — 核心函数

Function Output:
- bHit
- HitLocation
- HitNormal

Nodes:

`PC.DeprojectScreenPositionToWorld(ScreenPos.X, ScreenPos.Y)`
→ WorldOrigin
→ WorldDirection

`TraceStart = WorldOrigin`
`TraceEnd = WorldOrigin + WorldDirection * 100000`

`LineTraceByChannel`
- TraceChannel = PlacementGround / Visibility
- TraceComplex = false
- Ignore Self = true
- ActorsToIgnore:
  - PreviewActor
  - PlayerPawn

Branch Hit
→ Location = Hit.ImpactPoint
→ Location.Z += ActiveItemData.ZOffset

可选网格：
`GridSize=10`
```
X = Round(Location.X / 10) * 10
Y = Round(Location.Y / 10) * 10
```

不要对 Z 网格化。

---

# 11. ValidatePlacement(Location, Yaw)

必须双重检测。

## 11.1 地面坡度
`Dot(HitNormal, UpVector)`
→ >= 0.92
否则 Invalid。

## 11.2 Footprint 占用
HalfExtent:
- X = ActiveItemData.Footprint.X * 0.5
- Y = ActiveItemData.Footprint.Y * 0.5
- Z = 50

`BoxOverlapActors`
Object Types:
- WorldStatic
- WorldDynamic
- Pawn

ActorsToIgnore:
- PlayerPawn
- PreviewActor

如果返回数组 Length > 0：
- Invalid

额外规则：
- 不允许放在 Boss 身上
- 不允许放在敌人身上
- 不允许放在路障/建筑碰撞内
- HealingStation 等可放置物自身 Actor Collision 必须走 Placeable Channel

---

# 12. UpdatePlacement(ScreenPos)

1. Branch bPlacementActive
2. `ScreenToWorldPlacement(ScreenPos)`
3. Branch bHit
4. Set PreviewActor Location
5. Set PreviewActor Rotation `(0,CurrentYaw,0)`
6. `ValidatePlacement`
7. Set bCurrentValid
8. PreviewActor.SetValidState(bCurrentValid)

颜色：
- Valid = Green
- Invalid = Red

注意：颜色只修改预览 Dynamic Material，不修改最终 Actor。

---

# 13. CommitPlacement(ItemID, ScreenPos)

1. `UpdatePlacement(ScreenPos)` 再验一次
2. Branch `bCurrentValid`
3. False → Return false
4. Inventory.HasItem(ItemID,1)
5. False → Return false
6. SpawnActor `ActiveItemData.PlaceActorClass`
   - Location = CurrentWorldLocation
   - Rotation = CurrentYaw
7. 调用 BPI_Placeable::OnPlaced(Player)
8. Return true

关键：Drop 时必须再次 Trace + Validate，不能相信上一帧的 Preview 状态。

---

# 14. 旋转放置

桌面：
- 鼠标滚轮或 `R`

移动端：
- 在 Preview 状态显示小旋转 Button

函数：
`RotatePlacement()`
```
CurrentYaw += RotationStep
if CurrentYaw >= 360:
    CurrentYaw -= 360
UpdatePlacement(LastPointerScreenPos)
```

---

# 15. BP_PlacementPreview

Components:
- SceneRoot
- PreviewVisual
- BoxComponent_Footprint（NoCollision，HiddenInGame）
- DynamicMaterial

函数 `SetSourceClass`：
最佳做法：
1. 每个 Placeable Actor 实现 `BPI_Placeable`
2. Interface 返回 `PreviewMesh / PreviewSprite / PreviewScale`
3. Preview Actor 根据类型设置 Visual

函数 `SetValidState(bool)`：
- True → Tint `(0.1,1,0.2,0.55)`
- False → Tint `(1,0.12,0.08,0.55)`

视觉：
- Translucent / Unlit
- Disable Depth Test = false
- Render CustomDepth 可选

---

# 16. PlayerController 初始化

`Event BeginPlay`
1. CreateWidget `WBP_GameHUD`
2. AddToViewport Z=0
3. Create/Find `BP_PlacementManager`
4. HUD.SetPlacementManager(Manager)
5. Bind PlayerStats / Weapon / Inventory / Encounter / Boss events
6. Set Input Mode Game And UI
   - WidgetToFocus = HUD
   - MouseLock = DoNotLock
   - HideCursorDuringCapture = false
7. Mobile 不显示 Mouse Cursor

---

# 17. Boss HUD

`WBP_BossHUD`
Size = 560×86

Tree:
Overlay
- BossPortrait 64×64
- ProgressBar 440×34
- TXT_BossName
- TXT_BossHP（可选）

函数:
`SetBossHealth(Current, Max)`
```
Percent = Clamp(Current / Max, 0, 1)
PB_HP.SetPercent(Percent)
```

不要 UMG Binding。

---

# 18. ZoneRail

VerticalBox:
- BossZone
- Z5
- Z4
- Z3
- Z2
- Z1

每节点 `112×148`

函数 `SetCurrentZone(Index)`：
- 当前节点：蓝色 Glow，Scale 1.0
- 其他节点：Glow Collapsed
- 已通过：降低 Saturation，可选
- BossZone 仅最终阶段高亮红色

禁止用 SetRenderTranslation 做选中动画；只改 Glow/Color。

---

# 19. TopRightCounters

Size 212×182

Rows:
- Pause Button = 72×72
- Kill Counter = 200×44
- Crystal Counter = 200×44

所有 Icon:
- SizeBox = 34×34
- H/V Center
- 文字与 icon 之间用 Spacer 8
- 不用 Overlay 随意拖位置

---

# 20. PlayerStatus

Size 224×202

HP:
- Heart Icon 44×44
- HP ProgressBar 160×24
- HP Text Overlay 在 Bar 中央

Level:
- TXT_Level 80×40
- XP ProgressBar 125×18

函数：
`SetHealth(Current,Max)`
`SetLevel(Level,CurrentXP,XPToNext)`

---

# 21. WeaponBar

HorizontalBox，4槽。
每槽固定 `132×202`，槽间 Spacer=8。

总宽：
`132*4 + 8*3 = 552`

这就是 WeaponBar 固定宽度 552 的原因，保证四把武器绝对不会发生累计偏移。

切枪：
Slot OnClicked → `WeaponSystem.SelectWeapon(Index)`

选中：
只显示 `IMG_SelectedGlow`，不要改变槽 Size，不要 Scale Up，否则相邻槽会产生视觉位移。

---

# 22. Event Dispatcher 接口

PlayerStats:
- OnHealthChanged(Current,Max)
- OnXPChanged(Current,Required)
- OnLevelChanged(Level)

WeaponSystem:
- OnWeaponSelected(Index)
- OnAmmoChanged(Index,Current,Reserve)
- OnWeaponInventoryChanged()

Inventory:
- OnItemCountChanged(ItemID,Count)

Encounter:
- OnZoneChanged(CurrentZone)
- OnKillChanged(Kills)
- OnCrystalChanged(Crystals)

Boss:
- OnBossSpawned
- OnBossHealthChanged(Current,Max)
- OnBossDefeated

HUD 只响应事件，不主动每帧查询。

---

# 23. 防止图标偏移的验收规则

每个可复用 Slot 必须检查：

1. Icon 外层必须存在唯一固定 SizeBox。
2. SizeBox 不允许 SizeToContent。
3. Image H/V Alignment = Center。
4. Render Translation 必须 `(0,0)`。
5. Render Scale 必须 `(1,1)`。
6. Pivot 必须 `(0.5,0.5)`。
7. Padding 只能为正值，且同类型 Slot 完全一致。
8. `SetBrushFromTexture(..., MatchSize=false)`。
9. Selected 状态不改变 Slot Size。
10. 所有 Canvas Position/Size 使用整数。
11. 图标透明 PNG 外围 Padding 由美术文件自己统一，不在 UMG 单独补偿。
12. 不允许为单个 Icon 写“特殊偏移”。

---

# 24. 必测分辨率

PIE / Mobile Preview：

- 1080×1920
- 720×1280
- 1440×2560
- 1080×2400
- iPhone 类安全区
- Android 挖孔屏

验收：
- 四武器槽中心线一致
- 右侧道具槽中心线一致
- BossBar TopCenter 不漂
- 左侧 ZoneRail 不进入 SafeZone
- DragVisual 中心跟手
- 世界 Preview 落点与手指/鼠标射线一致
- Drop 时不会因为 DPI Scale 产生偏移
