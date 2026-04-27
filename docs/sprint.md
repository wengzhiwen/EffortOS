# Sprint 26: 参数变更触发数据重算

**状态**: 已完成
**目标**: 参数变更后自动重算受影响活动的指标

## 任务清单

- [x] S26-1: 修复 _compute_metrics 使用活动日期对应的参数（而非最新参数）
- [x] S26-2: 实现后台重算机制（params_service.py 的 mark_activities_for_recalc）
- [x] S26-3: TSS 计算策略优化：功率覆盖率 < 50% 时心率兜底
- [x] S26-4: 新增 /api/params/recalc-status 端点
- [x] S26-5: 设置页面显示重算进度
- [x] S26-6: 移除基于速度的 EF 计算（对训练分析无价值）

## 评估小结

Sprint 26 完成了参数变更触发数据重算：
- `_compute_metrics` 改用 `get_effective_params(user, activity.start_time)` 获取对应日期的参数
- 参数变更后后台线程逐个重算受影响活动（测试环境同步执行）
- TSS 策略：功率覆盖率 ≥ 50% 用功率 TSS，否则心率 TSS 兜底
- 设置页面实时显示重算进度（轮询 /api/params/recalc-status）
- 移除了基于速度的效率因子计算
- 采纳提案「参数设置与数据重算」
- 128 个测试全部通过
