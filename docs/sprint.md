# Sprint 3: 指标计算引擎

**状态**: 已完成
**对应 Milestone**: M4
**目标**: 实现完整的运动指标计算，包括 TSS、NP、IF、分区统计和 PMC

## 任务清单

- [x] S3-1: NP/IF/VI/EF/Work 计算函数（功率衍生指标）
- [x] S3-2: HR_IF/hrTSS 计算函数（心率衍生指标）
- [x] S3-3: 分区时间统计计算（心率分区 + 功率分区）
- [x] S3-4: metrics_service 统一入口（根据运动类型选择计算策略）
- [x] S3-5: PMC 计算 — CTL/ATL/TSB 指数加权移动平均
- [x] S3-6: 上传后自动计算指标（集成到上传流程）
- [x] S3-7: PMC API 端点（GET /api/pmc）

## 评估小结

Sprint 3 全部完成。实现了完整的运动指标计算引擎：

**功率衍生指标**：NP（标准化功率）、IF（强度因子）、VI（变异性指数）、EF（效率因子）、Work（总做功 kJ）

**心率衍生指标**：HR_IF（心率强度因子）、hrTSS（心率 TSS）、HR_EF（心率效率因子）

**分区统计**：基于 Joe Friel 5 区的心率分区时间 + 基于 Coggan 7 区的功率分区时间

**PMC 体系**：CTL（42 天 EMA）、ATL（7 天 EMA）、TSB = CTL - ATL

**TSS 策略**：骑行有功率 → 功率 TSS；无功率或跑步/步行 → 心率 TSS

**API 集成**：上传后自动计算指标、PMC API 端点

68 个测试全部通过
