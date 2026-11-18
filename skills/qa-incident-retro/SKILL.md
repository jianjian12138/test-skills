---
name: qa-incident-retro
title: 生产事故时间线复盘与改进项闭环跟踪
version: 12.1.0
tier: L1
stage: release_ops
tags: ["incident", "postmortem", "rca", "action-items", "retro"]
mcp_tool_binding: route_qa_skills
---
# qa-incident-retro — 生产事故时间线复盘与改进项闭环跟踪

## 1. 技能定位与适用场景 (When to Use)
- **所属生命周期阶段**：`release_ops`（架构层级：`L1`）
- **核心职责**：将生产事故整理为「时间线 → 根因 → 改进项」三段式复盘报告；每条改进项强制携带责任人、截止时间与可验证的完成标准，杜绝「改进项写完后无人认领」。
- **触发条件**：线上 P0/P1 故障恢复后、重大缺陷引发业务损失后、需要向甲方交付事故复盘文档时。
- **“骨·肉·尺”定位**：【尺 · 验收与度量】以事故时间线与改进项闭环校准放量后的门禁，确保问题可追溯、可收敛（配合 [`skills/templates/SCENARIO_BONE_MASTER_TEMPLATE.md`](../templates/SCENARIO_BONE_MASTER_TEMPLATE.md) 使用）。
- **关联 MCP 原生工具**：`route_qa_skills`（由 `skills/tools/mcp_server.py` 统一暴露）。

## 2. 四维边界契约 (4-Panel Boundary Blueprint)
- **输入契约 (Input Contract)**：接收事故时间线原始记录（告警时刻、发现时刻、止血时刻、恢复时刻）、trace_id、影响面与已做的处置动作。缺失关键时间戳或责任人时必须输出澄清清单，严禁编造人名、时间或根因。
- **工具与权限边界 (Tools & Permissions)**：默认只读沙箱；事故数据中的用户标识、手机号、账号必须先经 `sanitize_sensitive_data` 脱敏；禁止把生产密钥、内部 IP 直接写入复盘文档。
- **输出规约 (Output Schema)**：输出结构化 JSON 或三段式 Markdown——①时间线表格（时刻/事件/证据来源）②根因分析（直接原因 + 5 Why 根因 + 系统性根因）③改进项表格（改进项/责任人/截止日期/验收标准/当前状态），缺一不可。
- **护栏与门禁 (Guardrails & Limits)**：改进项无责任人或无截止日期即判定复盘不完整（`status=BLOCKED`）；单次最大自治循环步数 `max_steps = 5`；评测门禁 `pass^5 >= 80.0%`。

## 3. 标准化执行流水线 (Standard Operating Procedure)
1. **输入校验与脱敏预检**：调用 `sanitize_sensitive_data` 过滤事故文本中的 PII 与密钥；核对四个关键时间戳（发现/定位/止血/恢复）是否齐全。
2. **领域知识加载**：读取 [`references/domain_guide.md`](references/domain_guide.md) 获取时间线粒度、5 Why 追问深度与改进项验收标准的写法。
3. **核心分析与脚本调度**：执行 [`scripts/skill_runner.py`](scripts/skill_runner.py) 生成复盘骨架并校验改进项字段；可用 `python3 qaskills.py route "生产事故复盘"` 联动 `qa-log-triage`（链路还原）与 `qa-release-check`（上线门禁回归）。
4. **防逃逸自检与归档**：运行 [`tests/test_skill.py`](tests/test_skill.py) 校验输出契约，绑定 `trace_id` 归档。

## 4. 领域深度规约与关联脚本资产 (Domain Rules & Local Assets)
- **领域参考指南**：[`references/domain_guide.md`](references/domain_guide.md) — 时间线四时刻模型、5 Why 根因法、改进项 SMART 验收标准与无责复盘原则。
- **可执行辅助脚本**：[`scripts/skill_runner.py`](scripts/skill_runner.py) — 输入输出结构化的复盘校验结果，支持命令行 JSON 导出。
- **技能自检测试**：[`tests/test_skill.py`](tests/test_skill.py) — 验证四件套完整性与改进项门禁逻辑。
