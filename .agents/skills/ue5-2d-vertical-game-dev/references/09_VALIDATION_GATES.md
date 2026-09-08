# 09 Validation Gates

## Architecture Gate
- Parent正确
- InheritanceDepth合格
- Concrete Data-Only优先
- Component复用
- DuplicateLogic=0
- UserLogicPreserved

## Data Gate
- StableID唯一
- SchemaVersion合法
- 中文DisplayName/Category/Tooltip
- Hard Range合法
- Reference完整
- Unknown/User Fields保留

## Art Gate
Source Art和Runtime Art分开：
- Source尺寸/Alpha/Grid/Scale
- Import
- Sprite
- Flipbook
- Animation Profile
- Binding
- Runtime

## Object Completeness Gate
对象必须同时检查 Gameplay、Art、Animation、VFX、SFX、UI、Dashboard、Runtime。

## Update Safety Gate
- Allowed Field Mask
- UnexpectedChanges=0
- DuplicateScan=0
- Cardinality合法
- NO numbered duplicate assets

## Evidence Gate
未执行 = NOT EXECUTED，不得写 PASS。

## Placeholder Gate
Default Cube / Default Material / White Texture / Debug Widget / Text-only 临时UI / Temporary Sprite / Placeholder VFX 一律 PLACEHOLDER，不计 PASS。
