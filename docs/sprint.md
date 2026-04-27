# Sprint 7: 用户认证（M7）

**状态**: 已完成
**目标**: 实现邮箱验证码无密码登录，为 API 添加认证保护

## 任务清单

- [x] S7-1: VerificationCode 模型（6 位验证码、10 分钟过期、旧码失效）
- [x] S7-2: 认证 API 路由（request-code、verify、logout、me）
- [x] S7-3: API 认证保护（activities/params/ai 写操作需认证，读操作按用户过滤）

## 评估小结

Sprint 7 完成了用户认证系统：
- 验证码模型：6 位数字码、10 分钟过期、自动失效旧码
- 认证路由：request-code → verify → 登录，Bearer token + httponly cookie 双模式
- API 保护：上传/删除/参数保存/AI 需认证，列表/详情按用户过滤
- 92 个测试全部通过（含 7 个认证测试、2 个认证保护测试）
