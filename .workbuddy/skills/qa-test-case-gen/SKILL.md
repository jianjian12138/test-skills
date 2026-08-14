---

name: qa-test-case-gen
description: |-
  当用户已有测试点（来自 qa-test-analysis）或需求，希望直接产出可执行的用例文件、
  免去人工调格式时使用。本技能用确定性脚本把结构化用例 JSON 直接生成标准化的
  Excel（.xlsx）与 Xmind（.xmind），列名与层级统一、开箱即用。触发词："生成测试用例"、
  "导出 Excel 用例"、"导出 Xmind 用例"、"把测试点写成用例"，或在 qa-test-analysis
  产出之后使用。
  英文触发词（English triggers）：test case generation, Excel cases, Xmind.
license: MIT
runtime_dependencies: openpyxl
compatibility: "WorkBuddy / Claude / 通用 Agent（编排层零依赖；执行层 openpyxl 运行期依赖，见 runtime_dependencies）"

metadata:
  version: "1.0.0"
  category: traditional
  stage: 03-cases
  tier: 1
---
# qa-test-case-gen — 用例格式化直出（Excel / Xmind）

用例格式转换（CSV→Excel、MD→Xmind）是典型的时间黑洞。本技能用**确定性脚本**
把结构化用例 JSON 直接落盘为标准化 Excel 与 Xmind，无需二次调整。

> ⚠️ **能力边界（S-01 命名澄清）**：本技能是**用例格式化直出**工具，**不是**「AI 测试用例生成器」。
> 它只负责把**已存在的结构化用例 JSON** 转成 Excel/Xmind，**不发明测试思路、不分析需求**。
> 测试思路 / 测试点来自上游 `qa-test-analysis`（需求 → 测试点），本技能仅承接其产物。
> 若期望「给需求直接出用例」，应先跑 `qa-test-analysis` 产出 `testpoints.md`，再用本技能格式化。

## 何时使用

- 已有 `testpoints.md`（来自 `qa-test-analysis`）或等价测试点。
- 用户说「生成用例」「导出 Excel/Xmind 用例」「测试点写成用例」。

## 操作流程

### 步骤 1 — 整理为用例 JSON

把测试点转化为 `references/cases-schema.md` 定义的 JSON（也可直接基于需求写）。
字段：编号、模块、名称、类型、优先级、前置、步骤（数组）、预期。
**质量把关**：每个用例步骤必须可达预期结果；优先级遵循 P0–P3；高风险项用例更密。

### 步骤 2 — 生成文件

运行内置脚本（混合深度：确定性产出交由脚本，保证格式稳定）：

```bash
python scripts/gen_case.py --input cases.json --outdir <变更目录>/03-cases --name <模块>用例
```

- 默认同时产出 `<name>.xlsx` 与 `<name>.xmind`。
- 仅 Excel：`--excel-only`；仅 Xmind：`--xmind-only`。

### 步骤 3 — 校验与交付

- Excel 列：用例编号 / 模块 / 用例名称 / 类型 / 优先级 / 前置条件 / 测试步骤 /
  预期结果 / 实际结果 / 状态（后两列留空供执行填写）。
- Xmind 层级：根 → 模块 → 用例（含类型/优先级/前置/步骤/预期的备注）。
- 提示用户：自动生成用例建议人工复核参数合理性与场景完整性，再进入执行。

## 深化能力（V2）

- 用例自动扩充：`scripts/expand_cases.py` 基于字段定义生成边界/异常用例并去重
  （见 `references/checklist.md` 的「用例自动扩充方向」）。
- 测试清单与常见坑见 `references/checklist.md`。

## 高质量用例纪律（W2 / W7 增强）

### 三级推导（功能点 → 测试点 → 测试用例）
承接 `qa-test-analysis` 的三级推导模型，明确本技能在第三级的角色：
- **L1 功能点**：来自 `qa-req-spec` 的需求条目（"要做什么"）。
- **L2 测试点**：来自 `qa-test-analysis` 的 `testpoints.md`（"验证什么"，介于需求与用例之间，去重/归并可复用）。
- **L3 测试用例**：本技能产出（"怎么验"，含步骤、预期、优先级，落 Excel/Xmind）。
L2 是采纳率关键——先把「验证什么」想清楚再写步骤，可把用例采纳率从 60–70% 提升到 90%+（对标 AliExpress 实践）。

### 三级推导追溯矩阵（脚本化审计，R-07）
为让 L1→L2→L3 推导**可审计、可闭环**，本技能提供 `scripts/trace_matrix.py`：从工作区抽取
`requirement.md`（需求 `REQ-<id>`）、`testpoints.md`（测试点 `TP-<id>`，段内提及 `REQ-` 即溯源需求）、
`cases.json`（用例 `TC-<id>`，`cases[].covers` 即归属测试点），输出 **case→testpoint→req** 矩阵 Markdown/JSON
并报告断链（`--fail-on-gaps` 可 fail-closed）。上游逐步采纳 `REQ-/TP-/covers` 约定后，矩阵即自动闭合；
未采纳时工具如实标注断链，不伪造完整链路。

### 步骤对照表（防"11 步只实现 3 步"，W2）
当用例用于自动化（`qa-ui-automation` / `qa-api-runner`）时，生成后**必须产出「用例步骤 ↔ 代码实现」逐条对照表**：
每个用例步骤对应一行实现（函数/接口/选择器），缺失对应实现的步骤标红。
禁止「步骤全写但代码只实现部分」——对照表随用例一并交付，作为执行完整性自查。

### 调试三轮制（自动化落地，W2）
UI/接口自动化落地采用三轮收敛，避免一次性全量跑浪费：
- **第 1 轮**：跑 3–5 条关键路径用例（核心流程 + 1 条边界）。
- **第 2 轮**：仅重跑第 1 轮失败项 + 同类扩展。
- **第 3 轮**：全量回归。
- **超 3 轮仍未稳定**：标记「待人工」，不强行刷绿，记录阻塞原因。

## 依赖

- Excel 生成需 `openpyxl`：`pip install openpyxl`。
- Xmind 生成纯标准库（zip + json），无额外依赖。

## 与下游衔接

- 功能用例 → 人工/自动化执行，结果回填 Excel → `qa-report` 读取出报告。
- 接口相关用例 → 转入 `qa-api-doc` + `qa-api-runner` 做自动化执行。

## 阶段产物契约（stages.json artifacts）

本阶段主技能须产出的文件名（与 `qa-orchestrator/stages.json` 契约一致）：

- cases.xlsx
- cases.xmind
- cases.json
