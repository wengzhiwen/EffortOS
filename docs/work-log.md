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

采纳了两个用户提案：历史数据管理器 + 用户关键参数按日期管理。
47 个测试全部通过。
