# Sprint 36: Best Efforts 最佳表现 + 进度趋势

**状态**: 已完成
**目标**: 参考竞品（Strava / intervals.icu）增加 Best Efforts 和训练趋势功能

## 任务清单

- [x] **Best Efforts 计算服务** — 滑动窗口算法，提取 9 个时长（5s~3600s）的峰值功率和峰值心率
- [x] **Best Efforts API + 存储** — ComputedMetrics 新增 best_efforts 字段，活动序列化 API 包含
- [x] **活动详情页展示 Best Efforts** — 表格展示各时长峰值功率/心率
- [x] **训练趋势图** — 仪表盘增加周 TSS 趋势柱状图 + 周训练天数柱状图
- [x] **强度等级可视化** — 活动列表增加强度等级筛选器，后端支持 intensity_level 过滤

## 评估小结

Sprint 36 完成了竞品研究驱动的功能增强：
- 采纳用户提案"找参考"，研究了 intervals.icu / TrainingPeaks / Strava / Golden Cheetah 四大竞品
- 实现 Best Efforts 最佳表现功能（参考 Strava），从计算服务到 UI 展示全链路
- 仪表盘新增周训练趋势图，提升训练量可视化
- 活动列表增加强度等级筛选，方便按训练强度分类查看
- 149 个测试全部通过
