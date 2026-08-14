---

name: qa-flaky-detect
description: |-
  不稳定测试（flaky）检测技能：基于同一测试集的多轮重跑结果，识别「时过时不过」的 flaky 用例，
  计算 flaky 率与重跑建议，超阈值时产出阻断信号。解决「CI 偶发红但本地复现不了」的隐形成本。触发词：
  "flaky", "不稳定测试", "偶发失败", "重跑", "测试抖动", or after qa-api-runner/qa-ui-automation.
  英文触发词（English triggers）：flaky test, test stability, nondeterministic.
license: MIT
compatibility: "WorkBuddy / Claude / 通用 Agent（零依赖标准库）"

metadata:
  version: "1.0.0"
  category: traditional
  stage: cross_cutting
  tier: 1
---
# qa-flaky-detect — 不稳定测试检测

Flaky 测试是自动化套件的「隐性毒药」：它在不改代码时也随机失败，久而久之团队会习惯性忽略红灯，
真实回归被掩盖。本技能通过**多轮重跑**的数据，客观识别 flaky 用例。

> ⚠️ **治理门禁 · 不执行外部工具**：本技能仅基于你提供的多轮重跑结果（JSON）做 flaky 统计与门禁判定，**不自行触发重跑、不调用 CI/测试框架**；真实重跑由你的流水线执行。

> 一条 flaky 测试的成本 = 每次失败的排查时间 × 发生频率。及早定位比反复重跑更划算。

## 输入约定

`--runs` 指向多轮重跑结果（JSON），支持两种结构：

```json
{ "runs": [ {"run_id":"r1","results":{"t_login":true,"t_pay":false}},
            {"run_id":"r2","results":{"t_login":true,"t_pay":true}} ] }
```
或扁平结构：
```json
{ "results": [ {"test":"t_login","run":1,"passed":true},
               {"test":"t_login","run":2,"passed":true},
               {"test":"t_pay","run":1,"passed":false},
               {"test":"t_pay","run":2,"passed":true} ] }
```
`true`/`passed:true` 表示通过，否则失败。

## 操作流程

```bash
python scripts/detect_flaky.py --runs runs.json --out flaky_report.md \
       --signals-dir signals --threshold 0.05 [--fail-on]
```

判定逻辑：
- 某用例在 N 轮中**既有通过又有失败** → 标记为 flaky。
- 某用例 N 轮**全部失败** → 标记为「稳定失败（stable-fail）」，与 flaky 区分（需修 bug 而非重跑）。
- `flaky 率 = flaky 用例数 / 总用例数`。
- flaky 率 > `--threshold`（默认 0.05）→ 产出 `flaky_detected` **阻断信号**；
  存在 flaky 但未超阈值 → 产出 `warn` 级非阻断信号，附重跑建议。

## 与上下游衔接

- 输入：CI 多轮重跑记录（或由 `qa-api-runner` / `qa-ui-automation` 多次执行结果汇总）。
- 输出：flaky 报告 + 信号 → 接入 `qa-release-check` 门禁；作为测试稳定性的横切质量门。

## 能力边界（诚实标注）

- 本技能**只做统计判定与门禁**，不自动重跑测试（重跑由 CI 编排执行）。
- 判定依赖足够的重跑轮数：`--min-runs`（默认 2）以下轮数不足以判定 flaky，会给出「样本不足」提示。

## 参考资料

- 检查项、阈值、CLI 用法与常见坑：见 [`references/guide.md`](references/guide.md)。
