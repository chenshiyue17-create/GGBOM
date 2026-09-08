# P08 DIRECT EXEC

前置：P07_STATUS=PASS

不要解释，不要重规划。读取 `P08_DIRECT_SPEC.json`，严格按以下顺序直接施工：

1. 创建DestructibleBase和10类Prop数据/子类。
2. Intact→Damaged≤50%→Destroyed0。
3. 爆炸桶严格Radius250 Damage200；其他数值为平衡种子。
4. 创建5个Placeable和DT_PlacementItems。
5. Pointer ScreenSpacePosition直接Deproject；禁止DPI二次除法。
6. Trace→Grid→SlopeDot>=0.92→BoxOverlap。
7. Drop必须重新Validate，成功才Consume inventory。
8. 测Barrier 8→7；非法Drop仍8；爆炸桶AOE正确。
9. 日志P08_PROP_PLACE_OK。

最终只返回：
P08_STATUS=PASS/FAIL
ASSET_ERRORS=n
COMPILE_ERRORS=n
RUNTIME_ERRORS=n
ACCESSED_NONE=n
BLOCKING_ERROR=NONE/<text>
NEXT_GATE=<as defined in TEST_SPEC>
