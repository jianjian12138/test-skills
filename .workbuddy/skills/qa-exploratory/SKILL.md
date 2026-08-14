---

name: qa-exploratory
description: |-
  探索性测试引导技能：把功能 / 风险点转化为一组结构化测试章程（charter），并给出 HTSM
  启发式、常用 Tour、缺陷苗头信号与 note-taking 模板。用于需求模糊、时间紧、补充脚本化
  测试盲区。触发词： "探索性测试", "exploratory", "章程", "charter", "随机测试",
  or after qa-test-analysis.
  英文触发词（English triggers）：exploratory testing, charter, session-based.
license: MIT
compatibility: "WorkBuddy / Claude / 通用 Agent（零依赖标准库）"

metadata:
  version: "1.0.0"
  category: traditional
  stage: 06-execution
  tier: 1
---
# qa-exploratory — 探索性测试引导

探索性测试 = **边学、边设计、边执行、边记录**的同步过程。它不是「随机乱点」，而是
有章程（charter）、有策略（heuristics/tour）、有停手条件（stop condition）的测试。

> 脚本化测试保证「该测的都测了」；探索性测试负责「没想到要测的也被发现了」。

## 何时使用

- 需求模糊 / 文档不全，无法一次性写出完整用例。
- 时间紧，需要快速覆盖核心风险。
- 补充脚本化测试的盲区（异常交互、边界组合、用户体验）。
- 与 `qa-test-analysis` 衔接：分析出的风险点 → 直接喂给本技能生成章程。

## 操作流程

### 步骤 1 — 收集输入

- 功能列表（模块 / 页面 / 接口）。
- 风险点（来自 `qa-test-analysis` 的风险矩阵、或团队已知脆弱点）。

### 步骤 2 — 生成章程

```bash
python scripts/gen_charters.py --input features.json --out charters.md
# 或极简：
python scripts/gen_charters.py --features "订单导出,优惠券核销" \
    --risks "大数据量超时;权限越界" --timebox 90 --out charters.md
```

`features.json` 示例：
```json
{
  "session_timebox_min": 90,
  "features": [
    {"name": "订单导出", "risks": ["大数据量超时", "权限越界"]},
    {"name": "优惠券核销", "risks": []}
  ]
}
```

`charters.md` 含：每个功能一组章程，含 **目标 / 区域 / 方法(Tour) / 风险点 / 停止条件 / 时间盒**。

### 步骤 3 — 执行与记录

- 用 `references/heuristics.md` 的 Tour 与缺陷苗头信号边测边记。
- 用 note-taking 模板（见 heuristics.md）沉淀发现。
- 发现的 bug 转 `qa-bug-report`；需要回归的转 `qa-bug-verify`。

## 与上下游衔接

- 输入：`qa-test-analysis` 风险矩阵、需求/NFR。
- 输出：章程 → 执行 → 缺陷（`qa-bug-report`）/ 用例补充（`qa-test-case-gen`）。
- 兼容性：需多设备/浏览器覆盖时，结合 `qa-compat-matrix`。
