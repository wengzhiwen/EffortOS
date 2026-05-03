# Sprint 48: 输入校验 + 安全加固

**状态**: 已完成
**目标**: 持续优化 — API 输入校验审查 + 文件上传安全加固

## 任务清单

- [x] **文件上传安全审查** — 修复 XXE 漏洞：xml.etree.ElementTree → defusedxml.ElementTree
- [x] **API 输入校验审查** — MAX_CONTENT_LENGTH 已正确应用(50MB)，文件扩展名/UUID 文件名已有防护
- [x] **XSS 防护检查** — html.escape() 已在活动名称序列化中使用

## 安全审计结果

- **已修复**: XXE 注入漏洞（defusedxml 替换标准 XML 解析器）
- **已确认安全**: 文件扩展名白名单、UUID 安全文件名、MAX_CONTENT_LENGTH 限制、上传速率限制(10/h)
- **依赖更新**: requirements.txt 添加 defusedxml>=0.7
