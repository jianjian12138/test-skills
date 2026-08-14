---

name: qa-mutation
description: |-
  变异测试分数治理门禁：本技能**不注入变异体、不运行测试**，仅基于变异工具(mutmut/cosmic-ray/pit)已产出的 mutants 清单计算变异分数（killed/(total-equivalent)），低于阈值时产出阻断信号，衡量测试套件「杀死缺陷」的真实能力。真实变异注入须接专业工具。触发词：
  "变异测试", "mutation testing", "变异分数", "测试充分性", or after qa-test-case-gen/qa-api-runner.
  英文触发词（English triggers）：mutation testing, mutation score, test adequacy.
license: MIT
compatibility: "WorkBuddy / Claude / 通用 Agent（零依赖标准库）"

metadata:
  version: "1.0.0"
  category: traditional
  stage: cross_cutting
  tier: 1
---
# qa-mutation — 变异测试分数

覆盖率只回答「代码跑到了没」，变异分数回答「**跑到了之后，测试能不能抓出被故意改坏的版本**」。

> ⚠️ **治理门禁 · 不执行外部工具**：本技能仅消费变异工具（mutmut/cosmic-ray/pit）**已有产出**、计算并门禁变异分数，**不注入变异体、不执行测试套件**；真实变异注入须接专业工具。
变异工具（mutmut / cosmic-ray / pit 等）会注入微小改动（变异体 mutant），若测试套件未能让某个
变异体失败（即「存活 survived」），说明该处行为没有被有效断言覆盖。

> 变异分数是测试套件「杀伤力」的黄金指标。覆盖率 100% 但变异分数低，等于「走过场」。

## 输入约定

`--mutants` 指向一个 mutants 清单（JSON），每个变异体形如：

```json
[
  {"id": "M1", "file": "calc.py", "line": 12, "operator": "RC", "status": "killed"},
  {"id": "M2", "file": "calc.py", "line": 18, "operator": "AOR", "status": "survived"},
  {"id": "M3", "file": "calc.py", "line": 20, "operator": "AOR", "status": "timeout"},
  {"id": "M4", "file": "calc.py", "line": 25, "operator": "LCR", "status": "equivalent"}
]
```

- `status` 取值：`killed`（被测试抓出）/ `survived`（存活，测试未察觉）/ `timeout`（超时，按已杀死计）/
  `equivalent`（等价变异，不计入分母）。
- 兼容旧式布尔字段：存在 `killed: true/false` 时，映射为 `killed` / `survived`。

## 操作流程

```bash
python scripts/mutation_score.py --mutants mutants.json --out mutation_report.md \
       --signals-dir signals --threshold 0.8 [--fail-on]
```

- 变异分数 = (killed + timeout) / (total − equivalent)。
- 分数 ≥ `--threshold`（默认 0.8）→ 放行；低于 → 产出 `mutation_score_low` **阻断信号**。
- `--fail-on` 时同时 `sys.exit(1)`，便于直接在 CI 步骤中断。

## 与上下游衔接

- 输入：变异工具产出（或由 `qa-api-runner` / `qa-ui-automation` 执行结果派生）。
- 输出：变异报告 + 信号 → 接入 `qa-release-check` 门禁；作为测试充分性的横切质量门。

## 能力边界（诚实标注）

- 本技能**只做分数聚合与门禁判定**，不负责注入变异体（那由 mutmut/cosmic-ray 等专业工具完成）。
- 等价变异（equivalent）依赖工具标注，未标注则计入分母；建议上游工具启用等价性分析以减少误判。

## 参考资料

- 检查项、阈值、CLI 用法与常见坑：见 [`references/guide.md`](references/guide.md)。
