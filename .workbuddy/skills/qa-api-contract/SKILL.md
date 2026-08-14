---

name: qa-api-contract
description: |-
  接口契约测试技能：对比新旧两份 OpenAPI 规范，自动识别破坏性变更（Breaking Change）并卡 CI。
  内置 35 条规则（27 BREAKING / 8 WARN），覆盖端点、参数、请求体、响应、组合类型、安全方案、服务器与弃用 8 个维度。触发词：
  "契约测试", "接口契约", "API 破坏性变更", "OpenAPI diff", "接口兼容性", or after qa-api-doc.
  英文触发词（English triggers）：API contract, OpenAPI, contract testing, breaking change.
license: MIT
compatibility: "WorkBuddy / Claude / 通用 Agent（零依赖标准库）"

metadata:
  version: "1.0.0"
  category: traditional
  stage: 06-execution
  tier: 1
---
# qa-api-contract — 接口契约测试

接口契约的本质是**「消费者依赖的约定不能被悄悄打破」**。本技能对比上线前/后的
OpenAPI 规范，识别破坏性变更，并在 CI 中拦截，避免「本地能跑、一上线就崩」。

> 破坏性变更一旦合入，所有依赖该字段/端点的调用方都会失败。契约测试就是这道闸门。

## 能力边界（诚实标注）

- **覆盖 35 条规则**（27 BREAKING / 8 WARN），跨端点、参数、请求体、响应、组合类型、
  安全方案、服务器与弃用 8 个维度（规则全量见 `scripts/contract_diff.py` 的 `RULES` 常量，
  且 `tests/run_all_tests.py::t_contract_rules` 已实测 35/35 全部可被触发、自比对零误报）。
- **盲区（已知限制）**：跨文件 `$ref`、以及无法解析的**外部 `$ref`**（如远程 URL）不做深入
  比对，仅以 WARN（R35）提示存在盲区。同一文件内 `$ref` 可解析。若契约大量依赖外部引用，
  需先内联后再比对。
- 仅接受 **OpenAPI 3.x 的 JSON** 形式；YAML 需先转 JSON。保持零外部依赖。

## 操作流程

### 步骤 1 — 准备两份规范

```json
# old.json / new.json 均为 OpenAPI 3.x 的 JSON 形式
{ "openapi": "3.0.3", "paths": { "/orders": { "get": {...}, "post": {...} } }, ... }
```

### 步骤 2 — 比对并判定

```bash
python scripts/contract_diff.py --old old.json --new new.json --out contract_report.md \
       --signals-dir signals [--fail-on]
```

破坏性变更（27 条 BREAKING 中任意命中即阻断，举要）：
- 端点/操作删除（R01/R02）；必填参数删除或变必填（R03/R05）
- 参数位置/类型/format 收窄/枚举删除（R06–R09）；新增必填参数或请求体必填属性（R10/R12）
- 请求体属性类型/约束收紧、additionalProperties 由 true 收紧（R14/R17/R18）
- 响应字段删除/类型变更/必填变可选、2xx 状态码删除、响应 header 删除（R20–R24）
- nullable 由 true 收紧（R26）、oneOf/anyOf 分支删除（R27）
- 安全方案新增/类型变更、OAuth scope 新增（R29/R30/R31）

非破坏性告警（8 条 WARN，不阻断）示例：可选参数删除（R04）、响应枚举新增（R25）、
安全方案删除（R32）、servers 变更（R33）、deprecated 标记（R34）、外部 `$ref` 盲区（R35）。

### 步骤 3 — 处置

- 有 BREAKING → 报告标红、写入 `signals/qa-api-contract.json` 的 `breaking_change` 阻断信号、
  `--fail-on` 时 `sys.exit(1)`，由 `qa-release-check` 门禁拦截发布。
- 仅 WARN/无差异 → 放行。

## 与上下游衔接

- 输入：`qa-api-doc` 产出的 OpenAPI（或仓库内规范文件）。
- 输出：契约报告 + 信号 → 接入 `qa-ci` / `qa-release-check` 门禁。

## 参考资料

- 检查项、阈值、CLI 用法与常见坑：见 [`references/guide.md`](references/guide.md)。
