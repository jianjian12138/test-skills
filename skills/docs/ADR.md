# 架构决策记录（ADR）

> 记录 skills 系统的关键架构决策与演进理由，便于后人理解「为什么是这样」，
> 以及后续维护时的取舍边界。状态：Accepted = 已采纳；Superseded = 已被取代。

---

## ADR-001　轻量属性：治理论证层零第三方；执行层按需懒加载并显式声明

- **状态**：Accepted
- **背景**：做测试系统自己的系统，最忌「装一堆包才能跑」。甲方环境不可控，依赖越重越难落地。但「完全零第三方」与「开箱即用重能力（HTTP/Excel/Playwright）」存在张力，原"纯标准库、零第三方"表述与执行层代码（requests/openpyxl/playwright）不符，属声明 vs 现实偏差，已于 V10 整改收敛为分层声明。
- **决策（分层）**：
  - **治理论证层（零第三方）**：`qa-orchestrator`、`qa-release-check`、各信号生产者/门禁/元层脚本**仅用 Python 标准库**，不引入任何第三方包；保证任意装了 Python3 的机器直接跑。
  - **执行层（按需懒加载 + 显式声明）**：真正驱动外部能力的技能——`qa-api-runner`（requests）、`qa-report` / `qa-test-case-gen`（openpyxl）、`qa-ui-automation`（playwright）——在**函数内**懒加载第三方，并在 SKILL.md frontmatter 以 `runtime_dependencies` 字段**显式声明**；`validate_portability.py` 扫描脚本顶层 import，非标准库且未声明即 FAIL，确保「声明=现实」。
- **后果**：治理论证层 55+ 脚本零依赖可直接跑；执行层重能力由声明制依赖承载，既不污染治理论证层、又让"零依赖"声明真实可验（消除自评夸大）。

## ADR-002　质量信号契约（Quality Signal Contract）门禁

- **状态**：Accepted
- **背景**：复审发现「新能力（契约/风险/移动）未进发布门禁」，能力孤岛会复发。
- **决策**：各技能把结论写成 `signals/<skill>.json`（source/generated_at/signals[]，每条含 signal/severity/count/blocking）。门禁（`qa-release-check`）扫描聚合 `blocking=true` 的信号 → `sys.exit(1)`。
- **好处**：加新维度零改门禁代码（OCP 友好）；统一了 12 类技能的输出契约。
- **边界（P1-5 修正）**：`blocking` 字段是**唯一阻断权威**；`severity` 仅作信息性分级（供排序/展示），**不参与门禁判定**。纯描述性/信息性信号设 `blocking=false` 即不阻断——消除"severity∈{critical,high} 才阻断"的歧义（与 `gen_release_checklist.py:collect_blocking` 仅取 `blocking` 的实现一致，且被 `t_gate_medium` 用例实证）。
- **子系统边界（R-40 澄清）**：本契约的 `blocking` 权威仅作用于「质量信号门禁」（`qa-release-check` 聚合）。`qa-orchestrator` 的 `close_loop.evaluate_closure` 使用缺陷/安全 **severity（S1/S2、Critical/High）作为「发布就绪」独立门禁维度**，属于「变更闭环」子系统，与本条信号契约 `blocking` 权威是**两套并行机制、互不等价**，二者边界须清晰、不可混用（见 ADR-004 trust-tier 与 close_loop 文档）。

## ADR-003　横切关注点建模（cross_cutting）

- **状态**：Accepted
- **背景**：`qa-risk-based`/`qa-test-strategy`/`qa-ci` 曾误放在 08-archive 阶段，语义错位。
- **决策**：在 `stages.json` 顶层设 `cross_cutting` 数组，与 8 阶段并列；它们贯穿全程而非隶属单一阶段。编排 SKILL.md 单独成节说明。

## ADR-004　trust-tier 成熟度分级

