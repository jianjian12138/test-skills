# 多专家深度评审 V10 — 40 技能 QA 系统（独立专家团 · 对标 GitHub 开源）

> 评审日期：2026-08-11 · 评审方式：模拟专家团（测试 / skills / 软件架构 / agent 四视角）+ GitHub 开源强关联项目对标
> 评审对象：`D:/test-skills/.workbuddy/skills`（40 技能 = 38 传统 + qa-agent-eval / qa-agent-security 两 Agent 测试；8 阶段 + 11 横切）
> 复闸状态（实测）：compileall OK · 自测 **63/64**（R-05 时间炸弹用例 FAIL）· drift rc=0（无漂移）· portability 40/72
> 独立定级：**7.8 / 10**（低于 V9 自评标 8.1，符合独立团更严的常态；见 §6 依据）

---

## 0. 评审范围与对标方法

| 维度 | 本次口径 |
|---|---|
| 范围清单 | 见 `01-评审范围清单.md`（40 SKILL.md / 78 py / REGISTRY v2 / stages 8+11） |
| 分级标准 | 见 `02-问题分级标准.md`（P0–P3 + 严重度矩阵） |
| 证据纪律 | 每条 `R-xxx` 必带 `文件:行号`；门禁/分数等量化结论均实测（见上"复闸状态"） |
| GitHub 对标 | 仅选**与测试 skills 强关联**的项目（LLM 测试生成、agentic QA、agent 安全红队、变异/混沌/视觉/a11y、agent 框架），不凑 star |
| 诚实底线 | 不虚高、不替未实现项背书；已实现的治理/静态门禁据实标注，未实现的真实执行明确为"待接专业工具" |

---

## 1. GitHub 开源强关联项目对标表（核心参照系）

| 类别 | 开源项目 | 与本法强关联点 | 对本包的启示 |
|---|---|---|---|
| LLM 测试生成 | **ChatUniTest**（ZJU-ACES-ISE, FSE'24） | "Generation-Validation-Repair"闭环、自适应焦点上下文 | 本 `qa-test-case-gen` 仅是 JSON→Excel/Xmind **格式化**，无 AI 生成/修复闭环（S-01） |
| 覆盖率引导生成 | **CoverUp**（arXiv:2403.16218）/ **TestGen-LLM**（Meta） | 覆盖率反馈驱动生成、丢弃不提升覆盖的用例 | 本 40 技能**缺独立覆盖率阶段/技能**（T-04） |
| Agentic QA 技能包 | **agentic-qe**（shaal, npm） | **41 个 QE Skills**、ML flaky 检测、a11y/视觉/TDD、constitution 治理、fleet 协调 | 最直接竞品：它**真跑**检查，本包多为**治理/静态门禁**（T-03/A-03）；其 frontmatter 优化（tokenEstimate/agents/status）值得借鉴（S-02） |
| 多 Agent 移动 QA | **MultiAgentAndroidQASystem**（Agent-S+AndroidWorld） | Planner/Executor/Verifier/Supervisor 四 agent 协作 | 本 `qa-orchestrator` 是单 agent 路由，非多 agent 协作（A-01） |
| 多 Agent 测试 | **Intelligent-Test-Automation**（AutoGen） | 生成/验证/执行三 agent 自修复 | 同上，编排范式差异 |
| Agent 安全基准 | **AgentDojo**（ETH SPY Lab） | 间接提示注入、ASR/效用双轴；本包方法论来源 | 二元 ASR 已被 **action-graded-severity**（arXiv 2026）证明丢弃危害程度（L0–L6）（G-01） |
| 红队框架 | **PyRIT**（MS）/ **garak**（NVIDIA）/ **ADR-Bench**（Uber, 303 场景+133 MCP） | 攻击面广度、威胁快照、ASR 分级 | 本 `qa-agent-security` 45 条**合成 fixture**，攻击面与真实度有限（G-01） |
| 变异测试 | **mutmut** / **cosmic-ray** / **PIT** | CI kill-rate 阈值门禁、覆盖率引导变异 | 本 `qa-mutation` **不注入变异体**，仅聚合分数（T-03 诚实但命名易误期） |
| 混沌工程 | **Chaos Mesh** / Gremlin | 真实故障注入、爆炸半径控制 | 本 `qa-chaos` 治理门禁，不注入（T-03） |
| 无障碍 | **axe-core** / pa11y / Lighthouse | 对比度、键盘可达性真实检查 | 本 `qa-a11y` 仅静态子集（T-03） |
| 视觉回归 | **Percy** / BackstopJS / Applitools | 像素级比对 | 本 `qa-visual-regression` 仅 DOM/属性快照（T-03） |
| Agent 框架 | **LangGraph** / **AutoGen** / **OpenAI Agents SDK** / **Claude Agent SDK** | 显式图、checkpoint、human-in-the-loop、护栏 | 本编排器无图引擎/checkpoint/护栏框架（A-01） |

