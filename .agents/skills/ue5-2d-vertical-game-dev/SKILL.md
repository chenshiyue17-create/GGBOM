---
name: ue5-2d-vertical-game-dev
description: End-to-end UE5.8 2D/2.5D top-down portrait mobile game development SOP for AI-assisted production. Enforces project scan before edits, Blueprint parent/child architecture, data-driven object definitions, Chinese editor labels, object-centric dashboards, source-art to Paper2D Sprite/Flipbook pipeline, idempotent update/patch rules, dependency impact analysis, duplicate prevention, validation gates, PIE/build/performance evidence, and complete definition-of-done for characters, weapons, projectiles, abilities, enemies, bosses, UI, VFX, levels, waves, upgrades, and runtime content.
---

# UE5.8 2D俯视角竖屏游戏开发总 Skill

本 Skill 是项目级规则，不是单个功能教程。

## 最高优先级原则
1. 任何任务先扫描现有工程，再修改。
2. 能 UPDATE 不 CREATE；能 PATCH 不 REGENERATE；能复用不复制。
3. Blueprint：父类管共性，Component 管能力，DataAsset 管对象差异。
4. Concrete Blueprint 默认 Data Only；禁止新角色复制旧角色业务图。
5. 所有 UE Editor 对人属性必须中文 DisplayName / Category / ToolTip；内部 Key 保持英文稳定。
6. 美术属于使用它的对象 Definition；全局 Art Registry 只扫描/统计/验证，不作为第二配置源。
7. Source Art 与 UE Runtime Art 必须分层。角色源图只是生产输入，最终运行资产必须是 Paper2D Sprite + Flipbook + Animation Profile + Runtime Binding。
8. 所有更新必须幂等。存在则更新，相同则 NO-OP，不存在才创建；禁止 xxx_1 / xxx_New / xxx_Final 式重复。
9. 所有修改必须生成 Before/After Diff，超出 Field Mask 的变更拒绝提交。
10. 没有真实 Compile/PIE/Build 证据不得写 PASS。
11. Placeholder 不等于完成。
12. FINAL=READY 只有在本对象/功能的全部关键 DoD Gate 通过后才允许。

## 强制执行顺序
PROJECT SCAN → OBJECT RESOLVE → DEPENDENCY/IMPACT → CHANGE PLAN → MUTATION MODE → PATCH/MERGE → DUPLICATE SCAN → COMPILE → RUNTIME TEST → DIFF GUARD → COMMIT/ROLLBACK → FINAL REPORT

详细规则见 references/。
