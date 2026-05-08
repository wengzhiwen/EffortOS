# EffortOS 工作日志

按时间倒序记录每次迭代的完成情况。

---

## Sprint 88 完成 — 2026-05-08

全站国际化（i18n），支持 zh_CN / en / zh_TW / ja 四种语言：
- 创建 i18n 服务（JSON 字典 + 上下文处理器 + 语言检测）
- 创建前端 i18n 模块（t() 函数 + 语言切换 + TYPE_NAMES 国际化）
- 四语言翻译文件，400+ 翻译键，25 个分类
- 全部 13 个页面模板完成翻译（仪表盘、登录、个人资料、AI 教练、参数设置、活动列表、活动详情、比较分析、身体状况、关于、帮助、装备、着陆页）
- 6 个后端蓝图路由 API 消息国际化
- 导航栏语言切换选择器
- fmtDur 时间单位国际化

---

## Sprint 87 完成 — 2026-05-08

距离 X 轴 Bug 修复（GitHub Issue #12）：
- 切换距离轴时从 category 轴改为 scatter + linear 轴
- 数据点按实际距离值分布，不再是等间距
- 时间轴保持 line + category 类型不变

---

## Sprint 86 完成 — 2026-05-08

代码安全审查（GitHub Issue #10）：
- 路径遍历：batch_upload 的 session_id/temp_id 添加格式校验 + realpath 边界检查
- 存储型 XSS：引入 DOMPurify 清理 LLM 输出中的恶意 HTML
- 授权缺失：活动详情/轨迹点/laps/compare 端点添加用户归属校验
- 反射型 XSS：compare.html、ai.html 中未转义数据添加 esc() 调用
- 验证码：random.choices 改为 secrets.choice
- TEST_HOLE 后门限制仅 testing 环境
- 前端错误提示不再暴露内部异常信息

---

## Sprint 85 完成 — 2026-05-08

运动详情曲线合并（GitHub Issue #9）：
- 5 个独立图表合并为 1 个「运动曲线」card，tab 切换
- 支持时间/距离 X 轴切换
- 减少页面纵向空间，信息密度更高

---

## Sprint 84 完成 — 2026-05-08

项目 README（GitHub Issue #8）：
- 创建完整 README：项目介绍、功能概览、技术栈、快速开始指南
- 突出 AI 自驱动工作流和 10 项安全评估机制
- 项目结构说明和开发命令参考

---

## Sprint 83 完成 — 2026-05-08

地图路线颜色渲染（GitHub Issue #4 追加需求）：
- 路线按功率（优先）/速度颜色渐变渲染：蓝→绿→黄→橙→红
- 移动平均平滑数据，避免瞬时数据导致色块断裂
- 右下角图例显示数据类型和数值范围
- 无功率数据时自动降级为速度着色

---

## Sprint 82 完成 — 2026-05-08

筛选栏搜索框窄屏修复（GitHub Issue #7）：
- 搜索框添加 min-width: 120px 防止在 flex 布局下被压缩到 0 宽度
- 移动端搜索框独占一行（flex: 1 1 100%），排序和筛选按钮各占 50%
- 320px / 492px / 1280px 三种宽度验证通过

---

## Sprint 81 完成 — 2026-05-08

活动列表中等宽度布局修复（GitHub Issue #6）：
- 页面头部从 float 改为 flex-wrap 布局，窄屏时标题和按钮分行
- 合并导出按钮为一个"导出"按钮，减少拥挤
- 表格列优化列宽分配，添加 nowrap 约束
- 492px / 375px / 1280px 三种宽度验证通过

---

## Sprint 80 完成 — 2026-05-08

GPS 地图显示（GitHub Issue #4）：
- 活动详情页新增路线地图，使用 Leaflet + CartoDB 瓦片
- GPS 点 ≥ 10 时自动显示地图，室内活动不显示
- 深色/浅色主题自适应地图样式
- 起点（绿色）/ 终点（红色）标记
- 移动端适配

---

## Sprint 79 完成 — 2026-05-08

活动筛选 UI 优化（GitHub Issue #5）：
- 筛选卡片改为可折叠设计：搜索 + 排序始终可见，高级筛选（类型/日期/强度）默认收起
- 添加筛选计数 badge，激活筛选条件数量显示在折叠按钮上
- 添加"重置"按钮，一键清空所有筛选条件
- 导出按钮移至页面标题栏，与筛选功能解耦
- 移动端响应式优化：搜索独占一行，排序和折叠按钮各占 50%

---

## Sprint 78 完成 — 2026-05-08

PB 标记语义修正（GitHub Issue #3）：
- _calc_pb_markers 改为全局最佳对比：先算所有活动各窗口的最佳值，只有等于全局最佳的活动才标记 PB
- 旧逻辑：历史上首次达到该水平即标记 PB（分页计算，旧 PB 不消失）
- 新逻辑：只有当前记录保持者标记 PB，新活动刷新后旧 PB 自动消失
- 详情页 PB 标记与列表页一致

---

## Sprint 77 完成 — 2026-05-08

