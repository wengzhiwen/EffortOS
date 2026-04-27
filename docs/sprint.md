# Sprint 21: 公共认证模块 + DRY 优化

**状态**: 已完成
**目标**: 消除认证逻辑的重复定义，提升代码 DRY 性

## 任务清单

- [x] S21-1: 创建 app/utils/auth.py 公共认证模块
- [x] S21-2: 更新 5 个蓝图使用公共模块（auth/activities/dashboard/params/ai）
- [x] S21-3: 代码质量检查

## 评估小结

Sprint 21 完成了认证模块的 DRY 优化：
- 新增 `app/utils/auth.py`：集中管理 `get_authenticated_user`、`require_user`、`user_filter`
- 5 个蓝图全部改用公共模块，消除 4 处重复定义
- auth/routes.py 保留兼容函数供现有 import 使用
- 123 个测试全部通过
