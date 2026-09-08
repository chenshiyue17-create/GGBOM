# 多端开发与本次工具修复

## 同步和路径

源码通过 Git 同步，每台机器独立检出。用 `git pull --ff-only origin main` 获取更新；如有分歧先查看各端提交，不能用强制覆盖代替合并。`.gitattributes` 标记 UE/图片二进制并固定脚本换行。此次未迁移历史大文件到 LFS，避免要求所有终端立刻改变存储方式。

`.ggbom.local.json` 只存本机 UE 根目录或 `ue_bin`，不提交；环境变量 `GGBOM_UE_ROOT` / `GGBOM_UE_BIN` 优先。引擎、缓存、日志、新运行报告在本机保留，后者写入 `xxxx/Saved/GGBOM/`。不再把自动生成的新 PASS 覆盖到历史 ProjectState 快照。

运行 `python3 tools/dev.py --help` 查看入口，Windows 使用 `py -3` 或 `dev.cmd`。常用流程与测试仅用 Python 标准库；独立旧版美术 YAML 校验器仍需 PyYAML，且其成功只表示注册表字段校验，未验证美术文件哈希和视觉批准。

## 保存与应用

配置网页在保存前检查完整候选的敌人/武器/波次数据及可用效果引用，忽略前端 ArtInfo；Diff 由服务器计算而不是信任浏览器填写。支持字典与带唯一 Name 的数组差异计算；当前游戏数据 Schema 仍为按ID组织的字典。

单文件写入采用临时文件+替换。多表提交有旧版本 journal 和失败回滚；这不是面向任意外部读者的跨文件原子事务。不要在提交进行时使用外部编辑器或Git改写这些表。异常退出留下锁时，先确认没有配置/导入进程运行，再移除 `Content/Data/.ggbom-write.lock`；下次启动配置服务恢复 journal 中的完整旧版本。不要把 journal/锁提交到Git。

`config-plan` 展示可应用敌人及数值；`apply-enemy-defaults` / 网页按钮使用同一个执行路径：

1. 校验源数据并固定敌人配置哈希，生成独立run_id。
2. 在UE加载已有Blueprint类，预检查所有目标数值属性，未知字段/缺资产立即失败。
3. 设置MaxHealth、CurrentHealth初值、MoveSpeed、ContactDamage、ScoreReward（配置存在时）、ExpGemValue。
4. 回读CDO数值并保存对应资产；失败时尝试恢复原值，报告恢复错误。
5. 父进程验证退出码、本次run_id、配置哈希及状态，拒绝旧报告冒充本次成功。

**状态 APPLIED_EDITOR_DEFAULTS 仅证明本次编辑器属性回读和保存结果。尚未在实际UE5.8验证此路径；下一次编译/磁盘重载是否保持、BeginPlay是否覆盖属性、活动实例是否消费它们，都需要UE验收。** 对已有打开的编辑器，应先保存并关闭项目，再运行命令行资产应用，完成后重新打开检查，避免两个编辑器同时保存同一资产。

数值导入不会生成怪物、重建地图、删除变量或节点；不应用武器、波次、主角、美术或正在运行的实例。这些字段仍可编辑保存，但不能宣称已热更新到游戏。运行消费仍需迁移到唯一DataTable/DataAsset链路或其他已验证的运行数据绑定。

## 验收结果说明

- `validate` PASS：源码数据合法，不代表数值已经被游戏读取。
- `test` OK：离线工具行为通过，不代表蓝图、画面或设备性能通过。
- `snapshot_blueprint_structure.py`：现在只读取真实资产字节哈希，明确 structure_status=BLOCKED，退出2。原来按文件名推断结构的实现已移除。
- `validate_weapon_core_diff.py --before A --after B`：比较完整核心资产的字节快照，缺资产/缺哈希/同一个输入路径均拒绝。字节变化会失败，可能包含编辑器元数据变化；字节相等不能证明第三把武器可用。
- `dev.py preview weapon`：只打开已有Preview地图，不生成截图/批准。UI/敌人预览地图缺失时BLOCKED；指定asset_id选择功能未实现，也明确BLOCKED。
- `test_weapon_preview.py`、旧阶段构建/全量恢复/“定时截桌面即全流程通过”入口：返回BLOCKED而非虚假通过。
- `master_combat_system.py`：旧的全局参数覆盖/特效节点清空入口已退役；旧版本可在Git历史追溯。

## 本次仍未解决的运行问题

1. 活动蓝图的实际结构、编译和关联资源未连接UE回读。
2. `integrate_full_playable_game_flow.py` 等历史生成器仍含按帧位移、固定伤害及波次。它们不在支持的常用入口中。本次未执行这些生成器，也未重建其资产。后续应在真实UE图上迁移MoveSpeed×DeltaSeconds和数据驱动调度。
3. 其他历史诊断/修复脚本可能仍含旧路径或旧PASS；不应把它们作为新的唯一工作流。AGENTS.md和本文件规定当前入口。
4. 两套Projectile/Inventory、武器ID与数据表并存，需要确认当前激活引用后迁移，不能凭名称删除资产。
5. 美术批准、八方向子弹、单次伤害、升级暂停/UI、胜负和重开、Cook/Android帧时间与内存均未实测。

IDE下一项UE任务应读取当前Player/Projectile/Enemy/WaveManager图，确定实际运行数据源，做小范围迁移并提交新证据。不能用本轮离线OK更新所有Feature为PASS。
