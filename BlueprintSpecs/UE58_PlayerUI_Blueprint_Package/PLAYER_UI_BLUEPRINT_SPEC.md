# Player UI Blueprint Full Specification

## 1. WBP_HealthBar

### Widget Tree

```text
Overlay_Root
├── PB_HealthDelayed   [optional]
├── PB_Health
├── IMG_HPFrame
└── HorizontalBox_HPText
    ├── TXT_CurrentHealth
    ├── TXT_Slash
    └── TXT_MaxHealth
```

### Required Variables

```text
PB_Health              ProgressBar
TXT_CurrentHealth      TextBlock
TXT_MaxHealth          TextBlock
```

### Function: UpdateHealth

Inputs:

```text
CurrentHealth : Float
MaxHealth     : Float
```

Logic:

```text
SafeMax = Max(MaxHealth, 1.0)

Percent =
Clamp(
    CurrentHealth / SafeMax,
    0.0,
    1.0
)

PB_Health.SetPercent(Percent)

TXT_CurrentHealth.SetText(
    Round(CurrentHealth)
)

TXT_MaxHealth.SetText(
    Round(MaxHealth)
)
```

Do not use Property Binding.

---

## 2. WBP_ExperienceBar

### Widget Tree

```text
Overlay_Root
├── PB_Experience
├── IMG_EXPFrame
└── TXT_Experience [optional]
```

### Required Variables

```text
PB_Experience : ProgressBar
TXT_Experience : TextBlock [optional]
```

### Function: UpdateExperience

Inputs:

```text
CurrentXP      : Float
XPToNextLevel  : Float
CurrentLevel   : Integer
```

Logic:

```text
SafeXPMax = Max(XPToNextLevel, 1.0)

Percent =
Clamp(
    CurrentXP / SafeXPMax,
    0.0,
    1.0
)

PB_Experience.SetPercent(Percent)
```

Optional text:

```text
LV.{CurrentLevel}
```

or

```text
{Round(CurrentXP)} / {Round(XPToNextLevel)}
```

---

## 3. WBP_PlayerStatus

### Suggested Layout

```text
CanvasPanel
└── HorizontalBox_Status
    ├── Border_Avatar
    │   └── IMG_Avatar
    └── VerticalBox_Info
        ├── HorizontalBox_Level
        │   └── TXT_Level
        ├── WBP_HealthBar
        └── WBP_ExperienceBar
```

### Variables

```text
PlayerRef : BP_PlayerCharacter Object Reference
```

### Function: UpdateHealth

Inputs:

```text
CurrentHealth
MaxHealth
```

Implementation:

```text
WBP_HealthBar.UpdateHealth(CurrentHealth, MaxHealth)
```

### Function: UpdateExperience

Inputs:

```text
CurrentXP
XPToNextLevel
CurrentLevel
```

Implementation:

```text
WBP_ExperienceBar.UpdateExperience(
    CurrentXP,
    XPToNextLevel,
    CurrentLevel
)

TXT_Level.SetText(
    "LV." + CurrentLevel
)
```

---

## 4. BP_PlayerCharacter Variables

Required:

```text
MaxHealth          Float    Default 100
CurrentHealth      Float    Default 100

CurrentLevel       Integer  Default 1
CurrentXP          Float    Default 0
XPToNextLevel      Float    Default 40
```

Optional:

```text
bIsDead            Boolean
```

---

## 5. BP_PlayerCharacter Event Dispatchers

### OnHealthChanged

Parameters:

```text
CurrentHealth : Float
MaxHealth     : Float
```

### OnExperienceChanged

Parameters:

```text
CurrentXP      : Float
XPToNextLevel  : Float
CurrentLevel   : Integer
```

### OnLevelUp

Parameters:

```text
NewLevel : Integer
```

---

## 6. BeginPlay Initialization

```text
Event BeginPlay
→ Set CurrentHealth = MaxHealth
→ Call OnHealthChanged(CurrentHealth, MaxHealth)
→ Call OnExperienceChanged(CurrentXP, XPToNextLevel, CurrentLevel)
```

UI must also perform an explicit initial pull after binding, because dispatchers may fire before the HUD is created.

---

## 7. Function: ApplyPlayerDamage

Input:

```text
DamageAmount : Float
```

Logic:

```text
If bIsDead == true
    Return

NewHealth =
Clamp(
    CurrentHealth - DamageAmount,
    0,
    MaxHealth
)

Set CurrentHealth = NewHealth

Call OnHealthChanged(
    CurrentHealth,
    MaxHealth
)

If CurrentHealth <= 0
    → Die()
```