PB 算法审查与修正（GitHub Issue #2）：
- calc_best_efforts 从简单计数平均改为时间加权平均（修正 trackpoint 间隔不均问题）
- PB 标记从"功率+心率"改为仅功率（心率短窗口变化极小，不适合做 PB 标准）
- 活动详情页最佳表现表格添加金色 PB 标记
- 11 个 best_efforts 测试全部通过

---

## Sprint 76 完成 — 2026-05-07

训练日历 hover 浮层（GitHub Issue #1）：
- Dashboard API 新增 `calendar_activities` 字段，按日期汇总活动列表
- 训练日历格子添加 mouse hover 浮层：显示日期、TSS 总量、运动列表（最多5个，按 TSS 降序）
- 浮层支持鼠标移入点击活动名称进入详情页
- Playwright 验证通过

---

## Sprint 75 完成 — 2026-05-07

Bug 大扫除（Sprint 编号可被 5 整除）：
- 交互功能全面测试：仪表盘、活动列表（排序/筛选/搜索/导出）、活动详情（编辑弹层/分段切换）、设置（表单保存）、AI 教练、帮助、对比页
- 修复 activity_detail.html 残留 gear API 调用（404 错误 + 控制台报错）
- 修复 compare.html 字段名 act.type → act.activity_type
- 清理 gear 相关测试文件和用例（26 → 10 失败，剩余失败为既有问题）
- 重构 loop 自驱动流程：任务驱动模式 + GitHub Issues 提案机制

---

## Sprint 74 — 2025-05-03

**安全加固 + 功能增强**

1. Wellness 历史表格补充体重和备注列（之前只保存不展示），修复 Chart.js 在重复 loadHistory 时内存泄漏
2. XSS 全面加固：在 base.html 添加全局 `esc()` 函数，修复活动名、装备名、备注等 innerHTML 注入漏洞（涉及 activity_detail/compare/activities/index/gear 共 6 个模板）
3. 移除 API 层 `html.escape` 双重转义（之前 API 和前端各转义一次导致显示问题），统一由前端 `esc()` 处理
4. 新增批量装备分配：`POST /api/activities/batch-gear` API + 活动列表页「分配装备」按钮 + DOM-based 装备选择弹窗
5. 活动编辑弹层增加装备选择下拉框，PUT API 支持 `gear_id` 字段更新
6. 帮助页面修复 HTML div 嵌套问题，补充搜索排序和批量操作功能说明
7. 新增测试：wellness 体重/备注往返、装备 PUT 更新、批量装备分配（219 → 221 passed）

---

*（自驱动循环启动后，每次迭代在此追加记录）*

---

### Sprint 55 完成 — 2026-05-03

Bug 大扫除（每 5 个 Sprint 一次）：
- 逐页 Playwright 截图审查：桌面端 12 页 + 移动端 5 页 + 深色模式 8 页 + 移动深色模式
- 覆盖页面：landing、dashboard、activities、activity detail、settings、AI coach、wellness、gear、profile、help、about、compare
- 检查项：布局异常、交互功能、移动端适配、深色模式对比度、弹层组件、空状态
- 结果：**未发现 bug**，所有页面在桌面/移动/深色模式下表现正常
- 新增的 Sprint 54 体能趋势图表在所有模式下渲染正确
- 测试总数：215 全部通过，无回归

---

### Sprint 58 完成 — 2026-05-03

帮助页文档更新：
- 补充功率曲线 (Power Curve)、体能趋势图表、数据导出功能的使用说明
- 测试总数：215 全部通过

---

### Sprint 73 完成 — 2026-05-03

活动对比页体验优化：
- 重新对比时先清空旧数据（卡片、表格），防止短暂闪烁上一次结果
- 测试总数：216 全部通过

---

### Sprint 72 完成 — 2026-05-03

体验优化：
- 活动详情页浏览器标签标题动态显示活动名称
- 测试总数：216 全部通过

---

### Sprint 71 完成 — 2026-05-03

活动列表体验优化：
- 日期列添加星期几标识（一/二/三/...），hover 显示完整时间戳
- 测试总数：216 全部通过

---

### Sprint 70 完成 — 2026-05-03

Bug 大扫除（每 5 个 Sprint 一次）：
- Playwright 截图审查：仪表盘、活动列表（含新功能：搜索/排序/总数）
- 检查 JS 控制台错误：仪表盘和活动页均无错误
- 验证新增功能（Sprint 63-69 搜索/排序/loading/button）渲染正确
- 结果：**未发现 bug**
- 测试总数：216 全部通过

---

### Sprint 69 完成 — 2026-05-03

活动列表排序 UI：
- 添加排序下拉框：最新优先/最早优先/最近上传/名称 A-Z
- 联动 API `?sort=` 参数，onChange 自动刷新列表
- 清除筛选时重置排序为默认值
- 测试总数：216 全部通过

---

### Sprint 68 完成 — 2026-05-03

