# Quick Commands

审核单个蓝图：
使用 ue5-blueprint-auditor 审核 /Game/Blueprints/BP_PlayerCharacter；只审计不要修改。

审核一个系统：
使用 ue5-blueprint-auditor 审核“武器系统”；检查资产、结构、节点、PIE、联动、日志。

审核 UMG：
使用 ue5-blueprint-auditor 审核 UI/UMG；检查布局、绑定、Tick、输入、分辨率。

审核网络：
使用 ue5-blueprint-auditor 审核多人复制；测试 Listen Server + Client；只审计。

审核当前改动：
使用 ue5-blueprint-auditor 审核本次 Blueprint 改动；发现第一个 BLOCKER 就停止。

完整审核：
使用 ue5-blueprint-auditor 全量审核项目蓝图；continue_on_failure=true；输出全部缺陷。

复审：
使用 ue5-blueprint-auditor 复审上次失败项，并只跑受影响回归测试。

允许临时测试：
使用 ue5-blueprint-auditor 审核目标；AUDIT_ALLOW_TEMP_TESTS=true；
临时资产只能放 /Game/Tests/AuditTemp/。
