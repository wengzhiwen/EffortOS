# Sprint 20: 测试覆盖与日期查询 Bug 修复

**状态**: 已完成
**目标**: 补充关键端点测试覆盖，修复日期查询 bug

## 任务清单

- [x] S20-1: Dashboard API 测试（/api/dashboard, /api/pmc）— 6 个新测试
- [x] S20-2: Params API 测试（/api/params, /api/params/latest, /api/params/history）— 7 个新测试
- [x] S20-3: 活动导出和 Trackpoints 测试 — 6 个新测试
- [x] S20-4: 修复日期查询 bug（start_time__lte 字符串比较失效）

## 评估小结

Sprint 20 完成了测试覆盖和 bug 修复：
- 新增 19 个测试（104 → 123），覆盖 dashboard、params、export、trackpoints API
- 修复重要 bug：MongoEngine `start_time__lte` 字符串比较对带时间部分失效，改用 datetime 对象
- 123 个测试全部通过
