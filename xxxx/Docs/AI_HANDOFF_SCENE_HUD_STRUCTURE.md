# GGBOM Scene + HUD Structure Handoff

- Time: 2026-09-02T17:52:51
- Map: /Game/GGBOM/Maps/MAP_GGBOM_Main
- PureBlueprint: True
- FolderSetSuccess: 35/35
- LegacyWorldHUDArchived: 15
- LegacyWorldHUDHidden: 15
- WidgetBlueprints: {'WBP_GGBOM_CombatHUD': True, 'WBP_HUD_WeaponSlot': True, 'WBP_HUD_TacticalSlot': True, 'WBP_HUD_ZoneTracker': True}
- HUDPresenterBlueprint: True

## Planned Outliner Structure

- `00_Core_Runtime`
- `01_Camera`
- `02_Stage_Map`
- `03_Player`
- `04_Enemies`
- `04_Enemies/Boss`
- `05_Defense_Lanes`
- `06_Combat_Props`
- `07_Pickups_VFX`
- `08_HUD_Runtime`
- `90_ARCHIVE_Legacy_WorldSpace_HUD`
- `99_Engine_Runtime`

## Rule for next AI

Do not place screen HUD as PaperSpriteActor in the gameplay world. Use `/Game/GGBOM/UI/WBP_GGBOM_CombatHUD` as the screen HUD root and keep any old world-space HUD actors under `90_ARCHIVE_Legacy_WorldSpace_HUD` hidden.
