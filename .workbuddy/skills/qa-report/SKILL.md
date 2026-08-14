---

name: qa-report
description: |-
  当测试执行完成（功能用例已在 Excel 填好执行结果，和/或已有 qa-api-runner 的接口
  自动化 results.json），用户需要一份汇总测试报告时使用。报告自动统计通过率、
  各模块分布、缺陷与阻塞分布，并给出质量评估与上线建议。触发词："生成测试报告"、
  "出报告"、"统计通过率"、"测试总结"，或在测试执行完成之后使用。
  英文触发词（English triggers）：test report, pass rate, test summary.
license: MIT
runtime_dependencies: openpyxl
compatibility: "WorkBuddy / Claude / 通用 Agent（编排层零依赖；执行层 openpyxl 运行期依赖，见 runtime_dependencies）"

metadata:
  version: "1.0.0"
  category: traditional
  stage: 07-report
  tier: 1
---
# qa-report — 测试报告汇总

执行结果散落在 Excel 与各类工具里，手工统计既慢又易错。本技能**读表出报告**：
从用例执行表（状态列）与接口自动化结果（results.json）自动汇总通过率、模块分布、
缺陷分布与质量评估。

## 何时使用

- 功能用例已在 Excel 填好执行结果（通过/失败/阻塞）。
- `qa-api-runner` 已产出 `results.json`。
- 用户说「生成测试报告」「出报告」「统计通过率」「测试总结」。

## 操作流程

### 步骤 1 — 收集结果文件

- 功能用例：`03-cases/cases.xlsx`（需含「状态」或「实际结果」列）。
- 接口自动化：`06-execution/results.json`。

### 步骤 2 — 生成报告

```bash
python scripts/parse_results.py \
    --excel <变更>/03-cases/cases.xlsx \
    --json <变更>/06-execution/results.json \
    --title "<变更名>" --outdir <变更>/07-report
```

- 仅功能：`--excel` 即可；仅接口：`--json` 即可。
- 产出 `<变更>/07-report/test-report.md`。

### 步骤 3 — 报告内容

报告自动包含：
- 总数 / 已执行 / 通过 / 失败 / 阻塞 / 未执行 / **通过率**。
- 各模块通过率分布表。
- 缺陷 / 阻塞分布（失败最多模块优先排查）。
- 质量评估与上线建议（按通过率与阻塞自动分级）。

## 深化能力（V2）

- 多轮趋势对比：`scripts/trend_compare.py` 由多轮汇总 CSV 生成通过率 / 缺陷收敛趋势
  与发布结论（go / no-go）。
- 测试清单与常见坑见 `references/checklist.md`。

## 状态归一

脚本自动归一常见写法：通过/pass、失败/不通过/fail、阻塞/block 等，避免手工对齐。

## 与上下游衔接

- 上游：`qa-test-case-gen`（用例）、`qa-api-runner`（接口执行）。
- 下游：失败用例转 `qa-bug-report`（Phase 4）提交缺陷；评估报告结论驱动
  `qa-release-check`（Phase 4）上线验证决策。

## 阶段产物契约（stages.json artifacts）

本阶段主技能须产出的文件名（与 `qa-orchestrator/stages.json` 契约一致）：

- test-report.md
- test-report.json
- bug_report.json
