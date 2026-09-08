# Player UI Acceptance Checklist

## Health

- [ ] UI-PLAYER-001 Game start shows player health bar.
- [ ] UI-PLAYER-002 CurrentHealth=100, MaxHealth=100 -> Percent=1.0.
- [ ] UI-PLAYER-003 ApplyPlayerDamage(30) from 100 -> CurrentHealth=70.
- [ ] UI-PLAYER-004 After above damage -> health Percent=0.7.
- [ ] UI-PLAYER-005 Health never below 0.
- [ ] UI-PLAYER-006 Health never above MaxHealth.
- [ ] UI-PLAYER-007 Health reaches 0 -> death flow fires.
- [ ] UI-PLAYER-008 Enemy does not directly Set CurrentHealth.

## Experience

- [ ] UI-XP-001 CurrentXP=20, XPToNextLevel=40 -> Percent=0.5.
- [ ] UI-XP-002 XP reaches requirement -> CurrentLevel increments.
- [ ] UI-XP-003 Overflow XP is preserved.
- [ ] UI-XP-004 A large XP reward can trigger multiple level-ups.
- [ ] UI-XP-005 OnLevelUp fires for each level gained.
- [ ] UI-XP-006 OnExperienceChanged fires after XP processing.
- [ ] UI-XP-007 Level text matches CurrentLevel.
- [ ] UI-XP-008 WBP_LevelUp opens on level-up.

## Initialization

- [ ] UI-INIT-001 HUD binds all player dispatchers.
- [ ] UI-INIT-002 HUD explicitly refreshes health immediately after bind.
- [ ] UI-INIT-003 HUD explicitly refreshes experience immediately after bind.
- [ ] UI-INIT-004 Health bar is correct before taking first damage.
- [ ] UI-INIT-005 XP bar is correct before collecting first XP.

## Performance

- [ ] PERF-UI-001 No Property Binding on Health Percent.
- [ ] PERF-UI-002 No Property Binding on Experience Percent.
- [ ] PERF-UI-003 No Event Tick polling health.
- [ ] PERF-UI-004 No Event Tick polling experience.
- [ ] PERF-UI-005 UI updates via Event Dispatchers.
- [ ] PERF-UI-006 No repeated GetPlayerCharacter/Cast during runtime updates.

## Regression Test

1. Start game.
2. Confirm HP=100%.
3. Apply 30 damage.
4. Confirm HP=70%.
5. Apply 1000 damage.
6. Confirm HP=0 and death executes.
7. Restart.
8. Add 20 XP with threshold 40.
9. Confirm XP=50%.
10. Add 30 XP.
11. Confirm level increases and overflow XP remains.
12. Add enough XP for 2+ levels.
13. Confirm multiple upgrades occur correctly.
14. Confirm no UMG tick/property bindings were introduced.
