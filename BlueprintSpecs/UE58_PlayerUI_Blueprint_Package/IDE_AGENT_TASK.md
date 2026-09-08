# IDE Agent Task — UE5.8 Player UI

## Mission

Implement the player HUD health/experience subsystem directly inside the UE5.8 project.

Do not only generate instructions.
Do not stop at pseudo-code.
Do not claim completion unless project assets are actually created/modified and validated.

## Required Assets

```text
/Content/Blueprints/UI/WBP_GameHUD
/Content/Blueprints/UI/WBP_PlayerStatus
/Content/Blueprints/UI/WBP_HealthBar
/Content/Blueprints/UI/WBP_ExperienceBar
/Content/Blueprints/UI/WBP_LevelUp
```

Modify the project's real player Blueprint.

Expected reference:

```text
/Content/Blueprints/Characters/BP_PlayerCharacter
```

If the actual player Blueprint has a different path/name, locate the active pawn/character used by the current GameMode and modify that real asset instead.

## Required Player Data

```text
MaxHealth
CurrentHealth

CurrentLevel
CurrentXP
XPToNextLevel
```

## Required Functions

```text
ApplyPlayerDamage
AddExperience
CalculateXPRequirement
```

## Required Dispatchers

```text
OnHealthChanged
OnExperienceChanged
OnLevelUp
```

## Required UI Functions

```text
WBP_HealthBar.UpdateHealth
WBP_ExperienceBar.UpdateExperience
WBP_PlayerStatus.UpdateHealth
WBP_PlayerStatus.UpdateExperience
```

## Hard Rules

1. No permanent UMG Event Tick for HP/XP.
2. No ProgressBar Property Binding.
3. No direct enemy mutation of player CurrentHealth.
4. No fake placeholder implementation.
5. No completion report without validation.
6. Preserve existing project functionality.
7. Do not duplicate an existing equivalent health/XP system; integrate with it.
8. Use Event Dispatchers for UI updates.
9. HUD must perform an initial state refresh after binding.
10. Experience overflow must be preserved.

## Validation Evidence Required

Agent must report:

```text
[CREATED]
Exact asset paths

[MODIFIED]
Exact asset paths

[PLAYER VARIABLES]
Names + types + defaults

[DISPATCHERS]
Names + parameters

[FUNCTIONS]
Names + input/output

[HUD BINDINGS]
What is bound to what

[TEST RESULTS]
HP 100 -> damage 30 -> HP 70
XP 20/40 -> 50%
XP overflow level test
multi-level XP test

[PERFORMANCE AUDIT]
Property Binding count for HP/XP = 0
Tick polling for HP/XP = 0

[FAILURES]
Anything not validated
```

Any unvalidated requirement must be explicitly marked FAILED or NOT VERIFIED.