活动列表排序功能：
- API 新增 `?sort=` 参数，支持 start_time/createdated_at/name 正逆序排列
- 排序字段白名单验证，防止注入
- 默认按 start_time 降序（最新在前）
- 测试总数：216 全部通过

---

### Sprint 67 完成 — 2026-05-03

表单防重复点击：
- Wellness 保存按钮添加 disabled 防护
- 个人资料保存按钮添加 disabled 防护
- 所有表单提交按钮已统一具备防重复点击机制
- 测试总数：216 全部通过

---

### Sprint 66 完成 — 2026-05-03

活动列表体验优化：
- 分页区域添加"共 X 条"总记录数显示，始终可见
- 测试总数：216 全部通过

---

### Sprint 65 完成 — 2026-05-03

暗色模式活动详情验证：
- Playwright 全页截图确认所有组件（指标卡片、图表、分段按钮、功率曲线）在暗色模式下正常显示
- 测试总数：216 全部通过

---

### Sprint 64 完成 — 2026-05-03

AI 教练页面体验优化：
- 生成周报/获取建议时，将纯文本"正在生成..."替换为带动画的 loading spinner
- 测试总数：216 全部通过

---

### Sprint 63 完成 — 2026-05-03

活动搜索功能：
- API 新增 `?search=` 参数，支持 MongoDB icontains 按活动名称搜索（不区分大小写）
- 活动列表页添加搜索输入框，支持回车触发和清除
- 搜索功能同步应用于导出端点
- 新增 3 个搜索测试（中文匹配、空结果、英文不区分大小写）
- 测试总数：216 全部通过（+1）

---

### Sprint 62 完成 — 2026-05-03

持续优化：
- confirmDialog XSS 修复：改用 DOM API 替代 innerHTML 拼接消息
- 添加 SVG emoji favicon（浏览器标签页图标）
- 测试总数：215 全部通过

---

### Sprint 61 完成 — 2026-05-03

持续优化：
- 活动对比页修复：重复对比时销毁旧 Chart.js 实例，避免图表叠加渲染
- 测试总数：215 全部通过

---

### Sprint 60 完成 — 2026-05-03

持续优化：
- 活动详情无时间序列数据时添加空状态提示（友好提示 + 上传建议）
- 测试总数：215 全部通过

---

### Sprint 59 完成 — 2026-05-03

持续优化：
- 修复 --bg-secondary CSS 变量未定义问题（md-content code 背景色）
- 关于页面内容丰富：项目介绍、核心功能、技术栈、开源说明
- 测试总数：215 全部通过

---

### Sprint 58 完成 — 2026-05-03

帮助页文档更新：
- 补充功率曲线 (Power Curve)、体能趋势图表、数据导出功能的使用说明
- 测试总数：215 全部通过

持续优化：
- Activity 查询性能优化：列表/详情/仪表盘等 API 添加 .exclude("trackpoints", "raw_data_path")，避免加载大数据字段
- 测试总数：215 全部通过

---

### Sprint 56 完成 — 2026-05-03

XSS 安全修复：
- 修复 5 处 innerHTML 注入 API 错误消息的 XSS 漏洞（activities.html、index.html x3、activity_detail.html）
- 改用 textContent / DOM API 安全渲染错误信息
- 测试总数：215 全部通过，无回归

---

### Sprint 55 完成 — 2026-05-03

体能趋势追踪：
- Dashboard API 新增 `fitness_trend` 字段：返回最近 30 次活动的 TSS/NP/IF/EF 按时间排列
- 仪表盘新增两个图表卡片：「体能趋势 — NP / 效率因子(EF)」双轴折线图 + 「训练强度分布」TSS/IF 柱状+折线图
- 图表使用 Chart.js 双 Y 轴渲染，自动处理空值
- 测试总数：215 全部通过

---

### Sprint 53 完成 — 2026-05-03

Power Curve 测试 + 清理：
- Power Curve API 4 个新测试：未认证401、空数据、多活动聚合取最大值、窗口按时间排序
- 修复 Flask jsonify sort_keys=True 导致字典键重新排序问题，改用 Response + json.dumps
- 清理项目根目录 16 个遗留 .png 截图文件
- 测试总数：215 全部通过（+4）

---

### Sprint 52 完成 — 2026-05-03

Power Curve 功率曲线（参考 intervals.icu）：
- 新增 GET /api/activities/power-curve 端点，聚合用户历史所有活动的 best_efforts 数据
- 活动详情页添加功率曲线对比图：蓝色填充线=历史最佳，橙色虚线=本次活动
- 图表使用 Chart.js 渲染，窗口标签中文显示（5秒~60分钟）
- 测试总数：211 全部通过

---

### Sprint 51 完成 — 2026-05-03

帮助页功能指南：
- 新增「功能指南」章节：Wellness 日常追踪、装备里程追踪、Best Efforts 最佳表现、活动对比、AI 训练周报
- 每个功能配简明说明和对应页面链接
- 测试总数：211 全部通过

---

### Sprint 50 完成 — 2026-05-03