> 结论：本包在**治理编排层 + 信号契约 + fail-closed 门禁哲学**上自有亮点（见 §5 亮点），但在**真实执行深度**与**多 agent 协作范式**上明显浅于对标开源；定位应清晰表述为"治理/编排层"，而非"测试执行器"。

---

## 2. 测试专家视角（QA）

### T-01 · P2 · 自测套件含时间炸弹用例
`tests/run_all_tests.py:287-300` 的 `t_timezone_ok` 硬编码 `generated_at="2026-08-10T22:00:00+08:00"`。门禁 `STALE_WINDOW_H=24`（`qa-release-check/scripts/gen_release_checklist.py:39`），当前墙钟 2026-08-11 23:12 → 该信号已 stale → `stale_signals` 阻断 → `rc=1`。**实测 63/64 失败正是此例**。门禁逻辑本身正确（fail-closed），但自测非确定性：CI 次日即红，直接削弱"全绿交付就绪"的可信度（与 V9 声称 64/64 不符）。
**修复**：fixture 改用相对 `now` 的动态戳 `(datetime.now().astimezone() - timedelta(hours=1)).isoformat()`，使 stale 判定与墙钟解耦。

### T-02 · P2 · 信任证据为 CI 派生，非人工独立验证
`verified_by="ci:run_all_tests"` 由 `build_registry.py:114-129` 回填（全部 tier-1 标 `ci:run_all_tests` + 日期，2 个纯文档技能标 `pending:see-§7`）。这是"有证据"但证据强度有限——golden 套件自跑 ≠ 甲方人工冒烟。建议验收前对 tier-1 做一轮人工冒烟并升级为 `manual:*`。

### T-03 · P1 · 多个"质量门"实为治理/静态/启发式，命名-能力落差
以下技能**诚实披露**了边界，但命名/副标题易让甲方误判为"可执行测试"：
- `qa-mutation`：只聚合分数，不注入变异体（`SKILL.md:53-56`）—— 对照 mutmut/cosmic-ray。
- `qa-chaos`：治理门禁，不注入故障（`SKILL.md:15,38`）—— 对照 Chaos Mesh。
- `qa-synthetic-monitoring`：治理门禁，不发起探测（`SKILL.md:15,37`）。
- `qa-a11y`：仅静态子集，不计算对比度/键盘可达（`SKILL.md:67-69`）—— 对照 axe-core。
- `qa-visual-regression`：不做像素比对（`SKILL.md:62`）—— 对照 Percy。
- `qa-code-review`：启发式，不解析 AST（`SKILL.md:40`）—— 对照 Semgrep。
**建议**：名称/副标题显式标注"治理门禁/静态检查"；甲方手册明确"本包是治理编排层，真实执行须接专业工具"。

### T-04 · P3 · 缺独立覆盖率技能/阶段
ChatUniTest/CoverUp/TestGen-LLM 均把覆盖率反馈作为生成闭环核心；本 40 技能生命周期无独立 coverage 阶段，仅 `qa-mutation` 间接涉及。建议新增 `qa-coverage` 或明确接 `pytest-cov` 并接入信号契约。

---

## 3. Skills 专家视角

### S-01 · P2 · `qa-test-case-gen` 命名-能力落差
`SKILL.md:15-18,51-55` 实为"结构化 JSON→Excel/Xmind 确定性格式化"，`expand_cases.py` 仅基于字段派生边界（非 LLM 生成/验证/修复）。对照 ChatUniTest 的 Generation-Validation-Repair，存在"用例**生成**"命名与实际"格式化直出"的能力落差，易误期。建议改名或加副标题"用例格式化直出"，并标注非 AI 生成。

### S-02 · P2 · frontmatter 不一致
仅 `qa-code-review` 带 `metadata{category,stage,tier}`（`SKILL.md:5-8`）；其余技能 frontmatter 无 tier/stage 镜像，而 REGISTRY 有 `tier/orchestrated`（`REGISTRY.json:15-18`）。对照 agentic-qe 41 技能均带优化 frontmatter（tokenEstimate/agents/implementation_status），建议归一化（category/stage/tier）+ 跨 agent 兼容字段。

