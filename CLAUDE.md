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

所有 Python 命令使用项目虚拟环境 `venv/`，即 `venv/bin/python`、`venv/bin/pip`、`venv/bin/pytest` 等。

```bash
# 创建虚拟环境（首次）
python3 -m venv venv

# 安装依赖
venv/bin/pip install -r requirements.txt

# 启动开发服务器（需要先运行 MongoDB）
venv/bin/python run.py

# 代码格式化 + lint
venv/bin/ruff check --fix app/
venv/bin/ruff format app/

# 运行测试
venv/bin/pytest

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
| `proposals/` | 用户提案机制（详见下方） |

### 提案机制（proposals/）

用户通过 `proposals/` 文件夹参与迭代方向，这是迭代过程中用户与 Claude Code 的唯一沟通方式。

```
proposals/
├── 提案/    # 用户将想法以 markdown 文件放入此文件夹
├── 采纳/    # Claude Code 采纳的提案会被移入此处
└── 驳回/    # Claude Code 驳回的提案会被移入此处，并附带驳回理由
```

**流程：**
1. 用户将提案以 markdown 文件放入 `proposals/提案/`
2. Claude Code 每次规划时必须先浏览 `proposals/提案/` 文件夹
3. **采纳** → 将提案内容纳入计划，文件移至 `proposals/采纳/`
4. **驳回** → 在文件末尾追加驳回理由，文件移至 `proposals/驳回/`

### 启动方式

在项目目录下执行：
```
/loop
```

Claude Code 会自动读取 `.claude/loop.md`，开始自驱动循环。每个迭代完成一个小任务后自动 commit，当前 sprint 全部完成后自动规划下一 sprint。

### 迭代循环

1. **检查提案** → 浏览 `proposals/提案/`，处理用户提案（采纳或驳回）
2. 读取 sprint.md 和 work-log.md 获取当前状态
3. 有未完成任务 → 实现 → 验证 → commit → 更新文档
4. sprint 完成 → 评估项目状态 → 规划新 sprint → commit
5. **每一轮完成后必须：重启用户体验服务器 + 更新 markdown 文档**（见下方）
6. roadmap 完成 → 进入持续优化模式（代码质量、测试、性能、UX、安全）
7. 阻塞 → 记录原因 → 尝试替代方案

### 每轮完成后的收尾动作

每完成一个 sprint（或一个独立任务），**必须**执行以下收尾步骤：

1. **更新 markdown 文档**：
   - `docs/sprint.md` — 更新当前 sprint 状态和任务清单
   - `docs/work-log.md` — 追加本次迭代的完成记录
   - `docs/roadmap.md` — 更新相关 milestone 的完成状态

2. **重启用户体验服务器**：
   - 先终止端口 9527 上的旧进程：`kill $(lsof -ti :9527) 2>/dev/null`
   - 后台启动新实例：`FLASK_ENV=development PORT=9527 venv/bin/python run.py &`
   - 验证服务可用：`curl -s -o /dev/null -w "%{http_code}" http://localhost:9527/` 应返回 200
   - 目的：让用户随时通过 http://localhost:9527 体验最新功能

3. **代码质量检查**：
   - 运行 `venv/bin/ruff check --fix app/ && venv/bin/ruff format app/` 修复 lint 和格式
   - 确保无 lint 错误后再提交

4. **提交 git**：
   - 将所有变更（代码 + 文档）一起 commit，格式 `feat/module: 描述`
   - 不要 push，由用户决定何时推送

### 核心原则：永不停止优化

没有用户提案时不会停止。Roadmap 完成也不是终点，进入持续优化模式：主动搜索行业最佳实践、审视代码质量、补充测试、改进用户体验。**只有用户明确要求停止或 token 耗尽时才停下。**

### 错误处理：永远重试

迭代过程中遇到的任何错误（API 调用失败、网络超时、工具调用报错、文件读写异常等），**只要不是明确的 API 额度/配额耗尽（rate limit exceeded / quota exceeded），都必须继续重试**。重试策略：
- 先分析错误原因，尝试修复后重试
- 若同一问题连续失败 3 次，换一种实现方式绕过
- 记录错误但不停止迭代，跳过当前子任务继续下一个

### 用户中断：即时响应

当用户通过 Claude Code TUI 直接给出指示时：
- **立即处理**：将用户指示插入到当前正在进行的工作中（如正在写代码则先完成当前文件的修改，然后处理用户指示）
- **规划优先**：如果用户指示是方向性的（如"加一个新功能"），将其规划到当前或下一轮 sprint 中
- 用户指示的优先级高于自驱动循环中的任何计划任务

### 迭代连续性：永不中断

**一轮工作完成后，必须立即开始下一轮迭代**，不等待任何外部触发。具体要求：
- sprint 完成 → 更新文档 → commit → 立即规划下一 sprint → 开始实施
- 没有新提案时，自主决定下一轮优化方向（代码质量、测试覆盖率、性能、UX、安全等）
- 不输出"等待用户指示"或类似停顿语句，永远在行动

### Git 策略

每完成一个小任务自动 commit，格式：`feat/module: 简短描述`。不要 push，由用户决定何时推送。

## 注意事项

- 所有文档和注释以中文撰写
- API 响应格式统一为 JSON，包含 `code`、`message`、`data` 字段
- 运动数据文件可能较大，解析时注意内存使用，采用流式解析
- LLM API 调用需处理超时和错误重试
- 环境变量配置在 `.env` 文件中，包含 MongoDB 连接、OpenAI API Key 等
- 参考 sibling 项目 MotionO（`../MotionO/`）的 Flask + MongoDB 架构模式
- `samples/` 文件夹中放置了 TCX/GPX 运动数据文件，仅用于本地开发分析和测试，不提交到代码库，也不是项目交付物
