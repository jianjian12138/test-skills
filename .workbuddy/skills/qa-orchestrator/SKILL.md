---

name: qa-orchestrator
description: |-
  半自动 QA 测试全生命周期编排脚手架：当用户开启一轮测试工作，需要在完整 QA 生命周期
  （需求 → 分析 → 用例设计 → API/UI/性能/安全/探索式/兼容性测试 → 执行 → 缺陷 →
  发布 → 报告 → 归档）中做规划、路由与跟踪时使用。本技能为每轮变更建立标准化产物目录，
  把任务分派给其他 qa-* 技能，并可自动推荐下一步该用哪个技能（scripts/route_next.py）
  或通过 close_loop.py 推进编排闭环。**定位说明（避免误期）：编排层为半自动——
  执行类阶段（接口/UI/性能/安全自动化）需被测环境就绪且由用户/agent 实际触发，关键
  发布与归档节点的人工确认不可跳过；本技能不臆造执行结果，仅做规划/路由/跟踪。**
  触发词："开始一轮测试"、"帮我做测试"、"测试这个项目"、"规划测试"、
  "下一步用什么技能"，或任何端到端测试任务。
  英文触发词（English triggers）：QA orchestration, test lifecycle, test workflow.
license: MIT
compatibility: "WorkBuddy / Claude / 通用 Agent（零依赖标准库）"

metadata:
  version: "1.0.0"
  category: traditional
  stage: orchestrator
  tier: 1
---
# qa-orchestrator — 测试全流程总控（闭环版）

测试工作的头号损耗来自「需求、用例、接口、执行、报告散落在多个工具、难以追溯」。
本技能是全套 `qa-*` 技能的**入口与编排器**：为每轮待测「变更」建立标准化产物树，
按生命周期把任务路由到对应子技能，并能**自动推断下一步该调谁、一键推进到归档**。

## 何时使用

- 用户开启一轮测试（新需求、新版本、回归）。
- 用户不确定下一步该用哪个测试技能 → 调 `scripts/route_next.py`。
- 需要把需求、用例、接口、执行、报告归拢到同一可追溯目录。
- 想要"一条龙"推进：从需求跑到归档 → 调 `scripts/close_loop.py`。

## 核心职责

1. **建立变更目录**（`scripts/init_change.py`）→ 8 个阶段目录 + README 看板 + ROUTING.md。
2. **识别当前阶段**，路由到对应子技能（见下方路由表）。
3. **自动推荐下一步**：`python scripts/route_next.py --change <dir> [--auto]`。
4. **一键推进**：`python scripts/close_loop.py --change <dir>` 输出并按序推进各阶段。
5. **收尾**：`qa-report` 出报告 → `qa-archive` 归档。

## 生命周期路由表（由 stages.json 自动渲染，单一事实源）

| 阶段目录 | 对应技能 | 关键产出 |
| --- | --- | --- |
| `01-requirement/` | qa-req-spec | requirement.md / reqs.json |
| `02-analysis/` | qa-test-analysis | analysis.md / testpoints.md |
| `03-cases/` | qa-test-case-gen | cases.xlsx / cases.xmind / cases.json |
| `04-testdata/` | qa-test-data · qa-env-config | data.csv / .env / testdata.json |
| `05-api/` | qa-api-doc | api-doc.md / api-doc.json / openapi.json |
| `06-execution/` | qa-api-runner · qa-ui-automation · qa-perf-locust · qa-perf-jmeter · qa-security-scan · qa-exploratory · qa-compat-matrix · qa-api-contract · qa-mobile-autotest · qa-perf-design · qa-ui-testid · qa-ui-kb · qa-execution | results.json / locustfile.py / plan.jmx / report.md / security_findings.json |
| `07-report/` | qa-report · qa-perf-analysis · qa-security-report · qa-bug-report · qa-bug-verify · qa-release-check | test-report.md / test-report.json / bug_report.json |
| `08-archive/` | qa-archive | archive.zip / ci.yaml / test-strategy.md |

### 横切关注点（贯穿全程，不属单一阶段）