### S-03 · P3 · references 死链校验缺口
SKILL.md 多引 `references/guide.md`/`checklist.md`/`cases-schema.md`；`check_drift.py` 已校验 SKILL.md↔REGISTRY 引用，但**未覆盖 references 内部死链**。建议扩展漂移守卫至 references 存在性。

### S-04 · P3 · 触发词偏窄（中文为主）
触发词多为中文短语，跨 agent（Claude/通用）英文触发覆盖不足；agentic-qe 用 agent 定义+slash command。建议补充英文 synonym 触发，提升跨 agent 可发现性。

---

## 4. 软件架构专家视角

### A-01 · P2 · 编排器为"目录产物状态机"，非图/工作流引擎
`qa-orchestrator`（route_next/close_loop）扫描阶段目录推断下一步，是**基于文件的确定性状态机**。对照 LangGraph（显式图+checkpoint+human-in-the-loop）、AutoGen（多 agent 协作）、agentic-qe（fleet+持久化事件存储）：本编排器**无失败重试/回滚、无 checkpoint 恢复、无多 agent 并行、无真实护栏框架**；`--strict`/`--allow-no-evidence` 为软闸。
**优势**（须保留）：零依赖、无框架锁定、确定性、易审计、fail-closed 哲学。建议补齐 resume/checkpoint 与"编排层契约"文档。

### A-02 · P1 · 信号契约新鲜度窗口与墙钟耦合（设计反模式）
亮点：信号契约是全局最扎实的设计——`emit_signal` SSOT（19 处字节一致）、`schema_version`、`additionalProperties:false`、`blocking` 唯一门禁权威、fail-closed、stale 窗口（`gen_release_checklist.py:39,122-138,185-192`）。
但 `generated_at` 强制 + `STALE_WINDOW_H=24` 与**自测时间炸弹直接耦合**（见 T-01）：新鲜度窗口不应影响"门禁能否生成清单"。建议契约层与测试层解耦（测试注入固定 `now` 或契约提供 `--no-stale` 豁免）。

### A-03 · P2 · 横切关注点为"推荐"非"硬门禁"，一致性保障弱
11 个 cross_cutting 仅 `stages.json` 字符串数组（`stages.json` cross_cutting 11 项）；V9 才在 route_next 注入 `cross_cutting_recommend`，close_loop 有追踪但 `--strict-cross` 默认关。对照 agentic-qe 的 "constitution system" 强制治理，本包关键横切（a11y/code-review/mutation）未显式纳入发布门禁。建议将高相关横切可显式纳入 `qa-release-check` 聚合。

### A-04 · P3 · `_common.py` vendored 5 份的维护面
R-24 已验证 5 份 vendored `_common.py` 字节一致且有守卫，但 vendoring 本身有漂移面。可考虑单例共享 + 入口校验，降低长期维护成本。

---

## 5. Agent 专家视角

### G-01 · P1 · `qa-agent-security` 二元 ASR 缺危害分级 + 攻击面偏窄
`SKILL.md:49-53` 用二元 ASR + 效用保持率双轴，方法论借 agentdojo/promptfoo，正确。但 2026 arXiv **action-graded-severity** 指出二元 ASR 丢弃"行动危害程度"信息（L0–L6 量级：可逆/越界/提权）。对照 PyRIT/garak/ADR-Bench（Uber，303 场景+133 MCP server）的攻击面广度，本包 45 条为**合成 fixture**（非真实生产 agent 攻击），外部效度有限。建议引入 severity-graded ASR 与真实 agent harness。

### G-02 · P2 · `qa-agent-eval` 评测任务为合成 harness 桩
`SKILL.md:35-39` Pass@k/Wilson CI/五维度方法学扎实（借 tau-bench/Eval-Anything）。但 `gen_task.py` 自动生成任务+rubric（`checkers_autogen`），非真实生产 agent 轨迹。对照 SWE-bench/agentdojo 真实任务集，外部效度有限。建议支持导入真实 trace。

### G-03 · P2 · 两 Agent 技能与 8 阶段路由无桥接
两 agent 技能独立类目（不接入 orchestrator），符合设计；但缺"agent 评测→传统 QA 联动"（如 agent 暴露接口的回归）。agentic-qe 把 testability-scoring 贯穿全程。建议补轻量桥接技能/信号。

### G-04 · P3 · 多轮渐进攻击自动归因偏弱
`judge_attack` 按 `success_criteria` 单轮判定；`multi_turn_induction` 已有 5 条，但对照 Backbone Breaker 的"威胁快照"方法，可增强多轮渐进攻击的自动危害归因。

---

## 6. 亮点（独立团认可，须保留）

