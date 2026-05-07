# Sprint 75: Bug 大扫除

**状态**: 已完成
**目标**: 全面 UI 审查 + Bug 修复

## Bug 大扫除检查项

- [x] **桌面端截图审查** — 所有页面逐一截图检查
- [x] **移动端截图审查** — 响应式布局、表格溢出、触控区域
- [x] **深色模式审查** — 对比度、颜色协调、弹层背景
- [x] **交互功能测试** — 按钮、表单、弹层、下拉菜单
- [x] **修复发现的问题** — 每个修复单独 commit
- [x] **运行完整测试套件** — 221 passed，无回归

## 发现并修复的问题

1. **[严重] style.css 未被加载** — base.html 缺少 `<link>` 标签，导致 CSS 变量和所有样式未生效
2. **移动端表格溢出** — 活动列表等多列表格在移动端超出视口，添加 `min-width` + `overflow-x: auto`
3. **帮助页 HTML 结构错误** — 「功能指南」卡片嵌套在「文件格式」卡片内 + 重复的 card-title
4. **[严重] activity_detail 残留 gear API 调用** — 装备功能已移除但模板仍调用 `/api/gear`，导致 404 错误和控制台报错
5. **compare.html 字段名不一致** — `summaryCard` 使用 `act.type` 但 API 返回 `act.activity_type`，导致类型显示为 undefined
6. **gear 相关测试残留** — 删除 test_gear_api.py，移除 test_batch_delete 和 test_activity_crud 中的 gear 测试用例
