---
name: qa-flaky-detect
title: 不稳定用例（Flaky Test）根因识别与隔离治理
version: 12.0.0
tier: L2
stage: quality_gates_agent
tags: ["flaky", "quarantine", "async-wait", "race-condition"]
mcp_tool_binding: run_quality_gate
---
# qa-flaky-detect — 不稳定用例（Flaky Test）根因识别与隔离治理

## 1. 技能定位与适用场景 (When to Use)
- **所属生命周期阶段**：`quality_gates_agent`（架构层级：`L2`）
- **核心职责**：识别异步竞态、时间依赖与共享状态污染导致的 Flaky 用例并自动隔离。
- **关联 MCP 原生工具**：`run_quality_gate`（通过 `skills/tools/mcp_server.py` 暴露）。

## 2. 四维边界契约 (4-Panel Boundary Blueprint)
- **输入契约 (Input Contract)**：接收结构化业务上下文、代码变更片段或接口 Schema；若关键上下文缺失，必须先输出澄清问题清单，禁止静默猜测默认 ID 或生产地址。
- **工具与权限边界 (Tools & Permissions)**：默认在只读沙箱与脱敏数据集上运行；涉及写操作或外部请求时强制经过白名单校验（符合 OWASP AST10 v1.0-2026 技能安全规范）。
- **输出规约 (Output Schema)**：输出结构化 JSON 载荷或带明确优先级（P0–P3）、前置条件、执行步骤与可验证断言的 Markdown 报告。
- **护栏与门禁 (Guardrails & Limits)**：单次最大循环步数 `max_steps = 5`，严禁将未脱敏 PII 数据写入日志，评测门禁要求 `pass^5 >= 80.0%`。

## 3. 标准化执行流水线 (Standard Operating Procedure)
1. **上下文校验与脱敏预检**：调用 `sanitize_sensitive_data` 过滤输入中的手机号、身份证号与密钥。
2. **核心分析与引擎调度**：根据 `L2` 级别调用 `run_quality_gate` 执行确定性分析或生成测试资产。
3. **自愈与防逃逸校验**：针对边界条件、异常分支与跨租户越权路径补充逆向验证断言。
4. **可追溯归档**：绑定当前 `trace_id` 输出结构化产物并更新质量门禁评分。
