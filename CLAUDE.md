# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

EffortOS 是一个运动数据追踪和分析工具（类似 [intervals.icu](https://www.intervals.icu/)），用户上传 TCX/GPX 运动数据文件，系统基于用户的心率区/功率区设定计算疲劳值、TSS、Fitness 等运动指标，并通过 OpenAI GPT-5.4 提供个性化运动建议。

本项目同时是一个 **AI 自驱动实验项目**：以 Claude Code 为核心，持续执行「规划 → 选取任务（设计/研发/测试） → 实施 → 评估 → 再规划」的循环，在只有明确目标而无详细设计的基础上不断自我进化。

## 技术栈

- **后端**: Python + Flask
- **数据库**: MongoDB（无大规模部署/高并发需求）
- **前端**: Flask 模板 + 现代前端（待定）
- **LLM**: OpenAI GPT-5.4 API

## 开发命令

```bash
# 安装依赖
pip install -r requirements.txt

# 启动开发服务器（需要先运行 MongoDB）
python run.py

# 代码格式化
ruff format app/
ruff check app/

# 运行测试
pytest

# 运行单个测试文件
pytest tests/test_xxx.py

# 运行单个测试用例
pytest tests/test_xxx.py::test_function_name
```

## 架构设计原则

### 核心功能模块

1. **数据导入** — 解析 TCX/GPX 文件，提取时间序列数据（心率、功率、速度、海拔、踏频等）
2. **用户设定** — 心率区间（Z1-Z5）、功率区间配置
3. **运动指标计算** — TSS（训练压力分数）、CTL（慢性训练负荷/fitness）、ATL（急性训练负荷/fatigue）、TSB（训练压力平衡/form）、疲劳值等
4. **LLM 运动建议** — 基于用户历史数据和当前训练状态，调用 OpenAI API 生成训练建议
5. **数据可视化** — 运动数据图表展示、训练日历、趋势分析

### 项目结构（预期）

```
app/
├── __init__.py          # 应用工厂，注册蓝图、初始化扩展
├── config.py            # 配置类
├── blueprints/          # 蓝图路由（auth, activities, settings, dashboard 等）
├── models/              # MongoEngine 数据模型
├── services/            # 业务逻辑层
│   ├── parse_service.py # TCX/GPX 文件解析
│   ├── metrics_service.py # 运动指标计算引擎
│   └── llm_service.py   # OpenAI API 集成
└── templates/           # Jinja2 模板
```

### 数据模型核心概念

- **User** — 用户信息、心率区间设定、功率区间设定
- **Activity** — 单次运动记录：原始数据摘要、计算指标、文件引用
- **AthleteSettings** — 运动员配置：心率区间阈值、功率区间阈值、FTP、最大心率等

### 运动指标计算要点

- TSS 计算需根据运动类型选择基于心率（hrTSS）或基于功率（TSS）的算法
- CTL/ATL 使用指数加权移动平均（通常窗口为 42 天 / 7 天）
- 心率区间时间分布需对齐用户自定义的区间阈值
- 功率指标依赖用户设定的 FTP 值

## AI 自驱动工作流

### 核心文件

| 文件 | 作用 |
|------|------|
| `.claude/loop.md` | `/loop` 每次迭代读取的指令，定义完整的自驱动流程 |
| `docs/roadmap.md` | 项目总路线图，milestone 拆分和进度追踪 |
| `docs/sprint.md` | 当前 sprint 的任务清单（`[ ]`/`[~]`/`[x]`/`[!]` 状态标记） |
| `docs/work-log.md` | 工作日志，每次迭代完成后追加记录 |

### 启动方式

在项目目录下执行：
```
/loop
```

Claude Code 会自动读取 `.claude/loop.md`，开始自驱动循环。每个迭代完成一个小任务后自动 commit，当前 sprint 全部完成后自动规划下一 sprint。

### 迭代循环

1. 读取 sprint.md 和 work-log.md 获取当前状态
2. 有未完成任务 → 实现 → 验证 → commit → 更新文档
3. sprint 完成 → 评估项目状态 → 规划新 sprint → commit
4. 阻塞 → 记录原因 → 尝试替代方案

### Git 策略

每完成一个小任务自动 commit，格式：`feat/module: 简短描述`。不要 push，由用户决定何时推送。

## 注意事项

- 所有文档和注释以中文撰写
- API 响应格式统一为 JSON，包含 `code`、`message`、`data` 字段
- 运动数据文件可能较大，解析时注意内存使用，采用流式解析
- LLM API 调用需处理超时和错误重试
- 环境变量配置在 `.env` 文件中，包含 MongoDB 连接、OpenAI API Key 等
- 参考 sibling 项目 MotionO（`../MotionO/`）的 Flask + MongoDB 架构模式
