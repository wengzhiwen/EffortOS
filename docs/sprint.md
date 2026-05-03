# Sprint 45: Bug 大扫除

**状态**: 已完成
**目标**: 每 5 个 Sprint 一次的 Bug 大扫除 — 全面 UI 审查 + 测试回归

## 任务清单

- [x] **桌面端逐页截图审查** — 12 个页面全部截图审查，发现 PB 计算 500 错误
- [x] **移动端逐页截图审查** — 375x812 viewport 审查完成，无溢出/布局问题
- [x] **深色模式审查** — 桌面+移动深色模式均正常
- [x] **修复发现的问题** — 修复 _calc_pb_markers 遍历 best_efforts 错误层级导致活动列表 500 错误
- [x] **运行完整测试套件** — 202 全部通过，无回归

## 发现的问题

1. **[已修复]** 活动列表 API 500 错误 — `_calc_pb_markers` 遍历 `cm.best_efforts.items()` 而非 `cm.best_efforts[metric].items()`，导致 BaseDict 比较报错
