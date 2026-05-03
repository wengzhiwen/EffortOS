# Sprint 36: Best Efforts 最佳表现 + 进度趋势

**状态**: 进行中
**目标**: 参考竞品（Strava / intervals.icu）增加 Best Efforts 和训练趋势功能

## 任务清单

- [ ] **Best Efforts 计算服务** — 对 trackpoint 数据做滑动窗口计算，提取不同时长（5s/15s/1min/5min/20min/60min）的最佳功率、最佳心率
- [ ] **Best Efforts API + 存储** — 活动计算时自动生成 best_efforts 并存入 ComputedMetrics，提供查询 API
- [ ] **活动详情页展示 Best Efforts** — 在活动详情页增加"最佳表现"面板，表格展示各时长峰值
- [ ] **训练趋势图** — 仪表盘增加周/月维度的训练量、TSS 趋势图
- [ ] **强度等级可视化** — 活动列表和日历中用颜色标记强度等级（recovery→vo2max）