| 技能 | 角色 |
| --- | --- |
| `qa-risk-based` | 基于风险的测试（RBT），前置量化风险并反推用例密度 |
| `qa-test-strategy` | 测试策略制定 |
| `qa-ci` | CI 集成与门禁接线 |
| `qa-mutation` | 变异分数（测试杀伤力）横切质量门 |
| `qa-flaky-detect` | 不稳定测试（flaky）检测横切质量门 |
| `qa-a11y` | 无障碍（WCAG 2.1 A 级）静态检查横切质量门 |
| `qa-visual-regression` | 视觉回归（DOM/属性快照）横切质量门 |
| `qa-unit-tdd` | 单元/TDD 方法学健康度横切质量门 |
| `qa-chaos` | 混沌工程治理门（实验规格须受治理，否则阻断） |
| `qa-code-review` | 代码评审启发式门（硬编码密钥等阻断，其余待处理） |
| `qa-synthetic-monitoring` | 合成监控治理门（关键旅程须有断言+告警，否则阻断） |

> 性能路线二选一：`qa-perf-locust`（代码化/CI）或 `qa-perf-jmeter`（无代码/分布式），
> 共用 `qa-perf-design` 场景 schema。分析结果分别用 `qa-perf-analysis` / `qa-perf-jmeter`。
> 路由表由 `scripts/render_stages.py` 从 `stages.json` 渲染，修改阶段请改 `stages.json` 后重渲染，并跑 `scripts/check_drift.py` 防漂移。

## 操作流程

### 步骤 1 — 建立变更工作区

```bash
python scripts/init_change.py --base <工作区根> --change "<变更名或需求ID>" [--author <测试人>]
```

在 `<base>/changes/<change_slug>/` 下创建 8 阶段目录 + `README.md` 看板 + `ROUTING.md`。

### 步骤 2 — 自动推断下一步

```bash
python scripts/route_next.py --change changes/<slug> --auto
# 输出：qa-test-analysis   （依据哪个阶段产物缺失推断）
```

脚本扫描各阶段目录产物，返回第一个未完成的阶段对应的推荐技能；`--json` 给结构化结果。

### 步骤 3 — 按序路由 + 落盘

依据推荐技能，调用并指明产物落盘目录。示例：

> 「把这份需求文档转成标准需求文档，并建立测试工作区。」
> → `qa-req-spec`，产物写入 `01-requirement/requirement.md`。

> 「基于需求做测试分析并出测试点。」
> → `qa-test-analysis`，产物写入 `02-analysis/`。

### 步骤 4 — 一键推进到归档

```bash
python scripts/close_loop.py --change changes/<slug>
```

按生命周期顺序列出待办阶段与对应技能，更新 README 看板，逐步推进；
`--apply` 时会把每个已存在产物的阶段标记为「已完成」。

## 设计原则

- **可追溯优先**：一切产物按变更归集，禁止把用例/报告丢进临时聊天。
- **路由而非重做**：本技能不实现具体分析/执行逻辑，只负责编排与落盘。
- **闭环**：`route_next` + `close_loop` 让"需求 → 归档"真正自动串联。
- **完成标准 / DoD（借鉴 loop-me 工程纪律）**：`close_loop` 推进每一阶段须满足「执行者无需再问即可继续」——产物已落盘、看板已更新、下一步明确；未达标不标 `done`。辅以 **Push-right**（不把工作过早推回上游）与 **Brief**（交接携足上下文），保证阶段间 handoff 零歧义。

## 断点续推与 Run 对象（A-01 / W3 增强）

### 断点续推（checkpoint / resume，A-01）
半自动契约：每次完成一个阶段，调用 `scripts/checkpoint.py --change <dir> --stage <d> --status done` 追加一条审计 checkpoint；
`--resume` 仅**打印**下一步该做什么，**不自动执行**——须人或 agent 显式确认后再调用对应技能。
轻量重试：`--stage <d> --retry` 标记某阶段待重做（不改已落盘产物），路由时优先回到该阶段；
阶段被重做并再次 `done` 后，先前的 `retry` 不再抢占（done 优先于 retry）。

### Run 对象生命周期（W3）
把「一次测试 / 一次变更推进」建模为 Run（`scripts/run_object.py`）：承载 run_id、模型 / Prompt / 工具版本、
超时、配置覆盖，支持 cancel / retry / apply_config_override / replay，全部动作记入 `history`（确定性、可审计）。
核心原则（企业架构研究会）：**协议层（MCP / CLI / API）不能代替运行架构**——超时、取消、重试、重放发生在 Run 层，而非协议层。

> **replay ≠ 重跑**：`replay` 仅将 Run 状态标记为 `replayed`（记录其事件流可按序还原），**不重新触发底层执行**；若需真正重跑，请用 `retry`（标记该阶段待重做）或重新发起一次新 Run。

## 参考资料

- 检查项、阈值、CLI 用法与常见坑：见 [`references/guide.md`](references/guide.md)。
