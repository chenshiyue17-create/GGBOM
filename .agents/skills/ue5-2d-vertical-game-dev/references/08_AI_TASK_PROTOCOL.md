# 08 AI 每次任务强制协议

## Step 01 PROJECT SCAN
读取 ProjectSnapshot/ObjectRegistry/DependencyGraph/ValidationReport；不可用则先运行生成器。

## Step 02 RESOLVE OBJECT
解析 StableID、Definition、Blueprint、Parent、Components、Art、Validation。

## Step 03 CLASSIFY
DATA_CHANGE / CONTENT_ADD / CAPABILITY_ADD / BUG_FIX / ART_CHANGE / ARCHITECTURE_REFACTOR。

## Step 04 SEARCH/REUSE
先找现有 Parent、Component、Definition、Runtime System、Source Art、Flipbook、VFX、SFX、UI。

## Step 05 IMPACT
读取 Change Impact Rules，列出 Direct/Affected/Indirect。

## Step 06 CHANGE PLAN
明确：REUSED / CREATED / UPDATED / REMOVED / FORBIDDEN_TO_TOUCH / REQUIRED_TESTS。

## Step 07 MUTATION MODE
默认 STRICT_PATCH；新增集合项用 MERGE；不得无理由 REGENERATE。

## Step 08 SNAPSHOT
保存 BeforeSnapshot + Revision。

## Step 09 EXECUTE
严格 Field Mask；Find-or-Update；相同则 NO-OP。

## Step 10 DUPLICATE SCAN
检查所有重复类型。

## Step 11 VALIDATE
Schema/Data/Asset/Blueprint/Dependency/Art/Runtime。

## Step 12 EXECUTE TEST
Blueprint Compile；按 Impact 运行测试 Harness；必要时 PIE/Standalone/Android/Performance。

## Step 13 DIFF
生成 Before/After Diff。

## Step 14 SCOPE GUARD
UnexpectedChanges必须=0，否则 Rollback。

## Step 15 COMMIT/ROLLBACK
通过才 Commit，失败 Rollback 或明确 MIGRATION_INCOMPLETE。

## Step 16 FINAL REPORT
必须输出 CREATED / UPDATED / REMOVED / REUSED / UNCHANGED / UNEXPECTED CHANGES / VALIDATED / NOT EXECUTED / FINAL。

## 范围纪律
修 Run_NE 只修 Run_NE 链；改 Damage 不重构 Weapon；新增 Sniper 不复制 Assault；增加共享能力做 Component；已支持能力只改 Definition。
