# Sprint 27: 登录流程重整

**状态**: 已完成
**目标**: 未登录用户只能看到落地页，登录后才能访问功能页

## 任务清单

- [x] S27-1: 创建落地页模板（landing.html）
- [x] S27-2: 首页逻辑：未登录显示落地页，已登录显示仪表盘
- [x] S27-3: 功能页登录保护（activities/settings/ai/profile 重定向）
- [x] S27-4: 公开页面保持公开（login/help/about）
- [x] S27-5: 已登录用户访问 login 页自动跳转仪表盘

## 评估小结

Sprint 27 完成了登录流程重整：
- 新增 landing.html 落地页，展示产品介绍和核心功能
- 首页 `/` 根据登录状态分流：落地页 vs 仪表盘
- activities/settings/ai/profile/activity_detail 需登录
- login/help/about 保持公开访问
- 已登录访问 /login 自动跳转仪表盘
- 采纳提案「登录流程」
- 131 个测试全部通过
