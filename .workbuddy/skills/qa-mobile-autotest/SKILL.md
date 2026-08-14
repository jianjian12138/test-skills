---

name: qa-mobile-autotest
description: |-
  移动端 App 自动化测试技能：把「摸清现状→列清单→生成资产→自检→中文交付」整成标准流水线。
  含八步交付闭环、定位金字塔（accessibility id 优先，XPath 兜底）、五维质量 rubric
  （可运行性/定位健壮性/可维护性/稳定性/覆盖透明度，<70 必须补全）、fault-diagnosis 决策树。
  触发词： "移动端测试", "APP 自动化", "Appium", "移动测试技能", "手机兼容性", or after qa-test-analysis.
  英文触发词（English triggers）：mobile testing, Appium, mobile automation.
license: MIT
compatibility: "WorkBuddy / Claude / 通用 Agent（零依赖标准库）"

metadata:
  version: "1.0.0"
  category: traditional
  stage: 06-execution
  tier: 1
---
# qa-mobile-autotest — 移动端 App 自动化测试

移动端测试的真实困境不是「会不会写脚本」，而是**有没有可长期维护的测试工程**：用例条数不少，
却没人说得清覆盖了哪些业务流程，Android/iOS 各写一套，失败全靠猜。

本技能把「先摸底 → 再清单 → 再分层 → 再门禁」打包成 AI 能稳定执行的流程，产出
**可复查、可交接、可扩展** 的 mobile-tests 工程，而非一次性脚本。

## 三层架构

- **协作层**：本 SKILL.md 定义八步流程与完成标准。
- **脚本层**：`scaffold_manifest.py`（清单先行）、`check_env.py`（环境体检）、`quality_rubric.py`（五维打分）、`fault_diagnosis.py`（决策树）。
- **产物层**：`app-test-manifest.json` + `mobile-tests/` + 中文交付摘要。

## 八步交付闭环

1. 摸底环境（模拟器 / USB 真机 / 云网格）
2. 环境体检 `check_env.py`
3. 列清单（灵魂步骤）`scaffold_manifest.py` → screens[] / flows[] / risks[]
4. 生成 Screen / Flow 测试资产
5. 生成跨端定位（定位金字塔）
6. 运行 + 失败截图
7. 质量自检 `quality_rubric.py`
8. 中文交付摘要（<70 必须补全）

## 定位金字塔（告别 XPath 地狱）

```
L1 accessibility id  (跨端首选，推动开发加 testID)
L2 resource-id / name
L3 iOS predicate / class chain
L4 Android UiAutomator
L5 XPath 仅兜底，须注释原因
```

禁止 `Thread.sleep` 与写死坐标；失败先走 `fault_diagnosis.py` 决策树，一次只改一个变量。

## 五维质量 rubric（满分 100，<70 必须补全）

| 维度 | 权重 | 看什么 |
|---|---:|---|
| 可运行性 | 25 | 起服务即可跑通 P0 |
| 定位健壮性 | 25 | P0 无裸 XPath |
| 可维护性 | 20 | Screen/Flow 分层 |
| 稳定性 | 15 | 无 sleep，失败自动截图 |
| 覆盖透明度 | 15 | 有 manifest，报告标风险 |

## 与上下游衔接

- 输入：`qa-test-analysis` 风险、App 源码/APK/IPA。
- 输出：mobile-tests 工程 → `qa-compat-matrix`（设备矩阵）、`qa-exploratory`（探索性）、`qa-release-check`。
- 详见 `references/mobile-guide.md`。
