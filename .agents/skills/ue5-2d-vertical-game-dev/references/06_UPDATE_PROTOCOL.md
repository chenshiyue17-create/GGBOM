# 06 AI 幂等更新协议

## UPDATE ≠ APPEND
Mutation operation 必须明确：CREATE / UPDATE / REPLACE / REMOVE / MIGRATE。
默认：存在 UPDATE，相同 NO-OP，不存在 CREATE。

## Stable ID + GenerationKey
所有生成对象和可重复 Component/Binding 需要 Stable ID 或 GenerationKey。
禁止以显示名、文件名后缀、数组位置判断身份。

## Idempotency
同一任务执行 N 次，需求未变时项目最终状态必须相同：F(F(Project))=F(Project)。
禁止 xxx_1 / xxx_2 / xxx_New / xxx_Final。

## Find-or-Create / Find-or-Update
Component、Ability、WeaponSlot、AnimationMapping、Tag、Binding、Timer、VFX 配置必须先按 Stable ID 查找。

## Array规则
业务唯一对象禁止盲目 Add。优先 TMap<Key,Config>；使用 Array 时必须 FindByStableID 后 Update-or-Add。

## Event/Delegate/Timer
BindingCount目标=1。更新时 RemoveExisting+Add 或唯一 Handle。Timer 用稳定 TimerHandle；已存在只更新参数。

## Blueprint Generated Area
禁止“BeginPlay尾部追加式更新”。Generated逻辑隔离在稳定 Function/Generated Component/标记区域，可重建 Generated Area，但不触碰 User Area。
Concrete Blueprint 默认 Data Only 以最大化规避节点累积。

## Field-level Patch
普通修改默认 STRICT_PATCH，只写允许 Field Mask；其他字段必须 Preserve。
例如 HP 100→120，只允许 Stats.MaxHealth 改变。

## Mutation Modes
- STRICT_PATCH：普通字段修改，默认模式
- MERGE：按 Stable ID 合并新增内容
- REGENERATE_GENERATED：仅重建生成器拥有区域
- MIGRATION：Schema/StableID 架构迁移

## Before/After Snapshot + Diff
修改前后必须保存 Snapshot，生成 Diff。
若 Diff 出现未授权字段 → UPDATE_GUARD_FAIL。

## Scope Diff Guard
用户只改 Damage，则实际 Diff 不得额外修改 Art/Animation/Projectile/UI 等。

## Duplicate Scan
每次变更后检查：StableID、Component、Definition、Delegate、Timer、Ability、WeaponSlot、GameplayTag、AnimationMapping、WidgetBinding。

## Revision
每个 Definition：SchemaVersion + ContentRevision。NO-OP 不增加 Revision。

## Migration
升级 Generator/Schema 不得重建所有对象。按 SchemaVersion 做增量字段迁移并 Preserve Unknown/User Fields。

## Transaction
BEGIN TRANSACTION → Patch → Validate → Compile/Test → Diff Guard → COMMIT；失败 → ROLLBACK。
禁止留下半更新对象。
