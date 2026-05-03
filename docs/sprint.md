# Sprint 46: 性能优化 + 用户体验微调

**状态**: 已完成
**目标**: 持续优化 — API 查询效率优化

## 任务清单

- [x] **活动列表查询优化** — 修复 gear ReferenceField 懒加载 N+1 问题
- [x] **Dashboard API 性能优化** — recent activities 添加日期过滤；合并 7d/30d 重叠查询
- [ ] ~~前端加载骨架屏~~ — 推迟到后续 sprint

## 优化详情

- Dashboard recent activities: `Activity.objects()` → `Activity.objects(start_time__lte=end_dt)` 避免全表扫描
- Dashboard 7d/30d: 从 2 个独立查询合并为 1 个 30d 查询 + 内存过滤
- Activities gear 序列化: 通过 `_data["gear"]` 直接取 ObjectId 避免触发懒加载
