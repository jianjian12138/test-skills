---

name: qa-unit-tdd
description: |-
  单元/TDD 方法学健康度评估技能：基于测试金字塔占比、行覆盖率、失败用例、测试/代码比等指标，评估单元测试健康度，
  存在方法学失衡（金字塔倒挂）或覆盖率/失败不达标时产出阻断信号，守住「重 E2E 轻单测」的反模式。触发词：
  "单元测试", "TDD", "测试金字塔", "覆盖率门禁", "单测健康度", "测试占比".
  英文触发词（English triggers）：unit testing, TDD, test pyramid, coverage.
license: MIT
compatibility: "WorkBuddy / Claude / 通用 Agent（零依赖标准库）"

metadata:
  version: "1.0.0"
  category: traditional
  stage: cross_cutting
  tier: 1
---
# qa-unit-tdd — 单元/TDD 方法学健康度门禁

「能跑的 E2E 再多，也补不上单测缺失的底层漏洞」。TDD 与测试金字塔（单元 >> 集成 >> E2E）
是行业公认的性价比之王。本技能把**方法学指标**做成一道可执行门禁：

> ⚠️ **治理门禁 · 不执行外部工具**：本技能仅基于你提供的测试指标 JSON 做方法学健康度评估与门禁判定，**不自行运行测试、不调用覆盖率工具（coverage.py/JaCoCo 等）**；真实覆盖率采集由你的构建流水线执行。

> 覆盖率只是「跑没跑到」；本技能额外看「**单测占比是否健康、测试是否真在写**」——这两点才是方法学底线。

## 输入约定

`--metrics` 指向一份测试指标 JSON：

```json
{
  "unit": 120, "integration": 30, "e2e": 20,
  "line_coverage": 0.85, "branch_coverage": 0.75,
  "failed_tests": 0, "test_loc": 2000, "code_loc": 4000
}
```

| 字段 | 含义 |
| --- | --- |
| `unit` / `integration` / `e2e` | 三类测试的数量（用于金字塔占比） |
| `line_coverage` / `branch_coverage` | 行/分支覆盖率（0~1） |
| `failed_tests` | 当前失败用例数 |
| `test_loc` / `code_loc` | 测试代码行数 / 业务代码行数（测代码比） |

## 操作流程

```bash
python scripts/unit_health.py --metrics metrics.json --out unit_health.md \
       --signals-dir signals [--min-coverage 0.7] [--min-unit-ratio 0.6] [--fail-on]
```

门禁规则：

| 规则 | 级别 | 说明 |
| --- | --- | --- |
| UT-FAIL | critical | 存在失败用例（红着上线 = 门禁失效） |
| UT-PYRAMID | high | 单元测试占比 < `--min-unit-ratio`（默认 60%，金字塔倒挂） |
| UT-COVERAGE | high | 行覆盖率 < `--min-coverage`（默认 70%） |
| UT-TCR | medium | 测试/代码比 < 0.3（测试投入不足） |

- 存在 critical/high → 产出 `unit_health_low` **阻断信号**。
- 趋势分 = 1 − (高危项 / 4 个方法学维度)。
- `--fail-on` 时同时 `sys.exit(1)`。

## 与上下游衔接

- 输入：测试框架/覆盖率工具（pytest + coverage、jest、go test 等）聚合指标。
- 输出：健康度报告 + 信号 → 接入 `qa-release-check` 门禁，作为开发方法学横切门。

## 能力边界（诚实标注）

- 不直接跑测试，只评估**指标**（指标由上游工具产出）。
- 突变存活率本技能不重复计算，建议直接复用 `qa-mutation` 产出后并入门禁。
- 阈值（覆盖率/占比）可按项目成熟度下调，但不建议低于 50%。

## 参考资料

- 检查项、阈值、CLI 用法与常见坑：见 [`references/guide.md`](references/guide.md)。