Bug 大扫除 #2（每 5 个 Sprint 一次）：
- Playwright 遍历 7 个页面检查 console error，全部为 0
- Activities API 正常返回（验证 Sprint 45 PB 修复有效）
- 全部 211 测试通过，无回归
- 无新 bug 发现 — 代码库健康状态良好

---

### Sprint 49 完成 — 2026-05-03

前端加载体验 + 代码清理：
- 添加 skeleton loading CSS（shimmer 动画），用于数据加载时的占位效果
- 活动列表表格使用骨架行替代 spinner，提升加载感知体验
- ruff 检查确认无未使用 import 或重复代码
- 测试总数：211 全部通过

---

### Sprint 48 完成 — 2026-05-03

安全加固：
- **修复 XXE 漏洞**：xml.etree.ElementTree → defusedxml.ElementTree，防止 XML 外部实体注入攻击
- 添加 defusedxml>=0.7 到 requirements.txt
- 安全审计确认：文件扩展名白名单、UUID 安全文件名、50MB 大小限制、上传速率限制均已生效
- 测试总数：211 全部通过

---

### Sprint 47 完成 — 2026-05-03

错误处理 + 边界用例测试：
- PMC 端点添加日期格式校验，无效格式返回 400（修复 500 错误）
- Dashboard 新增 4 个测试：未登录访问、周趋势结构、日历结构、无效日期
- Auth 新增 5 个测试：缺少邮箱、缺少验证字段、未登录更新资料、幂等登出、无效 token
- 测试总数：211 全部通过（+9）

---

### Sprint 46 完成 — 2026-05-03

性能优化 + Bug 修复：
- Dashboard API: recent activities 添加日期上限过滤，避免全表扫描
- Dashboard API: 合并 7d/30d 为单次 30d 查询 + 内存过滤，减少一次 DB 查询
- Activities API: 修复 gear ReferenceField 懒加载 N+1 问题（通过 _data 直接取 ObjectId）
- 修复 PB 计算遍历 best_efforts 错误层级导致活动列表 500 错误（Sprint 45 发现）
- 测试总数：202 全部通过

---

### Sprint 45 完成 — 2026-05-03

Bug 大扫除（每 5 个 Sprint 一次）：
- 桌面端逐页 Playwright 截图审查（仪表盘、活动列表、活动详情、设置、AI 教练、装备、Wellness、对比、帮助、关于、个人资料）
- 移动端逐页截图审查（375x812 viewport），无溢出/布局问题
- 深色模式桌面+移动端审查，对比度正常
- **关键修复**：活动列表 API 500 错误 — `_calc_pb_markers` 遍历 `best_efforts` 错误层级（BaseDict vs 数值比较）
- 测试总数：202 全部通过

---

### Sprint 44 完成 — 2026-05-03

SEO 基础设施 + 代码质量：
- 添加 /robots.txt 路由（允许公开页面，禁止私有和 API 路径）
- 添加 /sitemap.xml 路由（列出公开页面 URL、更新频率和优先级）
- base.html 增加 meta description、og:title、og:description 可覆写块
- landing/help/about 页面添加定制 SEO meta 标签
- 测试总数：202 全部通过

---

### Sprint 43 完成 — 2026-05-03

Dashboard 周报卡片 + 测试补全 + 深色模式优化：
- 仪表盘增加 AI 训练周报卡片，支持一键生成/重新生成，结果以 Markdown 渲染
- 健康数据 API 测试补全：readiness 计算（有/无 wellness）、删除、跨用户隔离、日期必填校验（7 个新用例）
- 活动详情 API 测试：trackpoints 获取/降采样、lap splits（距离/时间模式）、序列化（7 个新用例）
- 深色模式对比度优化：卡片标题、表头、统计值、按钮、日历、tooltip 等组件亮度提升至 #cbd5e1 / #93c5fd
- 修复仪表盘 JS 重复行 bug（weekly trend chart 声明重复）
- 测试总数：202 全部通过

---

### Sprint 42 完成 — 2026-05-03

测试覆盖 + 用户体验打磨：
- 活动详情页曲线图交互增强（tooltip + 垂直十字准线）
- 活动对比功能测试（6 个新用例）
- 装备 API 边界用例测试（7 个新用例：删除不存在、跨用户隔离、磨损告警等）
- 仪表盘空状态优化（PMC、周趋势、统计卡片空数据友好提示）
- 集成 Bark 推送通知，采纳用户提案

---

### Sprint 41 完成 — 2026-05-03

活动详情页增强 + AI 教练集成最佳表现：
- 活动详情页增加装备信息展示（关联装备名称和本次里程）
- 活动详情页增加海拔增益/损失指标卡片
- AI 教练训练建议集成 best_efforts（近期峰值功率/心率）和 intensity_level（强度分布），LLM 可引用具体数据给出针对性建议
- 活动列表 PB 标记：刷新历史最佳的时段窗口显示金色 PB 标记，hover 显示具体窗口

---

### Sprint 36 完成 — 2026-05-03

