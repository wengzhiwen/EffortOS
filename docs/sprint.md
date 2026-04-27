# Sprint 22: 前端体验优化

**状态**: 已完成
**目标**: 消除前端重复代码、添加错误处理

## 任务清单

- [x] S22-1: 提取 typeNames 到 base.html 全局变量（消除 3 处重复）
- [x] S22-2: Dashboard 页面添加 API 错误处理（.catch）
- [x] S22-3: 活动详情页添加 API 错误处理

## 评估小结

Sprint 22 完成了前端体验优化：
- `TYPE_NAMES` 映射集中到 base.html，3 个子模板改用全局变量
- Dashboard 和活动详情页添加错误处理，避免 API 失败时页面卡在 loading 状态
- 123 个测试全部通过
