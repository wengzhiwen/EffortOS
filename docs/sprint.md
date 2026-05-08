# Sprint 80: 活动详情页 GPS 地图显示

**状态**: 已完成
**目标**: GPS 数据质量好的活动在详情页显示地图路线（GitHub Issue #4）

## 任务清单

- [x] 在 base.html 引入 Leaflet CSS/JS
- [x] activity_detail.html 添加地图容器，GPS 数据好时显示
- [x] JS：加载轨迹点 → 构建 polyline → 渲染地图 → fit bounds
- [x] 添加起点/终点标记（绿色起点，红色终点）
- [x] 深色/浅色主题地图适配（CartoDB dark/light tiles）
- [x] 移动端适配
- [x] 桌面端 + 移动端截图验证
- [x] 测试通过 + commit

## 修改内容

- 引入 Leaflet 1.9.4（CSS + JS）
- GPS 点 ≥ 10 个时在指标卡片和时序图之间插入路线地图
- 使用 CartoDB 瓦片（浅色/深色主题自适应）
- 起点绿色圆点 + 终点红色圆点，hover 显示标签
- 室内活动（无 GPS 数据）自动隐藏地图区域
- 缩放控件样式适配深色主题
