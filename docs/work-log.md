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
