---

name: qa-test-data
description: |-
  当用户需要为执行或自动化准备测试数据时使用——边界值 / 等价类取值、异常输入、
  批量造数，或对敏感字段做 PII 脱敏。本技能按字段规格生成 CSV/JSON 数据，并对标注
  字段自动打码，避免真实个人信息进入测试库。触发词："造测试数据"、"生成边界值"、
  "测试数据脱敏"、"批量造数"，或当用例在执行前需要填充输入数据时使用。
  英文触发词（English triggers）：test data, data generation, PII masking.
license: MIT
compatibility: "WorkBuddy / Claude / 通用 Agent（零依赖标准库）"

metadata:
  version: "1.0.0"
  category: traditional
  stage: 04-testdata
  tier: 1
---
# qa-test-data — 测试数据生成

手工造数慢、边界易漏、还容易把真实个人信息带进测试库。本技能按字段规格生成
**边界/等价/随机**数据，并对标注字段**脱敏**，输出 CSV/JSON 直接用于执行或自动化。

## 何时使用

- 用例需要输入数据（尤其边界、异常值）。
- 用户说「造测试数据」「生成边界值」「测试数据脱敏」「批量造数」。
- 接口/UI 自动化前置需要一批账号/订单等基础数据。

## 操作流程

### 步骤 1 — 编写数据规格

按 `references/data-spec.md`，描述字段类型与边界，标注需脱敏字段。
参考 `references/example-spec.json`。

### 步骤 2 — 生成

```bash
python scripts/gen_data.py --input spec.json --outdir <变更>/04-testdata --format csv
```
- 整型字段：自动产出 `min / max / min-1 / max+1 / 0` 边界。
- 字符串字段：空 / 最小长 / 最大长 / 超长。
- phone/email/enum：按规格随机若干条（`seed` 可复现）。
- `pii_mask` 中的字段：自动脱敏（首尾保留、中间打码）。

### 步骤 3 — 使用与落盘

产物 `testdata.csv` / `testdata.json` 落入 `04-testdata/`，供 `qa-api-runner`、
`qa-ui-automation` 或手工执行消费。

## 注意
- 脱敏仅防明文泄露，测试库仍应遵循最小权限；敏感系统勿用生产数据。
- 随机数据用 `seed` 固定，保证回归可复现。
- 枚举/业务约束（如手机号格式）建议用 `type:"enum"` 或具体生成器，避免无效数据。

## 与上下游衔接
- 上游：`qa-test-analysis` 测试点里的边界/异常维度 → 转成本技能规格。
- 下游：数据喂给 `qa-api-runner`（接口）、`qa-ui-automation`（UI）、`qa-perf-*`（性能铺底数据）。
