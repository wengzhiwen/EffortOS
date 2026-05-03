# Sprint 47: 错误处理 + 边界用例测试

**状态**: 已完成
**目标**: 持续优化 — API 错误处理健壮性 + 边界用例测试

## 任务清单

- [x] **API 错误处理审查** — PMC 端点添加日期格式校验，无效日期返回 400
- [x] **边界用例测试补充** — dashboard 新增 4 个测试，auth 新增 5 个测试
- [ ] ~~前端错误提示优化~~ — 推迟到后续 sprint

## 新增测试

Dashboard (4): no_auth, weekly_trend 结构, calendar 结构, invalid_date → 400
Auth (5): missing_email, missing_verify_fields, profile_no_auth, logout_no_auth(幂等), invalid_token
