# EffortOS 工作日志

按时间倒序记录每次迭代的完成情况。

---

*（自驱动循环启动后，每次迭代在此追加记录）*

---

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