1. **信号契约 SSOT + fail-closed 哲学**：`emit_signal` 19 处字节一致、`blocking` 唯一权威、severity 仅信息性、损坏即阻断——这是比多数开源脚本更严谨的"真实门禁"设计。
2. **三道闸工程化**：compileall / run_all_tests / check_drift / validate_portability 形成可复跑的 CI 防线（唯一瑕疵是 T-01 时间炸弹）。
3. **诚实边界标注**：qa-chaos/synthetic-monitoring/a11y/visual/mutation/code-review 均显式声明"不实际执行"，无假绿包装。
4. **零依赖治理层定位清晰**：标准库实现、跨 agent 兼容、无框架锁定，部署面极小。
5. **Agent 双技能方法学正确**：Pass@k/Wilson CI（eval）、ASR/效用双轴（security）口径对齐 agentdojo/tau-bench。

---

## 7. 问题汇总与定级（详见 `04-问题跟踪看板.md`）

| 编号 | 角色 | 问题 | 级别 | 证据 |
|---|---|---|---|---|
| T-01 | 测试 | 自测时间炸弹用例（t_timezone_ok 硬编码戳） | P2 | run_all_tests.py:287-300；gen_release_checklist.py:39 |
| T-02 | 测试 | verified_by 为 CI 派生非人工 | P2 | build_registry.py:114-129；REGISTRY.json:16 |
| T-03 | 测试 | 治理/静态门禁命名-能力落差（6 技能） | **P1** | qa-mutation/chaos/synthetic-monitoring/a11y/visual-regression/code-review SKILL.md |
| T-04 | 测试 | 缺覆盖率技能/阶段 | P3 | stages.json（无 coverage 阶段） |
| S-01 | skills | qa-test-case-gen 命名-能力落差 | P2 | qa-test-case-gen/SKILL.md:15-18,51-55 |
| S-02 | skills | frontmatter 不一致 | P2 | qa-code-review/SKILL.md:5-8 vs 其余 |
| S-03 | skills | references 死链校验缺口 | P3 | check_drift.py（未覆盖） |
| S-04 | skills | 触发词偏窄（中文为主） | P3 | 各 SKILL.md description |
| A-01 | 架构 | 编排器非图/checkpoint/多 agent | P2 | qa-orchestrator route_next/close_loop |
| A-02 | 架构 | 新鲜度窗口与墙钟耦合（设计反模式） | **P1** | gen_release_checklist.py:39,122-138 |
| A-03 | 架构 | 横切为推荐非硬门禁 | P2 | stages.json cross_cutting；close_loop --strict-cross 默认关 |
| A-04 | 架构 | _common.py vendored 5 份维护面 | P3 | R-24 看板 |
| G-01 | agent | 二元 ASR 缺危害分级 + 攻击面窄 | **P1** | qa-agent-security/SKILL.md:49-53；arXiv action-graded-severity |
| G-02 | agent | 评测任务为合成 fixture | P2 | qa-agent-eval/SKILL.md:35-39 |
| G-03 | agent | agent↔传统 QA 无桥接 | P2 | 两 agent 技能独立类目 |
| G-04 | agent | 多轮渐进攻击归因偏弱 | P3 | judge_attack / multi_turn_induction |

**级别分布**：P0×0 · P1×3 · P2×9 · P3×4。
**独立定级 7.8/10**：亮点（信号契约/fail-closed/诚实边界/零依赖）拉高下限；P1 三项（治理门命名落差、新鲜度耦合、二元 ASR 缺分级）与"真实执行深度浅于对标开源"拉低上限。无 P0，说明 V9 已解决致命项，但**交付定位须从"测试执行器"修正为"治理编排层"**，否则甲方按"执行器"预期验收会落差。

---

## 8. 整改建议（概览，详见 `07-整改计划.md`）

- **立即（P1）**：① 治理门技能改名/副标题标注"治理门禁/静态检查"并写入甲方手册（T-03）；② 信号契约与测试解耦 stale（A-02）；③ `qa-agent-security` 引入 severity-graded ASR（G-01）。
- **近期（P2）**：修时间炸弹自测（T-01）、人工冒烟升 verified_by（T-02）、test-case-gen 重定位（S-01）、frontmatter 归一化（S-02）、编排器补 checkpoint/桥接（A-01/G-03）。
- **演进（P3）**：补 qa-coverage（T-04）、references 死链校验（S-03）、英文触发词（S-04）、_common 单例（A-04）、真实 agent harness（G-02/G-04）。

> 本评审为**独立团结论**，未自动整改；是否进入下一轮升级（V10）由用户裁决。