- **状态**：Accepted
- **决策**：`REGISTRY.json` 每条技能带 `tier`(1/2/3)/`verified_by`/`last_verified`/`orchestrated`。
  - T1=有脚本且接编排并验证；T2=有脚本但未全验证；T3=纯文档。
- **后果**：甲方可按 tier 判断「哪些能直接用、哪些需评估」；新技能默认 T2 起步。

## ADR-005　公共库抽离（P2 工程化）

- **状态**：Superseded（被 V6 升级的 vendoring 决策推翻，见 ADR-005a）
- **背景**：55 脚本各自重复 `load_json`/`emit_signal` 等，维护成本高、行为易漂移。
- **原决策**：建 `lib/common.py` 统一 IO 与信号契约、以及 Agent 统计（Wilson CI / 两比例 z）。
  脚本通过 `sys.path.insert` 注入 `lib/` 后 `from common import ...`。**采用增量迁移**：先示范迁移 2 个脚本（qa-a11y、qa-unit-tdd），全量迁移列为后续维护项，不在本次范围强推（避免大改引入回归）。
- **推翻原因（V6）**：四专家评审指出 `lib/` 跨目录依赖违反 Anthropic Agent Skills 开放标准的「单目录可分解性」（技能目录须自包含、可独立分发）。`lib/` 也因此造成跨 agent 不可移植。

## ADR-005a　vendored `_common.py`（替代 ADR-005）

- **状态**：Accepted
- **决策**：不再使用跨目录 `lib/` 包；改为每个带脚本的技能以 `scripts/_common.py` **vendored 或内联副本任一形式自包含**公共库（仅 `emit_signal`/`load_json`/`save_json`/`read_text`/`wilson_ci`/`two_prop_z`，约 80 行、纯标准库）。现状：5 份 vendored `_common.py` 字节一致，其余技能为内联副本——二者任一即满足「单目录可分解、可独立分发」的自包含要求。
- **后果**：每个技能目录可单目录分解、可独立复制到任意 agent 技能目录；牺牲了"改一处全局生效"的 DRY 收益，换取可移植性与零耦合（权衡见 MAINTAINERS.md §2）。`qa-release-check` 等仅消费 `signals/*.json` 的脚本不依赖任何 `_common`。

## ADR-006　方法学广度补齐路线

- **状态**：Accepted
- **背景**：复审（V3）指出方法学广度仅 2/8（缺无障碍/视觉回归/混沌/单元-TDD/代码评审/合成监控）。
- **决策**：优先补高 ROI 的 3 类（a11y / visual-regression / unit-tdd），推进到 5/8；
  混沌工程、代码评审、合成监控列为下一轮。每类均以「轻量技能 + signals 契约 + 自测」形式落地，不破坏轻量属性。

## ADR-007　分发边界与生态路线

- **状态**：Accepted
- **背景**：分发生态仍为 zip-only，与开源标杆（npx/MCP/插件市场）有代际差。
- **决策**：本轮保持 zip 分发 + 规范化安装脚本（install.sh/install.ps1），不引入 MCP server（避免偏离轻量属性、且工作量大）。
  MCP / `skills add` 兼容包作为下一轮生态战役，单独评估。

## ADR-008　文档防漂移（SSOT）

- **状态**：Accepted
- **决策**：`stages.json` 为**结构 SSOT**（阶段 / 技能编排关系的唯一权威）；`SKILL.md` 中的生命周期路由表**手工维护**（非自动渲染生成）；
  `check_drift.py` 校验 `stages ⊆ REGISTRY ⊆ SKILL.md` 三处清单一致（CI 卡点），根治「新技能只进 stages 不进文档」的复发。
- **澄清（诚实边界）**：`render_stages.py` 仅输出 **stub / 辅助预览**（其 role→技能 字典仅覆盖少量示例，不保证全量），**不可替代**手工维护的 `SKILL.md` 路由表，亦非事实源；真实一致性以 `check_drift.py` 三处比对为准。