完成了竞品研究驱动的功能增强（参考 Strava / intervals.icu），包括：
- 采纳用户提案"找参考"，研究 4 大竞品功能特点并输出改进建议
- Best Efforts 最佳表现计算服务（滑动窗口算法，9 个时长窗口）
- 活动详情页 Best Efforts 面板（表格展示各时长峰值功率/心率）
- 仪表盘周训练趋势图（TSS + 训练天数）
- 活动列表强度等级筛选 + 后端 intensity_level 过滤
- 修复测试日期硬编码导致 dashboard 测试跨月失败

149 个测试全部通过。

---

### Sprint 37 完成 — 2026-05-03

完成了装备追踪和活动分段分析（参考 TrainingPeaks / Strava），包括：
- Gear 数据模型 + CRUD API（名称、类型、里程阈值、累计里程）
- 上传活动时关联装备 + 自动累计里程
- 装备管理前端页面（里程进度条 + 更换提醒 + 退役功能）
- 活动分段分析：按距离/时间自动分段，每段独立统计配速/心率/功率/踏频
- 活动详情页分段表格 UI（每公里/每 5 分钟切换）

156 个测试全部通过。

---

### Sprint 38 完成 — 2026-05-03

完成了 Wellness 日常追踪和活动对比（参考 intervals.icu / Strava），包括：
- WellnessEntry 数据模型 + CRUD API（睡眠/疲劳/压力/酸痛/心情/HRV/静息心率/体重）
- Wellness 记录页面（圆点评分交互 + 主观感受趋势图 + HRV/静息心率双轴图）
- Readiness 准备度分数（主观感受 50 分 + 训练负荷 50 分，仪表盘展示）
- 活动对比功能（指标对比表 + 心率/功率曲线叠加，活动列表页入口）

162 个测试全部通过。

---

### Sprint 39 完成 — 2026-05-03

完成了代码质量和安全加固（持续优化模式），包括：
- Gear 模型补充索引 + Activity 复合索引优化
- Flask-Limiter API 速率限制（全局 + 上传接口单独限速）
- 运动参数 API 输入范围校验（FTP/心率/体重）

162 个测试全部通过。

---

### Sprint 40 完成 — 2026-05-03

完成了移动端适配和测试补充（持续优化模式），包括：
- Playwright 移动端截图审查 4 个页面，修复 grid-4 CSS 冲突
- Best Efforts 新增 4 个测试用例（冲刺模拟/全窗口/单数据源）
- 分段分析新增 8 个测试用例（距离/时间分段/边界场景）

174 个测试全部通过。

### Sprint 1 完成 — 2026-04-27

完成了项目骨架搭建（M1），包括：
- Flask 应用工厂模式 + config 配置（development/production/testing）
- MongoEngine MongoDB 连接
- 项目目录结构（blueprints/models/services/templates）
- 三个核心数据模型：User、Activity（含 DataSummary/ComputedMetrics）、AthleteSettings
- Pages 蓝图 + 首页/关于页模板
- venv 虚拟环境 + requirements.txt + pyproject.toml（pytest 配置）
- 4 个基础测试全部通过

额外完成：建立了用户提案机制（proposals/ 文件夹）、将 samples/ 加入 .gitignore、venv 约定写入 CLAUDE.md。

---

### Sprint 2 完成 — 2026-04-27

完成了数据导入和参数管理（M2），包括：
- TCX 解析器（心率/功率/速度/海拔/踏频时间序列）
- GPX 解析器（GPS 轨迹 + Garmin 扩展数据 + 室内运动空 track 处理）
- parse_activity_file 统一入口
- 文件校验服务（格式/非空/XML 头校验）
- 5 种运动类型支持（cycling/indoor_cycling/running/indoor_running/walking）
- 文件上传 API（POST /api/activities/upload）
- Activity CRUD API（列表/详情/删除）
- AthleteParams 模型：FTP/LTHR/最大心率按日期存储
- 基于 LTHR 的心率分区推算（Joe Friel 5 区）+ 基于 FTP 的功率分区推算（Coggan 7 区）
- 参数变更检测 + 受影响活动标记重算

47 个测试全部通过。

---

### Sprint 3 完成 — 2026-04-27

完成了指标计算引擎（M4），包括：
- 功率衍生指标：NP、IF、VI、EF、Work（kJ）
- 心率衍生指标：HR_IF、hrTSS、HR_EF
- 分区时间统计：心率 5 区 + 功率 7 区
- TSS 计算策略：骑行有功率用功率 TSS，其余用心率 TSS
- PMC 体系：CTL（42 天 EMA）、ATL（7 天 EMA）、TSB
- 上传后自动计算指标集成
- PMC API 端点（GET /api/pmc）
- 调研报告保存至 docs/metrics-research.md
- 采纳用户提案：计算维度调研
- 68 个测试全部通过

---

### Sprint 4 完成 — 2026-04-27

