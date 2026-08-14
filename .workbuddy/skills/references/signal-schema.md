# 质量信号契约（Quality Signal Contract）

> 跨技能的统一质量产物格式。任何质量类技能在产出结果时，**同时**在变更工作区的
> `signals/<skill-name>.json` 写入结构化信号。发布门禁（`qa-release-check`）只扫描
> `signals/` 目录聚合所有 `blocking=true` 的信号，任一 blocking → 禁止发布 + `sys.exit(1)`。
>
> **收益**：此后新增任何质量维度（契约 / 风险 / 移动 / 安全 / 性能 / UI / 缺陷），**门禁零代码改动**。
> 根治「能力孤岛 / 假绿门禁复发」问题（复审 P0-1 / P1-6 违反 OCP）。

## 文件位置
- 每个技能写入：**`<change_dir>/signals/<skill-name>.json`**
- `skill-name` 必须与 `REGISTRY.json` / `stages.json` 中的技能名一致（如 `qa-api-contract`）。

## JSON 结构（SSOT = `scripts/_common.py:emit_signal`）

> **唯一事实源（SSOT）**：字段结构由 vendored `scripts/_common.py` 的 `emit_signal()` 决定
> （每个带脚本的方法学技能自包含一份、字节一致，`check_drift.py` 校验）。本文件与
> `references/signal-schema.json` 均为其派生文档；若不一致**以代码为准**。

### 顶层文档对象
```json
{
  "source": "qa-api-contract",
  "generated_at": "2026-08-09T17:30:00",
  "schema_version": "1.0",
  "signals": [ /* 见下 */ ]
}
```

| 字段 | 类型 | 必需 | 说明 |
|---|---|---|---|
| source | string | 是 | 技能名，须与 REGISTRY/stages 一致 |
| generated_at | string(ISO8601) | 是 | 产出时间；门禁据此判新鲜度（默认 24h 窗口） |
| schema_version | string | 是 | 契约版本，当前 `"1.0"` |
| signals | array | 是 | 信号对象数组（可为空 → `emit_signal` 不写文件，见约定 3） |

### 信号对象（数组元素）
```json
{
  "signal": "breaking_change",   // 必需：信号类型，snake_case，全局唯一可读
  "severity": "critical",        // 必需：critical | high | medium | low | info
  "count": 2,                    // 必需：该类信号命中数量
  "blocking": true,              // 必需：true=阻断发布；false=仅记录告警
  "detail_ref": "signals/qa-api-contract.detail.md",  // 可选：详情报告路径
  "verdict": "no_findings",      // 可选：干净运行结论（如 a11y_verified / unit_health_verified）
  "rules": ["A-CONTRAST"]        // 可选：命中的规则标签列表（如 a11y 对比度规则）
}
```

| 信号字段 | 类型 | 必需 | 说明 |
|---|---|---|---|
| signal | string | 是 | 信号类型标识 |
| severity | enum | 是 | `critical` / `high` / `medium` / `low` / `info`（**仅信息性分级**，供排序与告警；**不参与门禁判定**） |
| count | integer | 是 | 命中数量（≥0） |
| blocking | boolean | 是 | 是否阻断发布 |
| detail_ref | string | 否 | 详情报告相对路径 |
| verdict | string | 否 | 干净/验证结论（RK-02 修复后，干净运行亦产出非阻断 verified 信号，如 `no_findings` / `passed`） |
| rules | array\<string\> | 否 | 命中规则标签（如 `A-CONTRAST`、`XPATH`、`SLA`） |

## 约定
1. 一个文件可含多个 signal 对象；同一技能可多次运行覆盖写同一文件。
2. **`blocking` 是门禁的唯一阻断权威**：任一 `blocking=true` 的信号即阻断发布，**无论 `severity` 取值**（含 `medium`/`low`）。`severity` 仅作信息性分级（排序/告警），绝不参与门禁判定（对接 `gen_release_checklist.py:collect_blocking` 仅取 `blocking`）。
3. `signals` 为空 → `emit_signal` **不写文件**（视为「无质量信号」）；门禁提示「未提供质量信号」但不阻断。
4. 各技能在写 signals 的同时，仍保留原有人类可读报告（如 `contract_report.md`）。
5. **门禁（默认 fail-closed）**：`DEFAULT_REQUIRED` 来源须产出 verified（非阻断）信号才算「跑了且过」，缺失来源 → 阻断（须 `--skip-required` 显式人工覆盖并审计）。

## 校验
- `check_drift.py` 校验 5 份 vendored `_common.py` **字节一致且含 `schema_version`**（R-24/S-03）。
- `references/signal-schema.json` 为机器可读 JSON Schema（`severity` 枚举 + `blocking` 必需字段 + **`blocking=true → severity` 的 if-then 语义约束**），供消费方静态校验。
- `check_drift.py` **规则 13b（P1-5）**：校验 `signal-schema.json` 确实含 `blocking→severity` 语义约束（防契约被弱化）；若仓库内存在 `signals/*.json`，其每条 `blocking=true` 信号须声明有效 `severity`，否则报漂移。
