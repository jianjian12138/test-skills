---

name: qa-bug-report
description: |-
  当测试发现缺陷、需要产出结构化缺陷单，或需要提交到 TAPD / 禅道 / Jira 时使用。
  本技能把缺陷 JSON 转成标准化的 Markdown 缺陷报告，并生成主流缺陷平台可直接使用的
  字段映射载荷。触发词："提交缺陷"、"提bug"、"缺陷单"、"bug报告"，或在 qa-execution /
  qa-api-runner / qa-perf-analysis / qa-security-report 发现失败之后使用。
  英文触发词（English triggers）：bug report, defect, issue tracker.
license: MIT
compatibility: "WorkBuddy / Claude / 通用 Agent（零依赖标准库）"

metadata:
  version: "1.0.0"
  category: traditional
  stage: 07-report
  tier: 1
---
# qa-bug-report — 缺陷提交（结构化 + 对接平台）

把一次失败转化成一个**规范、可复现、可对接**的缺陷单：
标准字段（标题/模块/类型/严重级/优先级/环境/步骤/期望/实际/证据）+ 给
TAPD / 禅道 / Jira 的字段映射，减少「开发看不懂、复现不了」的扯皮。

> 缺陷质量 = 复现步骤是否清晰 + 严重级是否准确。先定级，再写步骤。

## 何时使用

- 测试发现失败（`qa-execution` 路由来的 api/ui 失败、`qa-security-report` 高危项）。
- 用户说「提交缺陷」「提bug」「缺陷单」「bug 报告」。

## 操作流程

### 步骤 1 — 填缺陷 JSON

按 `references/bug-schema.md` 填：

```json
{"title":"下单页提交后无响应","module":"下单","type":"ui","severity":"S1",
 "priority":"P0","env":"staging","reporter":"张三","assignee":"李四",
 "steps":["打开下单页","填收货地址","点提交"],"expected":"订单创建成功","actual":"按钮转圈后无反应",
 "evidence":"screenshot_01.png"}
```

### 步骤 2 — 生成报告 + 平台载荷

```bash
python scripts/gen_bug.py --bug bug.json --out bug_report.md --tracker tapd
```

产出：
- `bug_report.md`：人读的标准缺陷单。
- 控制台/同目录输出 `<tracker>` 字段映射 JSON（TAPD/禅道/Jira 可直接贴）。

### 步骤 3 — 提交

按 `references/tracker-guide.md` 把映射 JSON 投到对应平台 API / 手工录入。

## 深化能力（V2）

- 严重级判定：`scripts/rate_severity.py` 按「影响 × 可能性」矩阵（含 CWE / EPSS）
  自动给出 S1–S4 与修复优先级建议。
- 测试清单（复现步骤模板 / 附件采集 / 严重级矩阵）见 `references/checklist.md`。

## 字段约定

- **严重级 S1–S4**：S1 致命（核心不可用/数据丢失）、S2 严重、S3 一般、S4 轻微。
- **优先级 P0–P3**：P0 立即修、P1 本迭代、P2 排期、P3  backlog。

## 与上下游衔接

- 输入：`qa-execution` 失败路由、`qa-api-runner` 报错、`qa-perf-analysis` 不达标、`qa-security-report` 高危。
- 输出：缺陷单 → 研发修复 → `qa-bug-verify` 验证。
