# UE5.8 2D俯视角竖屏游戏 AI-First 开发 SOP v1.0

这是一个“防 AI 越改越乱”的项目级 SOP 包，可作为 ChatGPT Skills、AI IDE 项目规则或团队开发规范使用。

## 核心目标
不是让 AI “写出代码”，而是让 AI 在长期 UE5.8 项目中持续增量开发时保持：
- 全局观念
- 父子蓝图一致
- 数据单一真相源
- 中文可编辑属性
- 美术/动画直接配置在对应对象模块
- Paper2D Runtime 资产完整
- 幂等更新，不重复追加
- 依赖影响可追踪
- Dashboard 不是空壳
- 真实 Compile / PIE / Android / Performance 验证

## 推荐使用方式
### ChatGPT Skills
上传整个 ZIP。

### AI IDE / Codex / Agent
优先读取：
1. SKILL.md
2. SOP_MASTER.md
3. references/08_AI_TASK_PROTOCOL.md
4. references/06_UPDATE_PROTOCOL.md
5. 当前任务对应对象模块规则

## 目录
- `SOP_MASTER.md`：总开发协议
- `references/01_PROJECT_ARCHITECTURE.md`：模块与全局控制层
- `references/02_BLUEPRINT_INHERITANCE.md`：父子蓝图、组件化、重复逻辑
- `references/03_DATA_OWNERSHIP_AND_CHINESE_PROPERTIES.md`：数据所有权与属性汉化
- `references/04_OBJECT_WORKBENCH_DASHBOARD.md`：对象工作台和具体图表结构
- `references/05_SOURCE_ART_AND_PAPER2D_PIPELINE.md`：源美术与 Paper2D Runtime 资产
- `references/06_UPDATE_PROTOCOL.md`：幂等更新、Patch、Diff、Rollback
- `references/07_CHANGE_IMPACT_MATRIX.md`：修改影响范围
- `references/08_AI_TASK_PROTOCOL.md`：AI 每次任务强制步骤
- `references/09_VALIDATION_GATES.md`：验证门
- `references/10_TEST_AND_PERFORMANCE.md`：自动测试和性能
- `references/11_NAMING_AND_FOLDERS.md`：目录与命名
- `references/12_DEFINITION_OF_DONE.md`：对象级完成标准
- `references/13_OBJECT_SCHEMAS.md`：角色/武器/敌人等对象字段结构
- `templates/`：扫描、变更、最终报告、CSV模板
- `machine/`：机器可读 JSON Schema / Change Impact Rules
