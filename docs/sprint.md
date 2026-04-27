# Sprint 4: 数据可视化

**状态**: 已完成
**对应 Milestone**: M5
**目标**: Dashboard 首页、活动列表/详情、PMC 曲线图、参数设置页

## 任务清单

- [x] S4-1: 基础页面布局和样式（导航栏、CSS 框架、Chart.js 引入）
- [x] S4-2: Dashboard 首页 — 今日 TSS、CTL/ATL/TSB 数值、PMC 趋势图、最近活动列表
- [x] S4-3: 活动列表页 — 运动记录列表（含上传、删除、分页）
- [x] S4-4: 活动详情页 — 指标摘要 + 心率/功率分区图表
- [x] S4-5: PMC 曲线图 — Chart.js 折线图展示 CTL/ATL/TSB
- [x] S4-6: 用户参数设置页面 — FTP/LTHR 配置 + 分区预览 + 历史记录

## 评估小结

Sprint 4 全部完成。实现了完整的前端可视化界面：

- 自定义 CSS 样式系统（卡片、网格、标签、表单）
- Dashboard 首页：TSS/CTL/ATL/TSB 四宫格 + PMC 30 天趋势图 + 最近活动
- 活动列表页：上传、删除、分页、运动类型筛选
- 活动详情页：完整指标展示 + 心率/功率分区柱状图
- 参数设置页：参数保存 + 分区预览 + 历史记录
- Dashboard API、Params API（CRUD + 历史）
- params_service 支持 user=None（认证前）
- 68 个测试全部通过
