# Sprint 5: LLM 运动建议

**状态**: 已完成
**对应 Milestone**: M6
**目标**: OpenAI API 集成、训练周报生成、个性化建议

## 任务清单

- [x] S5-1: OpenAI API 服务层（llm_service.py）— API 调用封装、错误重试
- [x] S5-2: 训练状态上下文构建 — PMC 数据 + 最近活动整理为 LLM prompt
- [x] S5-3: 训练周报生成 API — POST /api/ai/weekly-report
- [x] S5-4: 个性化建议 API — POST /api/ai/suggestion
- [x] S5-5: AI 教练页面 — 周报展示 + 自由提问

## 评估小结

Sprint 5 全部完成。实现了 AI 运动建议功能：
- llm_service.py：OpenAI API 封装（带重试机制）
- 训练周报：基于本周活动 + PMC 状态生成周报
- 个性化建议：支持自由提问，基于 PMC 和最近 TSS 数据
- AI 教练页面：周报生成 + 建议获取 UI
- 系统提示词：运动科学专业知识 + 中文输出
- 68 个测试全部通过
