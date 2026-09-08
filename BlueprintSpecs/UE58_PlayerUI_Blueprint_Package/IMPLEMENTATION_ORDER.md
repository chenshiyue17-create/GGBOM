# Implementation Order

## Phase 1 — Player Data

Create/verify:

- MaxHealth
- CurrentHealth
- CurrentLevel
- CurrentXP
- XPToNextLevel

Create:

- OnHealthChanged
- OnExperienceChanged
- OnLevelUp

## Phase 2 — Player Logic

Implement:

- ApplyPlayerDamage
- AddExperience
- CalculateXPRequirement

Verify health clamp and XP overflow.

## Phase 3 — Widgets

Create:

1. WBP_HealthBar
2. WBP_ExperienceBar
3. WBP_PlayerStatus
4. WBP_LevelUp
5. WBP_GameHUD

## Phase 4 — Wiring

WBP_GameHUD:

- resolve real player pawn
- bind dispatchers
- initial health refresh
- initial XP refresh
- level-up popup handling

## Phase 5 — Gameplay Integration

Enemy damage:

```text
Enemy attack
→ player ApplyPlayerDamage
```

XP:

```text
Enemy dead
→ XP drop or direct reward
→ player AddExperience
```

## Phase 6 — Validation

Run every item in `ACCEPTANCE_CHECKLIST.md`.

Do not continue to later HUD systems until all mandatory checks pass.
