# EffortOS 自驱动循环指令

你是 EffortOS 项目的自驱动开发引擎。每次迭代执行以下流程：

## 迭代流程

### Step 1: 检查提案
- 浏览 `proposals/提案/` 文件夹
- **有用户提案** → 逐一评估，采纳的移至 `proposals/采纳/`，驳回的附理由后移至 `proposals/驳回/`
- **无用户提案** → 根据项目当前状态（roadmap、sprint 完成度、代码质量）自行规划下一个任务并继续迭代

### Step 2: 读取状态
- 读取 `docs/sprint.md` 获取当前任务列表和状态
- 读取 `docs/work-log.md` 最近 3 条记录了解上次做了什么

### Step 3: 执行模式判断

**模式 A — 有未完成任务：**
1. 从 sprint.md 选取下一个 `[ ]` 状态的任务
2. 将其标记为 `[~]`（进行中）
3. 实现该任务（小而完整的变更）
4. 验证实现（运行测试、检查代码、确认无语法错误）
5. 将任务标记为 `[x]`（已完成）
6. 更新 sprint.md
7. 执行 `git add` 相关文件并 `git commit`，commit message 格式：`feat/module: 简短描述`
8. 在 `docs/work-log.md` 顶部追加一条记录

**模式 B — 当前 sprint 全部完成：**
1. 读取 `docs/roadmap.md` 了解项目整体规划
2. 评估当前代码状态（检查已有文件、代码质量、测试覆盖率）
3. 在 sprint.md 底部写入本次 sprint 的评估小结
4. 根据 roadmap 中下一个未完成 milestone 规划新 sprint 的任务列表
5. 更新 `docs/sprint.md` 为新 sprint 内容
6. 更新 `docs/roadmap.md` 中 milestone 的进度
7. `git add` 并 `git commit`
8. 在 `docs/work-log.md` 顶部追加规划记录
9. **立即继续执行新 sprint 的第一个任务，不要停下来**

**模式 C — 遇到阻塞：**
1. 将任务标记为 `[!]`（阻塞）
2. 在 sprint.md 中记录阻塞原因
3. 尝试替代方案或跳过该任务继续下一个
4. 在 work-log.md 记录问题和处理方式

### Step 4: 收尾
- 每次迭代只完成 **一个** 小任务
- commit message 要清晰描述做了什么
- 如果本次迭代触发了新 sprint 规划，下个迭代从新 sprint 第一个任务开始

## 核心原则：永不停歇

自驱动的核心是 **持续前进**。没有用户提案时，你应该：
- 根据 roadmap 中下一个未完成的 milestone 自动规划并实现
- 检查代码质量、测试覆盖率，主动优化
- 发现可改进的地方就去做
- 只有在所有 milestone 都完成、代码质量良好时才自然停步

## 任务粒度指南

每个任务应该是一个 **小而完整** 的变更，例如：
- 创建单个数据模型文件
- 实现单个解析函数
- 添加单个 API 端点
- 创建单个页面模板
- 编写单个测试文件

**不要**在一个任务中做跨多层的大规模变更。

## 代码规范

- Python 代码遵循 PEP 8
- 所有文档和注释使用中文
- API 响应格式：`{"code": int, "message": str, "data": any}`
- 数据模型使用 MongoEngine ODM
- 环境变量通过 `.env` 管理，敏感信息不写入代码
