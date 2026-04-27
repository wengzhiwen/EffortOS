# Sprint 1: 项目骨架搭建

**状态**: 已完成
**对应 Milestone**: M1
**目标**: 搭建 Flask 应用框架、MongoDB 连接、核心数据模型和基础路由

## 任务清单

- [x] S1-1: Flask 应用工厂模式 + config 配置（run.py 入口 + app/__init__.py 工厂 + app/config.py）
- [x] S1-2: MongoDB 连接初始化（MongoEngine 集成到应用工厂）
- [x] S1-3: 项目目录结构（创建 blueprints/models/services/templates 目录及 __init__.py）
- [x] S1-4: User 数据模型（邮箱、昵称、创建时间、最后登录）
- [x] S1-5: Activity 数据模型（运动类型、时间、原始数据摘要、计算指标、文件引用）
- [x] S1-6: AthleteSettings 数据模型（心率区间阈值 Z1-Z5、功率区间阈值、FTP、最大心率）
- [x] S1-7: 基础页面蓝图（pages blueprint，首页和关于页占位模板）
- [x] S1-8: .env 配置模板 + requirements.txt 依赖清单
- [x] S1-9: pytest 测试框架配置（conftest.py + 测试用的 app fixture）

## 评估小结

Sprint 1 全部完成。创建了完整的项目骨架：
- Flask 应用工厂模式 + 三套配置（development/production/testing）
- MongoEngine 集成 + 三个核心数据模型（User、Activity、AthleteSettings）
- Pages 蓝图 + 基础页面模板（base.html、index.html、about.html）
- venv 虚拟环境 + requirements.txt + pyproject.toml
- 4 个基础测试全部通过

下一步进入 Sprint 2（M2: 数据导入），实现 TCX/GPX 文件解析和上传。
