---

name: qa-test-strategy
description: |-
  在项目 / 版本测试启动时使用，产出测试计划 / 测试策略：测试范围、目标、测试类型
  覆盖（UI/API/性能/安全）、进度安排、准入准出标准与风险应对。触发词："测试计划"、
  "测试策略"、"测试方案"、"测试规划"，或在 qa-req-spec 启动一轮变更之前使用。
  英文触发词（English triggers）：test strategy, test plan, test coverage.
license: MIT
compatibility: "WorkBuddy / Claude / 通用 Agent（零依赖标准库）"

metadata:
  version: "1.0.0"
  category: traditional
  stage: cross_cutting
  tier: 1
---
# qa-test-strategy — 测试计划 / 策略

在项目/版本启动时，先有**测试策略**再动手：范围、目标、测试类型覆盖、
进度、准入准出、风险。它是后续 `qa-req-spec` / `qa-test-analysis` 的总纲。

> 没策略就开测，容易漏类型、缺准出、进度失控。策略是测试的合同。

## 何时使用

- 新项目 / 新版本启动，需要测试规划。
- 用户说「测试计划」「测试策略」「测试方案」「测试规划」。

## 操作流程

### 步骤 1 — 填策略输入

```json
{"project":"订单中台","version":"v2.0","scope":"下单/支付/退款",
 "objectives":["核心链路零P0","性能达标"],"types":["ui","api","perf","security"],
 "schedule":"2周","entry":["需求冻结","环境就绪"],"exit":["用例执行率100%","无P0遗留"],
 "risks":["支付依赖第三方不稳定"]}
```

### 步骤 2 — 生成

```bash
python scripts/gen_strategy.py --strategy strategy.json --out test_strategy.md
```

产出 `test_strategy.md`：项目概述、测试范围、目标、各类型测试策略、
进度、准入准出、风险与应对。

### 步骤 3 — 衔接

策略定好后，进入 `qa-req-spec` 做需求结构化，再逐层设计。

## 与上下游衔接

- 上游：项目启动 / 版本规划。
- 下游：总纲驱动 `qa-req-spec`、`qa-test-analysis`、`qa-execution`、各专项技能。

## 参考资料

- 检查项、阈值、CLI 用法与常见坑：见 [`references/guide.md`](references/guide.md)。