Rules:

- Enemy blueprints must not directly Set CurrentHealth.
- All player damage must go through ApplyPlayerDamage.
- Health must always remain within 0..MaxHealth.

---

## 8. Function: AddExperience

Input:

```text
Amount : Float
```

Logic:

```text
CurrentXP += Max(Amount, 0)

WHILE CurrentXP >= XPToNextLevel:

    CurrentXP -= XPToNextLevel

    CurrentLevel += 1

    XPToNextLevel =
        CalculateXPRequirement(CurrentLevel)

    Call OnLevelUp(CurrentLevel)

END WHILE

Call OnExperienceChanged(
    CurrentXP,
    XPToNextLevel,
    CurrentLevel
)
```

If Blueprint WhileLoop is used, ensure `XPToNextLevel > 0`.

---

## 9. Function: CalculateXPRequirement

Recommended short-session curve:

```text
Level 1 -> 40
Level 2 -> 65
Level 3 -> 90
Level 4 -> 120
Level 5 -> 155
Level 6 -> 195
Level 7 -> 240
Level 8 -> 290
```

For MVP, formula is acceptable:

```text
XPRequired =
Round(
    40 * Pow(1.35, CurrentLevel - 1)
)
```

Final production version should move this data to a DataTable.

---

## 10. WBP_GameHUD

### Widget Tree

```text
CanvasPanel_Root
├── WBP_PlayerStatus
├── WBP_WaveInfo
├── WBP_BossHealth
├── WBP_SkillBar
├── WBP_VirtualJoystick
└── WBP_PauseButton
```

### Variables

```text
PlayerRef : BP_PlayerCharacter Object Reference
```

### Event Construct

```text
Event Construct
→ Get Owning Player Pawn
→ Cast BP_PlayerCharacter
→ Set PlayerRef

→ Bind Event to PlayerRef.OnHealthChanged
→ Bind Event to PlayerRef.OnExperienceChanged
→ Bind Event to PlayerRef.OnLevelUp

→ WBP_PlayerStatus.UpdateHealth(
      PlayerRef.CurrentHealth,
      PlayerRef.MaxHealth
  )

→ WBP_PlayerStatus.UpdateExperience(
      PlayerRef.CurrentXP,
      PlayerRef.XPToNextLevel,
      PlayerRef.CurrentLevel
  )
```

---

## 11. Custom Event: EV_UI_HealthChanged

Parameters:

```text
CurrentHealth
MaxHealth
```

Logic:

```text
WBP_PlayerStatus.UpdateHealth(
    CurrentHealth,
    MaxHealth
)
```

---

## 12. Custom Event: EV_UI_ExperienceChanged

Parameters:

```text
CurrentXP
XPToNextLevel
CurrentLevel
```

Logic:

```text
WBP_PlayerStatus.UpdateExperience(
    CurrentXP,
    XPToNextLevel,
    CurrentLevel
)
```

---

## 13. Custom Event: EV_UI_LevelUp

Input:

```text
NewLevel
```

Logic:

```text
Create Widget WBP_LevelUp
→ Add To Viewport
→ Set Game Paused(true)
```

When player selects an upgrade:

```text
Apply Upgrade
→ Remove From Parent
→ Set Game Paused(false)
```

---

## 14. Performance Contract

Forbidden:

```text
Event Tick
→ Get Player
→ Read Health
→ Set Percent
```

Forbidden:

```text
ProgressBar Percent Binding
```

Required:

```text
Data changes
→ Event Dispatcher
→ UI update once
```

This is mandatory for mobile performance.

---

## 15. Optional Delayed Damage Bar

Do not block MVP on this.

Variables:

```text
PB_HealthDelayed
TargetHealthPercent
DelayedHealthPercent
```

Recommended implementation:

- On health loss, immediately update PB_Health.
- Trigger short Widget Animation or Timer.
- PB_HealthDelayed lerps toward actual health.
- Do not create permanent Tick polling.

---

## 16. Runtime Flow

```text
BP_Enemy
   │
   └── causes damage
            ↓
BP_PlayerCharacter
   ├── ApplyPlayerDamage
   ├── AddExperience
   ├── OnHealthChanged
   ├── OnExperienceChanged
   └── OnLevelUp
            ↓
       WBP_GameHUD
            ↓
     WBP_PlayerStatus
       ├── WBP_HealthBar
       └── WBP_ExperienceBar
```
