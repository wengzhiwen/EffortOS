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