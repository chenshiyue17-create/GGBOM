# GGBOM Player Visibility Handoff

- Time: 2026-09-02T19:30:43
- Status: PASS
- Map: /Game/GGBOM/Maps/MAP_GGBOM_Main
- Player Blueprint: /Game/Blueprints/Player/BP_Player_Medic
- Runtime Player Actor: Player_Medic_Runtime
- The player must be visible near bottom center at Location=(0,-20,-560).
- Keep PaperFlipbookComponent visible, not hidden in game, sort priority 2000.
- Runtime camera note: Player0 possession can steal the level camera. Keep the orthographic camera component on BP_Player_Medic so the possessed pawn renders the same X-Z gameplay plane.
- Visual acceptance screenshot: output/current_runtime_window_front_after_pawn_camera_fix.png
- Screenshot result: Standalone window shows portrait street, enemy pack, and visible player near bottom center.
