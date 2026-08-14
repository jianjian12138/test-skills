---

name: qa-agent-eval
description: |-
  评估被测 Agent 本身的能力与可靠性（与被测业务系统区分）。提供任务完成率 Pass@1/Pass^k、工具调用准确率、规划/记忆/可靠性五维度评分、轨迹（trace）崩溃分析，以及自包含评测任务目录（含隐藏 rubric）的设计与生成。当用户需要评测 AI Agent、做 Agent 基准测试、Agent 能力评估、Agent 可靠性度量、Agent 轨迹分析、Pass@k 统计、构建 Agent 评测数据集时使用。
  英文触发词（English triggers）：agent evaluation, benchmark, Pass@k, LLM eval.
license: MIT
compatibility: "WorkBuddy / Claude / 通用 Agent（零依赖标准库）"

metadata:
  version: "1.0.0"
  category: agent
  stage: agent_testing
  tier: 1
---
# qa-agent-eval — Agent 能力评测

## 何时使用
- 要量化一个 Agent 的**任务完成能力**（不是测它的下游业务接口）。
- 需要 Pass@1 / Pass^k 可靠性指标、工具调用准确率、规划/记忆/可靠性五维度。
- 要分析 Agent 运行轨迹（trace）中的长程崩溃模式。
- 要搭建自包含、可复现的 Agent 评测任务（含隐藏评分 rubric）。

## 边界声明（重要）
> 本技能测的是 **Agent 本身**（决策 / 工具调用 / 可靠性）。
> 若目标是测"有确定接口的业务系统"（接口 / UI / 性能 / 安全），请用 27 个传统 QA 技能（qa-api-runner / qa-perf-* / qa-security-scan 等）。
> 二者场景不同，不要混用。

> **不涉及模型推理**：本技能**不加载 / 不运行任何 LLM 权重**，只消费被测 Agent 的**运行结果产物**（runs.json / trace / rubric）做统计与判分；被测 Agent 的推理能力由其自身的推理引擎提供，本技能不替代、也不参与其推理过程。

## 使用流程
1. 用 `gen_task.py` 生成自包含任务目录（可见 task.md + 隐藏 rubric_hidden.json + harness 桩）。
2. 把 Agent 接入 harness 跑任务，产出 results（每条 run 含 success / tool_calls / dims / trace）。
3. 用 `calc_metrics.py` 计算 Pass@1、Pass^k、工具调用准确率、五维度均值（**五维度为被测方自报，非 ground-truth**，报告内已显式标注，应以 checkers 实测为准）。
4. 用 `grade_trace.py` 对失败 / 可疑轨迹做崩溃模式归因。
5. 汇总成评测结论（可配合 qa-report 出报告，但评分口径用本技能）。

## 脚本
- `scripts/gen_task.py --out <dir> --tasks <n>`：生成自包含任务骨架。
- `scripts/calc_metrics.py --results <file> --k 5`：输出指标。
- `scripts/grade_trace.py --trace <file|->`：输出检测到的崩溃模式。

## Outputs（质量信号契约，P1-6）
- `calc_metrics.py` 额外写出 `signals/qa-agent-eval.json`（source=qa-agent-eval）：
  - `agent_eval_pass_at_k`：Pass@k 低于 `--signal-threshold`（默认 0.8）→ `blocking=true`（high）；否则非阻断信息信号。
  - `agent_eval_low_ci`：Pass@1 的 Wilson 95% CI 宽度 > 0.2（样本不足）→ 非阻断告警。
  - 该信号被 `qa-release-check` 门禁聚合，作为发布门禁输入（ADR-002）。

## 参考
- `references/metrics-guide.md`：五维度、Pass^k、G-Eval、trace 分析定义。
- `references/task-design.md`：自包含任务目录规范与隐藏 rubric 实践。
- `references/ai-false-pass.md`：AI 假通过 9 模式 + 永真断言黑名单 + BLOCKED 快速路径（`grade_run.py` 据此做空 checkers / 永真断言 fail-closed）。

## 结构化事件流（W3 增强）

`scripts/trace_event.py` 将评测 / 运行 trace 升级为结构化事件流：工具调用（tool_call）、状态写入（state_write）、
模型重试（model_retry）、任务结束（task_end）四类事件，均关联 run_id / step / 上下游 event_id。
支撑**可重放**（replay 按序还原）与**失败分类**（模型重试次数、任务终态分布），由 `classify` 输出摘要。

## Agent 评测深化（V10 / W6·W8·W9）

`scripts/scorecard.py` 把度量从 Pass@k 扩展到更贴近 Agent 能力画像的体系：

- **六维评分卡**（`compute_six_dim`）：任务成功率 / 工具调用准确性（直接计算）；规划合理性、反思纠错（代理指标，来自结构化事件的重试占比与恢复率）；轨迹效率（需成本预算归一化）；安全合规（需安全判定）。**诚实约定**：无法从可用数据计算的维度显式标 `available=False / value=None`，绝不伪称 1.0。
- **轨迹成本**（`trajectory_cost`）：步数 / Token / 耗时 / 成本聚合（W6 成本维度）。
- **错误分类**（`error_breakdown`）：失败 run 分到 timeout / planning_loop / tool_error / unknown（W8 启发式归类）。
- **能力探针基线**（`probe_baseline`）：按 bucket 分桶算 pass_rate / efficiency_rate / delta，并给出稳定方差（<3% 标志）与「通过率—有效率一致性」——替代单点通过率，直接补 T-01 时间炸弹的度量子（W9）。
- **真实 trace 导入**（`trace_event.py --import-trace`）：把通用 agent 轨迹（OpenTelemetry spans / agentdojo trajectory）转换为本项目结构化事件，支撑真实评测接入（G-02）。

## 借鉴来源（仅方法论）
Eval-Anything（评测即 skill 三轴）、deepeval（Agentic 指标）、tau-bench（Pass^k 可靠性）、agentdojo（效用 / ASR 双轴）。本技能取其度量方法，不引入其平台依赖。
