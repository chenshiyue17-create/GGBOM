# UE5.8 Player UI Blueprint Package

目标：在 UE5.8 纯蓝图项目中实现角色 HUD 核心状态 UI：

- 玩家血条
- 玩家经验条
- 当前等级
- 受伤刷新
- 获取经验刷新
- 连续升级
- 升级三选一事件入口
- 全程事件驱动
- 禁止 UMG Tick 轮询
- 禁止 ProgressBar Property Binding

## 推荐目录

```text
Content/
└── Blueprints/
    ├── Characters/
    │   └── BP_PlayerCharacter
    └── UI/
        ├── WBP_GameHUD
        ├── WBP_PlayerStatus
        ├── WBP_HealthBar
        ├── WBP_ExperienceBar
        └── WBP_LevelUp
```

## 核心数据流

```text
Damage
→ BP_PlayerCharacter.ApplyPlayerDamage()
→ OnHealthChanged
→ WBP_GameHUD
→ WBP_PlayerStatus
→ WBP_HealthBar.UpdateHealth()

XP Pickup
→ BP_PlayerCharacter.AddExperience()
→ OnExperienceChanged
→ WBP_GameHUD
→ WBP_PlayerStatus
→ WBP_ExperienceBar.UpdateExperience()

XP 满
→ LevelUp
→ OnLevelUp
→ WBP_GameHUD
→ WBP_LevelUp
```

## 实施顺序

1. 创建 WBP_HealthBar
2. 创建 WBP_ExperienceBar
3. 创建 WBP_PlayerStatus
4. 修改 BP_PlayerCharacter
5. 创建 Event Dispatcher
6. 创建 WBP_GameHUD
7. 绑定 Dispatcher
8. 主动初始化 UI
9. 接入伤害
10. 接入经验拾取
11. 接入升级三选一
12. 执行 ACCEPTANCE_CHECKLIST.md 验收

详细节点见 `PLAYER_UI_BLUEPRINT_SPEC.md`。
