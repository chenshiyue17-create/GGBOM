# UE5 Blueprint Auditor — 通用版

这是一个通用 UE5 Blueprint 审核 Skill，不绑定任何具体项目、玩法、2D/3D 或开发阶段。

支持：
- Actor / Pawn / Character
- ActorComponent / SceneComponent
- GameMode / GameState / PlayerState / GameInstance
- PlayerController / AIController
- Blueprint Interface / Function Library / Macro Library
- Level Blueprint
- UMG / CommonUI
- Animation Blueprint / State Machine / Montage
- Enhanced Input
- AI / BT / Blackboard 依赖
- SaveGame
- DataTable / DataAsset / Gameplay Tags
- Multiplayer replication / RPC
- Blueprint 性能
- PIE / Functional Test / Packaged Build / Device Evidence

## 安装

将整个文件夹：
`ue5-blueprint-auditor`

放进支持 Skill 的 AI IDE/Agent 的 skills 目录。

入口：
`SKILL.md`

## 最简调用

`使用 ue5-blueprint-auditor 审核当前 Blueprint 改动；只审计不要修改。`

或：

`使用 ue5-blueprint-auditor 审核 /Game/Blueprints/BP_PlayerCharacter。`

## 项目自定义验收

推荐项目根目录维护：
`UE5_AUDIT_CONTRACT.json`

格式参考：
- `contracts/UE5_AUDIT_CONTRACT_SCHEMA.json`
- `examples/GENERIC_HEALTH_CONTRACT.json`

如果没有自定义 Contract，Skill 会执行通用结构、逻辑、运行时、日志和性能审核；没有明确业务预期的项目行为会标成 `UNSPECIFIED`，不会凭空猜数值。