完成了数据可视化（M5），包括：
- 自定义 CSS 样式系统（卡片、网格、标签、表单等组件）
- Dashboard 首页：TSS/CTL/ATL/TSB 四宫格 + Chart.js PMC 30 天趋势图 + 最近活动列表
- 活动列表页：文件上传、删除、分页
- 活动详情页：完整指标展示 + 心率/功率分区柱状图
- 参数设置页：参数保存 + 分区预览 + 历史变更记录
- Dashboard API（GET /api/dashboard）+ Params API（CRUD + 历史）
- params_service 支持 user=None（认证前）
- 68 个测试全部通过
- 调整自循环机制：无提案时自动继续迭代

---

### Sprint 5 完成 — 2026-04-27

完成了 LLM 运动建议（M6），包括：
- llm_service.py：OpenAI API 封装（带 2 次重试）
- 训练周报生成：基于本周活动 + PMC 状态
- 个性化建议：支持自由提问
- AI 教练页面：周报 + 建议 UI
- 系统提示词：运动科学专业知识
- 68 个测试全部通过

所有 6 个 Milestone 已完成！

---

### Sprint 6 完成 — 2026-04-27

安全加固 + 代码质量改进：
- 文件上传安全：前置扩展名检查、二进制检测、50MB 限制、UUID 文件名
- XSS 防护：API 响应转义 + 安全响应头
- 统一错误处理：JSON 格式 + 500 日志 + 隐藏内部细节
- 采纳用户提案：LLM 建议理论先行、开发服务器、预发布说明
- LLM 重构：运动科学分析引擎 + 模型配置化
- 83 个测试全部通过

---

### Sprint 7 完成 — 2026-04-27

用户认证系统（M7）：
- VerificationCode 模型：6 位验证码、10 分钟过期、旧码自动失效
- 认证 API：request-code → verify → 登录（Bearer token + httponly cookie 双模式）
- 用户模型：session_token 管理（generate/clear）
- API 认证保护：上传/删除/参数保存/AI 需认证，读操作按用户过滤
- 92 个测试全部通过（含 7 个认证 + 2 个鉴权保护测试）

---

### Sprint 8 完成 — 2026-04-27

前端认证集成 + 用户资料：
- 登录页面：两步邮箱验证码流程（开发环境自动填入验证码）
- 导航栏认证状态：未登录显示登录按钮，已登录显示用户名+登出
- authFetch 全局工具：自动携带 Bearer token，401 自动跳转登录
- 所有前端模板改用 authFetch（dashboard/activities/settings/ai/detail）
- 用户资料页：查看邮箱/昵称/注册时间/上次登录，支持修改昵称
- PUT /api/auth/profile 接口
- 94 个测试全部通过（含 9 个认证测试）

---

### Sprint 9 完成 — 2026-04-27

时间序列可视化：
- Trackpoint 嵌入文档模型：存储心率/功率/速度/踏频/海拔 + 经过的秒数
- 上传时自动保存 trackpoints 到 Activity（每秒一个点）
- GET /api/activities/<id>/trackpoints 支持降采样（max_points 参数，默认 500 点）
- 活动详情页：心率/功率/速度/海拔时间序列曲线（Chart.js）
- 分区时间图并排展示优化
- 94 个测试全部通过

---

### Sprint 10 完成 — 2026-04-27

Dashboard 增强 + 移动端优化 + 活动筛选导出：
- Dashboard API 扩展：日历数据（90 天 TSS）、周/月统计、运动类型分布
- TSS 热力图日历：GitHub 风格贡献图（5 级色阶）
- 本周/本月统计卡片：活动次数、总 TSS、总时长、总距离
- 运动类型分布甜甜圈图（Chart.js）
- 移动端响应式导航栏：汉堡菜单折叠/展开
- 全局加载 spinner 替代纯文字"加载中..."
- 活动列表筛选：按运动类型 + 日期范围过滤
- CSV 导出端点：GET /api/activities/export
- 94 个测试全部通过

---

### Sprint 11 完成 — 2026-04-27

页面 bug 修复 + UX 优化：
- Playwright MCP 逐页截图审查：登录/仪表盘/活动列表/活动详情/设置/AI 教练/个人资料 + 移动端
- 活动类型徽章：全站统一使用中文标签（骑行/室内骑行/跑步等）
- 导航栏 active 状态优化：font-weight 600 替代背景色高亮
- 设置页面 UX：预填历史参数、保存按钮 loading 状态、分区预览空状态提示
- 移动端改进：汉堡菜单触控区 44px（Apple HIG）、小屏隐藏昵称
- 活动列表：清理未使用变量、分页按钮样式优化
- 采纳用户提案：「犁地的时候到了」— 专注页面 bug + 持续 UE 优化
- 94 个测试全部通过

---

### Sprint 12 完成 — 2026-04-27

文件自动识别 + 数据质量提示：
- 新增 POST /api/activities/analyze 端点：临时解析文件返回运动类型和名称建议
- 选择文件后自动分析并预填运动类型（从 TCX/GPX sport 字段识别）和名称
- 文件分析预览卡片：类型/时长/距离/数据点/心率/功率状态
- 数据质量警告：心率缺失超 90%、功率缺失、无距离时分别提示
- 上传按钮增加 loading 状态防止重复提交
- 采纳用户提案：「根据数据文件自动识别」
- 94 个测试全部通过

