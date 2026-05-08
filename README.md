# EffortOS

AI 自迭代的运动数据追踪与分析工具，类似 [intervals.icu](https://www.intervals.icu/)。上传 TCX/GPX 运动数据文件，系统自动计算 TSS、CTL、ATL、TSB 等训练指标，并通过 LLM 提供个性化运动建议。

本项目同时是一个 **AI 自驱动实验**：以 Claude Code 为核心，持续执行「规划 → 选取任务 → 实施 → 评估 → 再规划」的循环，在只有明确目标而无详细设计的基础上不断自我进化。

## 功能概览

- **数据导入** — 解析 TCX/GPX 文件，提取心率、功率、速度、海拔、踏频等时间序列数据
- **训练指标** — TSS（训练压力分数）、CTL（fitness）、ATL（fatigue）、TSB（form）、NP、IF 等
- **GPS 地图** — 活动路线可视化，按功率/速度颜色渐变渲染
- **训练日历** — GitHub 风格的训练热力图，hover 显示活动详情
- **最佳表现** — 各时间窗口的峰值功率/心率，PB 标记当前记录保持者
- **AI 教练** — 基于 OpenAI GPT 生成个性化训练建议和周报
- **深色/浅色主题** — 完整的主题切换支持
- **响应式设计** — 桌面端和移动端自适应

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python + Flask |
| 数据库 | MongoDB (MongoEngine ODM) |
| 前端 | Jinja2 模板 + 原生 JS + Chart.js + Leaflet |
| LLM | OpenAI GPT API |
| 代码质量 | Ruff (lint + format) + Pytest |

## 快速开始

```bash
# 克隆项目
git clone https://github.com/wengzhiwen/EffortOS.git
cd EffortOS

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入 MongoDB 连接、OpenAI API Key 等

# 启动开发服务器
python run.py
```

访问 http://localhost:9527 即可使用。

## AI 自驱动工作流

项目的迭代由 Claude Code 自主完成，工作流如下：

1. 执行 `/loop` 启动自驱动循环
2. 按优先级寻找任务：特殊 Sprint（Bug 大扫除）→ 用户提案 → GitHub Issues → 等待
3. 选取任务后自动规划、实现、测试、提交
4. 每轮完成后重启服务器并更新文档

任务来源：
- **用户提案** — 在 `proposals/提案/` 放入 markdown 文件
- **GitHub Issues** — 创建 Issue 并 assign 给 wengzhiwen

所有从 GitHub Issues 获取的提案都经过 10 项安全评估（范围检查、凭证安全、注入检测等），防止恶意注入。

## 项目结构

```
app/
├── __init__.py              # 应用工厂
├── config.py                # 配置
├── blueprints/              # 路由蓝图
│   ├── activities/          # 活动相关 API
│   ├── dashboard/           # 仪表盘
│   └── ...
├── models/                  # MongoEngine 数据模型
├── services/                # 业务逻辑
│   ├── parse_service.py     # TCX/GPX 解析
│   ├── metrics_service.py   # 运动指标计算引擎
│   └── llm_service.py       # OpenAI API 集成
└── templates/               # Jinja2 模板
```

## 开发命令

```bash
# 代码格式化 + lint
venv/bin/ruff check --fix app/ && venv/bin/ruff format app/

# 运行测试
venv/bin/pytest

# 启动开发服务器
venv/bin/python run.py
```

## License

MIT
