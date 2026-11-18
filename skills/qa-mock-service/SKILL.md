---
name: qa-mock-service
title: 下游依赖未就绪时的 Mock 服务与联调阻塞解除
version: 12.1.0
tier: L2
stage: tdm_cases
tags: ["mock", "stub", "dependency", "contract", "offline"]
mcp_tool_binding: generate_test_data
---
# qa-mock-service — 下游依赖未就绪时的 Mock 服务与联调阻塞解除

## 1. 技能定位与适用场景 (When to Use)
- **所属生命周期阶段**：`tdm_cases`（架构层级：`L2`）
- **核心职责**：当下游服务未部署、第三方接口不可用或沙箱环境缺依赖时，基于 OpenAPI 契约生成静态响应桩与状态化 Mock 序列，让主流程先跑通，不阻塞联调。
- **触发条件**：下游未就绪但需验证上游主链路；第三方按次计费/有配额限制；需要稳定复现下游超时、500、异常业务码等难构造场景。
- **“骨·肉·尺”定位**：【肉 · 节点深潜与联调解阻】在场景节点下游未就绪时提供契约一致的桩与故障注入，保证链路可跑通并保留真实回归回滚提示（配合 [`skills/templates/SCENARIO_BONE_MASTER_TEMPLATE.md`](../templates/SCENARIO_BONE_MASTER_TEMPLATE.md) 使用）。
- **关联 MCP 原生工具**：`generate_test_data`（由 `skills/tools/mcp_server.py` 统一暴露）。

## 2. 四维边界契约 (4-Panel Boundary Blueprint)
- **输入契约 (Input Contract)**：接收目标接口的 OpenAPI 片段（路径、方法、响应 schema）、期望状态序列与故障注入项。缺少响应 schema 时必须要求补充或明确标注「仅结构占位」，禁止猜测真实业务字段与生产地址。
- **工具与权限边界 (Tools & Permissions)**：Mock 仅绑定 `127.0.0.1` 本地端口，默认只读生成；禁止把 Mock 指向生产域名；Mock 响应中不得回填真实 PII，须使用 `qa-test-data` 的合成数据。
- **输出规约 (Output Schema)**：输出结构化 JSON——接口清单、响应样例、状态切换序列、故障注入开关与「恢复真实服务」的切换说明；Markdown 报告需含联调前置条件与可验证断言。
- **护栏与门禁 (Guardrails & Limits)**：禁止在 Mock 中硬编码真实密钥或生产 URL；单次最大自治循环步数 `max_steps = 5`；评测门禁 `pass^5 >= 80.0%`。

## 3. 标准化执行流水线 (Standard Operating Procedure)
1. **输入校验与脱敏预检**：解析 OpenAPI 片段，核对响应 schema；用 `sanitize_sensitive_data` 清洗样例中的敏感字段。
2. **领域知识加载**：读取 [`references/domain_guide.md`](references/domain_guide.md) 获取静态桩/状态化桩/故障注入的选型规则。
3. **核心分析与脚本调度**：执行 [`scripts/skill_runner.py`](scripts/skill_runner.py) 生成响应样例与状态序列；造数需求联动 `qa-test-data`，HAR 回放需求联动 `qa-shadow-replay`。
4. **防逃逸自检与归档**：运行 [`tests/test_skill.py`](tests/test_skill.py) 校验无生产地址、无真实密钥，绑定 `trace_id` 归档。

## 4. 领域深度规约与关联脚本资产 (Domain Rules & Local Assets)
- **领域参考指南**：[`references/domain_guide.md`](references/domain_guide.md) — 三类 Mock 选型、状态序列设计、故障注入矩阵与「Mock 不得替代真实联调」的边界。
- **可执行辅助脚本**：[`scripts/skill_runner.py`](scripts/skill_runner.py) — 由 schema 生成样例响应与状态序列，支持故障注入配置，纯标准库零依赖。
- **技能自检测试**：[`tests/test_skill.py`](tests/test_skill.py) — 验证四件套完整性、样例生成与生产地址/密钥拦截逻辑。
