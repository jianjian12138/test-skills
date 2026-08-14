# Agent 评测指标指南（qa-agent-eval）

## 1. 五维度能力模型
| 维度 | 含义 | 0~1 评分依据 |
|---|---|---|
| task_completion | 任务是否达成 | 输出满足 goal 且通过 rubric |
| tool_use | 工具调用正确性 | 调用了正确的工具与参数 |
| planning | 规划能力 | 是否拆解子目标、步骤有序 |
| memory | 记忆 / 上下文保持 | 是否遗忘前置约束、跨步一致 |
| reliability | 可靠性 / 鲁棒性 | 异常下的稳定表现、不崩溃 |

加权示例（在 rubric_hidden.json 中声明 weight）：task_completion 0.4, tool_use 0.2, planning 0.15, memory 0.15, reliability 0.1。
总分 = Σ(dim_i × weight_i)，阈值 pass_threshold 通常取 0.8。

## 2. Pass@1 与 Pass^k / Pass@k（两者方向相反，切勿混用）

- **Pass@1**：单次尝试任务成功率 = 成功任务数 / 总任务数（per-task 宏平均）。
- **Pass^k（可靠性 / 一致性，k 次全过）**：同一任务独立采样 n 次、c 次成功，问「不放回抽 k 次全部成功」的概率。
  - 算法（**tau-bench 口径，无放回**）：对每个任务算 **`C(c, k) / C(n, k)`**，再对所有任务取平均（`pass_hat_k`）。n<k 或 c<k 时为 0。
  - k 越大数值越低；回答「这个 Agent 稳不稳，能不能每次都做对」。
  - 出处：**tau-bench 的 pass^k 口径正是 `C(c,k)/C(n,k)`（无放回）**，不是 `(c/n)^k`。后者是 i.i.d. 有放回近似（`pass_hat_k_iid_mc_legacy`），在小样本 / 部分成功区**系统性高估**可靠性，仅作对照、勿作主指标。
  - 严禁写成 `1-(1-p)^k`——那是 Pass@k 的近似，方向相反（一个往下走、一个往上走），混用会系统性高估可靠性（Jensen 不等式）。
- **Pass@k（能力上限 / 重试兜底，至少一次成功）**：k 次中至少一次成功的概率。
  - 无偏估计：`1 - C(n-c,k)/C(n,k)`（要求 n≥k）；小样本下勿用 `1-(1-p)^k` 近似作主指标（保留为 `*_mc_legacy` 仅对照）。
  - k 越大数值越高；回答「允许重试 k 次能否兜住」。
- 用途：Agent 上线建议 **Pass@5 ≥ 0.8**（能力兜底），**Pass^5** 反映稳态可靠性。两指标从不同角度回答"能不能用"，须同时报告。

## 3. G-Eval 思路（可选）
用强模型对轨迹做有参考 / 无参考打分：给出评分 rubric（1~5 分）与维度权重，让裁判模型输出分数与理由。注意单模型自偏好，建议多裁判（PoLL）取 trimmed mean。

## 4. 轨迹（trace）崩溃分析
见 grade_trace.py：检测 4 类长程崩溃——
- goal_drift：偏离原目标 / 遗忘任务
- loop：重复相同动作无法前进
- halt：提前终止 / 放弃
- tool_misuse：调用错误工具或错误参数

## 5. 报告口径
- 主指标：Pass@1、Pass@5、工具调用准确率、五维度均值。
- 失败归因：用 grade_trace 输出崩溃模式，配合失败轨迹人工复核。
- 可与 qa-report 共用报告模板，但评分口径以本指南为准。