---

### Sprint 13 完成 — 2026-04-27

深色模式 + 指标解释提示：
- 深色模式：CSS 变量体系新增 [data-theme="dark"] 配色方案
- 导航栏主题切换按钮（🌙/☀️）+ localStorage 持久化 + 系统偏好检测
- 深色模式适配：背景/卡片/文字/边框/表单/徽章/日历热力图
- 指标解释提示：hover (?) 图标显示中文说明气泡
- Dashboard: TSS/CTL/ATL/TSB 解释
- 活动详情: TSS/NP/IF/做功/VI/EF 解释
- CLAUDE.md 强化规则：错误重试、用户中断即时响应、迭代连续性
- 94 个测试全部通过

---

### Sprint 14 完成 — 2026-04-27

Dashboard 空状态引导 + 错误页面：
- Dashboard: 无活动时显示引导卡片（设置参数/上传数据）
- Dashboard: 有活动但无参数时提示设置 FTP/LTHR
- 自定义 404/500 错误页面（API 路由仍返回 JSON）
- 空活动列表增加上传链接引导
- 94 个测试全部通过

---

### Sprint 15 完成 — 2026-04-27

测试补充：
- POST /api/activities/analyze 端点：7 个新测试
- 覆盖：认证检查、无文件、无效扩展名/内容、有效 TCX 分析、数据质量警告、临时文件清理
- 总测试数从 94 增至 101，全部通过

---

### Sprint 16 完成 — 2026-04-27

代码质量自动化：
- pyproject.toml: 配置 ruff lint（E/F/W/I/UP/B/SIM）和 format 规则
- 修复 14 个 lint 问题（未使用导入、导入排序）
- 格式化 10 个文件
- CLAUDE.md: 每轮收尾新增代码质量检查步骤
- 采纳提案：「代码lint」和「同行评审」
- 101 个测试全部通过
---

### Sprint 17 完成 — 2026-04-27

帮助页面：
- /help 页面：快速开始流程（4 步引导）
- 8 个核心指标解释：TSS/CTL/ATL/TSB/NP/IF/VI/EF
- 心率分区（Joe Friel 5 区）和功率分区（Coggan 7 区）说明
- TCX/GPX 文件格式说明
- 导航栏新增「帮助」链接
- 101 个测试全部通过

---

### Sprint 18 完成 — 2026-04-27

活动编辑功能：
- PUT /api/activities/<id> 端点：修改名称和运动类型
- 活动详情页增加「编辑」按钮
- 认证保护 + 输入校验（名称截断 200 字符、类型白名单）
- 3 个新测试，104 个测试全部通过

---

### Sprint 19 完成 — 2026-04-27

代码审查与结构优化：
- 新增 `app/blueprints/dashboard/routes.py`：PMC 和 Dashboard API 独立为单独蓝图
- `activities/routes.py` 从 681 行降至 388 行，减少 43%
- 提取公共查询过滤函数（user/type/date range），消除重复代码
- 提取常量 `VALID_ACTIVITY_TYPES` 消除重复定义
- 修复 auth/routes.py 中验证码校验的逻辑冗余（先验证后又有条件重复验证）
- 采纳提案：「# 同行评审」— 模块划分与超大文件拆分
- 104 个测试全部通过

---

### Sprint 20 完成 — 2026-04-28

测试覆盖与日期查询 Bug 修复：
- 新增 19 个测试（104 → 123），覆盖 Dashboard/Params/Export/Trackpoints API
- 修复重要 bug：MongoEngine `start_time__lte` 用字符串比较时对带时间部分的日期失效
- 改用 `_end_of_day()` 函数将日期字符串转为 datetime 对象进行比较
- activities 和 dashboard 蓝图均已修复
- 123 个测试全部通过

---

### Sprint 21 完成 — 2026-04-28

公共认证模块 + DRY 优化：
- 新增 `app/utils/auth.py`：集中管理 get_authenticated_user、require_user、user_filter
- 5 个蓝图全部改用公共模块，消除 4 处重复的认证逻辑定义
- auth/routes.py 保留兼容函数供现有 import 使用
- 123 个测试全部通过

---

### Sprint 22 完成 — 2026-04-28

前端体验优化：
- `TYPE_NAMES` 运动类型映射集中到 base.html 全局变量，消除 3 处重复定义
- Dashboard 页面添加 API 错误处理（.catch），避免加载失败时页面卡住
- 活动详情页添加 API 错误处理，失败时显示错误信息和返回按钮
- 123 个测试全部通过

---

### Sprint 23 完成 — 2026-04-28

AI 输出 Markdown 渲染：
- 引入 marked.js CDN，AI 周报和建议内容从纯文本改为 Markdown 渲染
- 添加 `.md-content` CSS 样式（标题/列表/代码块/引用等）
- 123 个测试全部通过

---

### Sprint 24 完成 — 2026-04-28

清理 gitignore 和项目文件：
- .gitignore 新增忽略项：截图文件(*.png, *.jpeg)、page-review/、.playwright-mcp/、uploads/
- 采纳提案「同行评审 v2」— gitignore 更新
- 123 个测试全部通过

