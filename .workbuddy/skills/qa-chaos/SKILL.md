---

name: qa-chaos
description: 混沌工程治理门禁技能：校验混沌实验规格是否「受治理」——业务关键实验必须定义稳态假设、终止条件、回退方案与爆炸半径；未受治理的关键实验产出阻断信号，避免在生产盲目注入故障。触发词："混沌工程", "chaos", "故障注入", "韧性", "resilience", "混沌实验", "稳态假设", or after qa-perf-analysis. 英文触发词（English triggers）：chaos engineering, fault injection, resilience.
license: MIT
metadata:
  version: "1.0.0"
  category: traditional
  stage: cross_cutting
  tier: 2
compatibility: "WorkBuddy / Claude / 通用 Agent（零依赖标准库）"
---
# qa-chaos 混沌工程治理门禁

在系统上线前，用**受控的故障注入**验证系统韧性（混沌工程）。本技能是一个**治理门禁**：它不实际对目标系统注入故障，而是校验你设计的混沌实验规格是否「受治理」——业务关键实验必须补齐四要素，否则视为高危、阻断发布。

> ⚠️ **治理门禁 · 不执行外部工具**：本技能仅校验混沌实验**规格**是否受治理，不实际对目标系统注入任何故障；所有判定基于你提供的 YAML/JSON 规格，不做运行时探测。

## 何时使用
- 你准备做故障演练 / 混沌实验（Pod 杀除、网络延迟、磁盘满、依赖超时等）。
- 你写好了混沌实验 YAML/JSON，想先卡一道「是否安全可控」的门禁。
- 在 `qa-perf-analysis` 之后，或作为发布前韧性保障的一环。

## 规则（治理四要素）
| 规则 | 含义 | 严重度 |
|---|---|---|
| C-STEADY | 实验须声明稳态假设（steady_state） | 缺则 high；业务关键缺则 critical |
| C-ABORT | 实验须有终止条件（abort_conditions 非空） | 缺则 high；业务关键缺则 critical/blocking |
| C-FALLBACK | 实验须有回退方案（fallback） | 缺则 high；业务关键缺则 critical/blocking |
| C-BLAST | 实验须界定爆炸半径（blast_radius） | 缺则 high |

业务关键（`business_critical: true`）实验缺上述任一要素 → 产出 `blocking=true` 信号，门禁失败。

## 使用方式
```bash
python qa-chaos/scripts/chaos_gate.py --spec chaos.json --out signals
```

## 诚实边界（重要）
- 本技能**只校验实验规格的治理完整性**，不实际对目标系统注入任何故障（无基础设施 / 网络依赖）。
- 实际故障注入需配合 Chaos Mesh / Litmus / 云厂商故障演练平台在**受控环境**执行；本技能确保「先治理、再注入」。
- 它不评估系统真实的韧性表现，只保证实验本身是安全可终止的。

## 参考资料

- 检查项、阈值、CLI 用法与常见坑：见 [`references/guide.md`](references/guide.md)。
