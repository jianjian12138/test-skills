---

name: qa-bug-verify
description: |-
  在缺陷（来自 qa-bug-report）修复之后使用，规划并执行验证与回归。本技能生成验证
  计划：按原复现步骤重跑、逐条核对验收标准，并根据缺陷影响的模块 / 代码推导关联
  回归范围。触发词："缺陷验证"、"验证bug"、"回归测试"、"bug回归"，或在 qa-bug-report
  的缺陷单转为已修复 / 待验证之后使用。
  英文触发词（English triggers）：bug verification, regression test, defect verify.
license: MIT
compatibility: "WorkBuddy / Claude / 通用 Agent（零依赖标准库）"

metadata:
  version: "1.0.0"
  category: traditional
  stage: 07-report
  tier: 1
---
# qa-bug-verify — 缺陷验证与回归

开发修复后，不只「再点一遍」。本技能生成**验证 + 回归计划**：
1. 验证：按原复现步骤重跑，确认修复且未引入新问题；
2. 回归：根据缺陷影响的模块 / 代码，推导关联回归范围，防止改坏别处。

> 修 bug 最怕「修一个爆三个」。验证看修复，回归看波及面。

## 何时使用

- 缺陷单状态变为「已修复 / 待验证」。
- 用户说「缺陷验证」「验证bug」「回归测试」「bug 回归」。

## 操作流程

### 步骤 1 — 填验证输入

把 `qa-bug-report` 的缺陷 + 修复信息归一化（`references/verify-schema.md`）：

```json
{"bug_id":"BUG-101","title":"下单提交无响应","module":"下单",
 "fix_version":"v2.0.1","affected_modules":["下单","购物车"],
 "steps":["打开下单页","点提交"],"acceptance":["订单创建成功","无报错"],
 "risk":"高"}
```

### 步骤 2 — 生成验证 + 回归计划

```bash
python scripts/gen_verify_plan.py --bug bug_fixed.json --out verify_plan.md
```

产出 `verify_plan.md`：
- **验证清单**：逐条原步骤 + 验收标准（通过/失败勾选）。
- **回归范围**：受影响模块 + 推导出的关联用例（按风险定深度）。
- **准入结论模板**：验证全过 + 回归无新增失败 → 可关闭。

### 步骤 3 — 执行与闭环

按计划在对应环境执行；全过则关闭缺陷，否则打回 `qa-bug-report` 复提。

## 回归深度策略

| 风险 | 回归范围 |
| --- | --- |
| 高 | 受影响模块全量 + 相邻模块冒烟 |
| 中 | 受影响模块核心路径 + 接口回归 |
| 低 | 受影响模块冒烟 |

## 与上下游衔接

- 输入：`qa-bug-report` 缺陷、`qa-api-runner` 等可复用用例。
- 输出：验证结论 → 缺陷关闭 / 打回；关联 `qa-release-check` 上线门禁。
