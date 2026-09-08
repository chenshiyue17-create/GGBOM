# P03→P13 Direct-Write 总执行顺序

P03 Components
→ P04 Player
→ P05 Combat/Weapons/Projectiles
→ P06 Enemy AI
→ P07 XP/Card
→ P08 Props/Placement
→ P09 Stages/Waves
→ P10 Boss
→ P11 UMG
→ P12 GameFlow/Save
→ P13 Optimization/Android

每次只给Agent一个阶段。
调用模板：
`执行 Pxx_DIRECT_EXEC.md；唯一数据源 Pxx_DIRECT_SPEC.json；节点只按 Pxx_NODE_RECIPES.md；不要解释；直接创建/Compile/Save/PIE；最后只返回状态行。`

失败模板：
`继续当前Pxx，仅修复 BLOCKING_ERROR=<错误>；不要重做已PASS资产；修复后重跑当前Gate。`

禁止：
- 自行重规划
- C++
- 用Compile成功冒充功能PASS
- 跳过PIE/真机Gate