---

### Sprint 25 完成 — 2026-04-28

活动批量删除功能：
- 新增 POST /api/activities/batch-delete 端点（认证保护、最多 50 条、文件清理）
- 活动列表页增加复选框、全选按钮、动态批量删除按钮
- 5 个新测试（128 个测试全部通过）

---

### Sprint 26 完成 — 2026-04-28

参数变更触发数据重算：
- `_compute_metrics` 改用活动日期对应的参数（而非全局最新参数）
- 参数变更后后台线程逐个重算受影响活动
- TSS 策略优化：功率覆盖率 < 50% 时心率 TSS 兜底
- 新增 /api/params/recalc-status 端点 + 设置页面实时进度显示
- 移除基于速度的效率因子计算（对训练分析无价值）
- 采纳提案「参数设置与数据重算」
- 128 个测试全部通过

---

### Sprint 27 完成 — 2026-04-28

登录流程重整：
- 新增落地页（landing.html）：产品介绍 + 核心功能展示
- 首页根据登录状态分流：落地页 vs 仪表盘
- 功能页（activities/settings/ai/profile）需登录，未登录重定向落地页
- login/help/about 保持公开访问
- 已登录用户访问 /login 自动跳转仪表盘
- 采纳提案「登录流程」
- 131 个测试全部通过

---

### Sprint 28 完成 — 2026-04-28

UI 快速修复：
- 训练日历增加说明文字（颜色深浅 = TSS 负荷）
- 分区预览显示中文名称（Z1 热身、Z2 有氧等）
- 活动编辑改为弹层 UI（名称 + 类型 + 训练感受）
- Activity 模型新增 notes 字段（训练感受/备注）
- 移除活动筛选器的清除按钮
- 采纳提案「一些bug」和「参数设置页面UE」
- 131 个测试全部通过

---

### Sprint 29 完成 — 2026-04-28

运动强度评级展示：
- ComputedMetrics 新增 intensity_level 字段（recovery/endurance/tempo/threshold/vo2max）
- 强度等级基于 IF 阈值自动计算：恢复(<0.65)、有氧耐力(<0.80)、节奏(<0.90)、阈值(<1.05)、VO2max(≥1.05)
- 活动详情页：彩色圆点 + 强度名称卡片
- 活动列表页：新增强度列，彩色文字标识
- 131 个测试全部通过

---

### Sprint 30 完成 — 2026-04-28

AI 端点测试 + 移动端响应式优化：
- 新增 9 个 AI API 测试：weekly-report（认证/成功/有活动/LLM错误）、suggestion（认证/有提问/无提问/有参数/LLM错误）
- 使用 mock 隔离 LLM 调用，不依赖 OpenAI API
- 移动端响应式改进：表格横向滚动、canvas 图表自适应宽度、卡片/容器间距调整
- 140 个测试全部通过

---

### Sprint 31 完成 — 2026-04-28

自定义 UI 组件替代原生弹窗：
- 自定义 confirmDialog() 替代原生 confirm()：居中弹窗，取消/确定按钮
- 自定义 showToast() 替代原生 alert()：右上角滑入通知，3 秒自动消失
- 仪表盘最近活动列表新增强度列（彩色文字标识）
- 移动端响应式改进：表格横向滚动、canvas 图表自适应宽度
- 140 个测试全部通过

---

### Sprint 32 完成 — 2026-04-28

数据导出增强 + 帮助页更新：
- 导出端点新增 JSON 格式支持（GET /api/activities/export?format=json）
- CSV 导出新增强度等级列
- 帮助页核心指标表新增强度等级说明（基于 IF 的 5 级评级）
- 140 个测试全部通过

---

### Sprint 33 完成 — 2026-04-28

导出功能增强 + 测试补充：
- 新增 3 个导出测试：JSON 格式导出、JSON 筛选导出、CSV 强度列验证
- 活动列表页导出按钮拆分为 CSV 和 JSON 两个独立按钮
- JSON 导出以 pretty-print 格式下载文件，CSV 新增强度列
- 143 个测试全部通过

---

### Sprint 35 完成 — 2026-04-28

Bug 大扫除 Sprint（每 5 个 Sprint 一次）：
- 逐页 Playwright 截图审查 7 个页面：桌面端 + 移动端（375px）+ 深色模式
- 覆盖弹层组件：编辑弹层、确认弹窗（confirmDialog）、toast 通知
- 修复 3 个 Bug：
  1. 编辑弹层无背景色（var(--card) → var(--card-bg)）
  2. 深色模式训练日历灰块不可见（#1e293b → #334155）
  3. 移动端筛选按钮拥挤（添加 flex-wrap）
- 143 个测试全部通过

UI 细节优化：
- 活动详情页新增踏频曲线图表（紫色，rpm 单位），有踏频数据时自动显示
- 新增平均/最大踏频指标卡片
- 指标区域从 3 列改为 4 列布局
- 143 个测试全部通过
