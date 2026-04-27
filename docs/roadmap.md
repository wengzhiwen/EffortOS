# EffortOS 项目路线图

## 项目愿景

构建一个类似 intervals.icu 的运动数据追踪与分析平台，用户上传 TCX/GPX 运动文件，系统计算训练指标并提供可视化。同时作为 AI 自驱动实验项目，由 Claude Code 持续迭代开发。

## Milestones

### M1: 项目骨架 `[x]` — Sprint 1 ✓
> Flask 应用框架 + MongoDB 连接 + 核心数据模型 + 基础路由

- [ ] Flask 应用工厂 + config 配置
- [ ] MongoDB 连接（MongoEngine）
- [ ] 项目目录结构（blueprints/models/services/templates）
- [ ] User 数据模型
- [ ] Activity 数据模型
- [ ] AthleteSettings 数据模型
- [ ] 基础页面路由（首页占位）
- [ ] .env 模板 + requirements.txt
- [ ] pytest 测试框架配置

### M2: 数据导入 `[x]` — Sprint 2 ✓
> TCX/GPX 文件解析 + 文件上传 API + 数据存储

- TCX 文件解析器（提取心率、功率、速度、海拔、踏频时间序列）
- GPX 文件解析器（提取 GPS 轨迹 + 基础指标）
- 文件上传 API（支持 TCX/GPX）
- 上传后自动解析并存入 Activity 集合
- 运动类型自动识别（骑行/跑步/游泳等）

### M3: 用户设定 `[~]` — Sprint 3（与 M4 合并，参数管理已在 S2 完成）
> 心率区/功率区配置 + 用户认证

- 用户注册/登录（邮箱验证码，参考 MotionO 模式）
- 心率区间配置 CRUD（Z1-Z5 阈值设定）
- 功率区间配置 CRUD
- FTP / 最大心率 / LTHR 等关键参数设置
- 个人资料页面

### M4: 指标计算引擎 `[x]` — Sprint 3 ✓
> TSS/CTL/ATL/TSB 及分区时间计算

- hrTSS 计算（基于心率区间）
- TSS 计算（基于功率，需要 FTP）
- CTL 指数加权移动平均（42 天窗口）
- ATL 指数加权移动平均（7 天窗口）
- TSB = CTL - ATL（训练压力平衡 / Form）
- 心率区间时间分布统计
- 功率区间时间分布统计
- 运动摘要计算（总时长、总距离、平均心率、NP、IF 等）

### M5: 数据可视化 `[x]` — Sprint 4 ✓
> Dashboard + 训练日历 + 趋势图表

- Dashboard 首页（今日 TSS、CTL/ATL/TSB 曲线、最近活动）
- 训练日历视图（按日/周/月展示训练量）
- 单次活动详情页（指标摘要 + 数据图表）
- Fitness/Fatigue/Form 趋势图
- 心率/功率区间分布图

### M6: LLM 运动建议 `[~]` — Sprint 5
> OpenAI GPT-5.4 集成

- OpenAI API 集成
- 训练周报自动生成
- 基于训练状态的个性化建议
- 历史趋势分析和预警

## 技术约束

- 数据库：MongoDB（无大规模部署需求）
- 后端：Python + Flask
- LLM：OpenAI GPT-5.4（M6 阶段引入）
- 不考虑高并发、分布式等生产级需求
