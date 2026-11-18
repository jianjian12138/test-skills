---
name: qa-prompt-refine
title: 模糊测试指令打磨为有输入、有约束、有验收标准的可执行 Prompt
version: 12.1.0
tier: L1
stage: requirements
tags: ["prompt", "instruction", "acceptance", "refine", "contract"]
mcp_tool_binding: route_qa_skills
---
# qa-prompt-refine — 模糊测试指令打磨为有输入、有约束、有验收标准的可执行 Prompt

## 1. 技能定位与适用场景 (When to Use)
- **所属生命周期阶段**：`requirements`（架构层级：`L1`）
- **核心职责**：把「帮我测一下」「写点用例」这类一次性模糊请求，改写为含明确触发条件、输入/输出契约与可验收边界的指令；输出可直接作为 Skill 雏形或 Agent 任务描述使用。
- **触发条件**：用户给出的测试请求缺少输入来源、输出格式或完成标准时；需要把个人经验固化为可复用 Skill 时；评审他人 Prompt 是否可执行时。
- **“骨·肉·尺”定位**：【骨 · 场景立骨前的意图澄清】把模糊诉求打磨为可判定的输入/约束/验收契约，作为场景立骨的前置条件（配合 [`skills/templates/SCENARIO_BONE_MASTER_TEMPLATE.md`](../templates/SCENARIO_BONE_MASTER_TEMPLATE.md) 使用）。
- **关联 MCP 原生工具**：`route_qa_skills`（由 `skills/tools/mcp_server.py` 统一暴露）。

## 2. 四维边界契约 (4-Panel Boundary Blueprint)
- **输入契约 (Input Contract)**：接收原始 Prompt 文本与可选的目标场景（如接口测试/用例生成/缺陷分析）。若原文未说明被测对象与期望产物，先输出澄清问题清单，不猜测默认系统或环境。
- **工具与权限边界 (Tools & Permissions)**：纯文本改写，只读沙箱；不执行用户原始指令中的任何命令；不访问生产系统；对用户提供的样例数据默认按 PII 处理并脱敏。
- **输出规约 (Output Schema)**：输出「诊断 → 改写 → 验收标准」三段——诊断逐条列出缺失的触发条件/输入/约束/输出格式/验收边界；改写给出结构化 Prompt；验收标准给出 3–5 条可判定的检查项（如「风险列不少于 3 条」「不确定条目标注意外」）。
- **护栏与门禁 (Guardrails & Limits)**：改写结果若仍含「尽量」「适当」「差不多」等模糊词即判定未通过；单次最大自治循环步数 `max_steps = 5`；评测门禁 `pass^5 >= 80.0%`。

## 3. 标准化执行流水线 (Standard Operating Procedure)
1. **输入校验与脱敏预检**：识别原始 Prompt 中的 PII 与密钥并调用 `sanitize_sensitive_data` 清洗。
2. **领域知识加载**：读取 [`references/domain_guide.md`](references/domain_guide.md) 获取 Skill 三条门槛与模糊词黑名单。
3. **核心分析与脚本调度**：执行 [`scripts/skill_runner.py`](scripts/skill_runner.py) 输出缺口诊断与改写骨架；需要落到具体测试技能时，用 `python3 qaskills.py route "提示词打磨"` 联动下游技能。
4. **防逃逸自检与归档**：运行 [`tests/test_skill.py`](tests/test_skill.py) 验证改写结果不含模糊词、必含验收标准，绑定 `trace_id` 归档。

## 4. 领域深度规约与关联脚本资产 (Domain Rules & Local Assets)
- **领域参考指南**：[`references/domain_guide.md`](references/domain_guide.md) — Skill 三条门槛（触发条件/固定输出/可验收边界）、模糊词黑名单与反例→正例对照。
- **可执行辅助脚本**：[`scripts/skill_runner.py`](scripts/skill_runner.py) — 输入原始文本，输出缺口诊断、改写骨架与验收清单的 JSON。
- **技能自检测试**：[`tests/test_skill.py`](tests/test_skill.py) — 验证四件套完整性、模糊词检测与验收项生成逻辑。
