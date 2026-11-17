---
name: qa-security-report
title: 安全渗透与合规审计综合评估报告
version: 12.0.0
tier: L1
stage: security
tags: ["security-report", "cvss", "remediation", "owasp"]
mcp_tool_binding: sanitize_sensitive_data
---
# qa-security-report — 安全渗透与合规审计综合评估报告

## 1. 技能定位与适用场景 (When to Use)
- **所属生命周期阶段**：`security`（架构层级：`L1`）
- **核心职责**：汇总 OWASP 漏洞评级、CVSS 得分与修复加固路线图。
- **关联 MCP 原生工具**：`sanitize_sensitive_data`（由 `skills/tools/mcp_server.py` 统一暴露）。

## 2. 四维边界契约 (4-Panel Boundary Blueprint)
- **输入契约 (Input Contract)**：接收结构化业务需求、代码变更 Diff、接口 OpenAPI Schema 或页面 ARIA 快照；当关键参数缺失时，优先输出澄清问题列表，严禁静默猜测默认 ID 或生产环境地址。
- **工具与权限边界 (Tools & Permissions)**：默认运行于只读沙箱与脱敏测试数据集之上；任何外部调用或写操作均须通过域名白名单校验（遵循 OWASP AST10 v1.0-2026 技能安全规范）。
- **输出规约 (Output Schema)**：输出结构化 JSON 载荷或带明确严重级别（P0–P3）、前置条件、复现步骤与确定性断言的 Markdown 报告。
- **护栏与门禁 (Guardrails & Limits)**：单次最大自治循环步数 `max_steps = 5`，强制过滤未脱敏 PII 数据，CI 评测硬门禁要求 `pass^5 >= 80.0%`。

## 3. 标准化执行流水线 (Standard Operating Procedure)
1. **上下文校验与脱敏预检**：调用 `sanitize_sensitive_data` 过滤输入中的大陆身份证号、手机号与 API 密钥。
2. **领域知识加载**：按需读取本技能目录下的深度参考手册 [`references/domain_guide.md`](references/domain_guide.md)。
3. **核心分析与脚本调度**：调用 MCP 工具 `sanitize_sensitive_data` 或执行本地辅助脚本 [`scripts/skill_runner.py`](scripts/skill_runner.py) 生成测试资产。
4. **防逃逸自检与归档**：运行 [`tests/test_skill.py`](tests/test_skill.py) 校验输出格式，绑定 `trace_id` 归档产物。

## 4. 领域深度规约与关联脚本资产 (Domain Rules & Local Assets)
- **领域参考指南**：[`references/domain_guide.md`](references/domain_guide.md) — 包含 `qa-security-report` 的正交检查表、常见边界缺陷模式与行业最佳实践。
- **可执行辅助脚本**：[`scripts/skill_runner.py`](scripts/skill_runner.py) — 支持独立命令行运行与参数化 JSON 导出。
- **技能自检测试**：[`tests/test_skill.py`](tests/test_skill.py) — 验证本技能契约完整性与输出断言。
