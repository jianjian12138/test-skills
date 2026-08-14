> ⚠️ **本文已被取代（请勿作为当前验收依据）**：本文件是 V10 升级的**早期草案（Phase 1–4 规划）**，现由仓库根目录
> [`UPGRADE_PLAN_V10.md`](../../UPGRADE_PLAN_V10.md)（V10 最终收口版，含 Phase 5）作为**唯一现行计划**。
> 本文第 44 行「Phase 5 ⬜ 待办 / 目标 ≥8.5」为草案旧口径，**已作废**；Phase 5 实际状态以根版为准：
> **已完成（93/93 自测）、自评 ≤8.1（诚实不虚高）**。如有冲突，一律以根版 `UPGRADE_PLAN_V10.md` 为准。

# WorkBuddy 测试技能套件 · V10 升级计划 · 早期草案（Phase 1–4，已取代）

> 来源 1（基础整改）：`reviews/EXPERT_PANEL_REVIEW_V10.md`（独立专家团 **7.8/10**，裁定 **P1×3 / P2×9 / P3×4**）
> 来源 2（行业对标）：10 篇微信公众号强关联文章的可取项萃取（见 §5 附录，编号 W1–W10）
> 目标：**清零全部 P1（3 项）+ 高优先 P2**，并把行业可取项作为"增强模块"并入各阶段；诚实保留"真实执行深度"为演进项
> 系统根：`D:/test-skills/.workbuddy/skills/`（40 技能：38 传统 + 2 Agent 测试；8 阶段 + 11 横切）
> 复闸实测基准（V10 评审时）：compileall OK · 自测 **63/64**（T-01 时间炸弹）· drift rc=0 · portability 40/72
> **Phase 1 收口（08-11）**：compileall OK · 自测 **69/69**（+5 golden：t_asr_harm_grading / t_grade_empty_dict_failclosed / t_no_trivial_assertion / t_api_engine_negative / t_coverage_real_increase）· drift rc=0 · portability **40/73**（新增 coverage_check.py）
> **Phase 2 收口（08-11）**：compileall OK · 自测 **72/72**（Phase 2 +3 golden：t_three_level_derivation / t_step_mapping_table / t_gen_task_five_classes）· drift rc=0 · portability 40/73。S-01 test-case-gen 重定位为"格式化直出"+能力边界；W7 三级推导模型落地(qa-test-analysis+qa-test-case-gen)+八大维度交叉矩阵+资损 L1-L4(qa-risk-based)；W2 步骤对照表+调试三轮制(qa-test-case-gen/qa-ui-automation)；W8 gen_task 五类样本轮转+风险类直连红队(qa-agent-eval)，根治 V9 R-08 同质子任务虚高 Pass@k。
> **Phase 3 收口（08-12）**：compileall OK · 自测 **80/80**（Phase 3 +8 golden：t_checkpoint_resume / t_run_object_lifecycle / t_structured_events / t_domain_slot_insert / t_locator_health_warn / t_bridge_agent_regression / t_release_include_cross / t_w3_w9_docs）· drift rc=0 · portability **40/78**（新增 checkpoint.py / run_object.py / trace_event.py / locator_health.py / bridge_agent_regression.py，73 → 78）。A-01 checkpoint/resume（retry 优先 + done 优先于 retry，半自动契约）；W3 Run 对象生命周期 + 结构化事件流；W7 领域插槽（insert/replace + 平台锁，produce 态基线零漂移）；A-03 横切 opt-in（--include-cross 缺失即阻断，收紧）；G-03 Agent 暴露接口→传统 QA 回归信号桥接；W5 定位金字塔 + locator-health（<65 预警）；W9 Workflow×Agent 边界 + 8 原子操作 + O-T-A-R。
> **Phase 4 收口（08-11）**：compileall OK · 自测 **89/89**（Phase 4 +9 golden：t_six_dim_scorecard / t_trajectory_cost / t_error_breakdown / t_probe_baseline_delta / t_import_trace / t_progressive_attribution / t_expected_action_highrisk / t_attack_surface_bias / t_fixtures_versioned）· drift rc=0 · portability **40/79**（新增 scorecard.py，78 → 79）。G-02 `trace_event.py --import-trace` 通用轨迹（OTel/agentdojo）转结构化事件；W6 `scorecard.py` 六维评分卡（可算维度直接计算、缺数据维度显式 na 不伪称 1.0）+ 轨迹成本聚合 + 红队新增 bias 偏见检测面（50 条/9 面）；W8 `grade_run.py` expected_action 期望动作 fail-closed 拦截 + high_risk 单独门禁、`gen_task.py` manifest 版本化（稳定核心集/挑战集）+ `fixtures/fixtures_manifest.json`；W9 `probe_baseline` 分桶 delta + 稳定方差<3% + 通过率/有效率一致性；G-04 `judge_attack.py --attribute-progressive` 多轮渐进危害威胁快照归因。

---

## 0. 三道 CI 闸（任何改动后必须仍全绿）

| 闸 | 命令 | 现状 / 目标 |
|---|---|---|
| 1. golden 自测 | `python tests/run_all_tests.py` | **89/89**（Phase 1 +5；Phase 2 +3；Phase 3 +8；Phase 4 +9：six_dim/trajectory_cost/error_breakdown/probe_baseline/import_trace/progressive/expected_action/bias/fixtures_versioned；63/64 → 89/89） |
| 2. 漂移守卫 | `python qa-orchestrator/scripts/check_drift.py` | **rc=0（无漂移）** |
| 3. 可移植性 | `python tools/validate_portability.py` | **40 技能 / 79 脚本 PASS**（Phase 1 coverage_check 72→73；Phase 3 五脚本 73→78；Phase 4 scorecard.py 78→79） |

复闸标准套（每阶段结束执行）：
```bash
PY="C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe"
ROOT="D:/test-skills/.workbuddy/skills"
"$PY" -m compileall -q "$ROOT"
"$PY" "$ROOT/tests/run_all_tests.py"
"$PY" "$ROOT/qa-orchestrator/scripts/check_drift.py"
"$PY" "$ROOT/tools/validate_portability.py"
echo "EXIT=$?"   # 三者均 0 方为通过
```

---

## 1. 五阶段总览与退出标志

| 阶段 | 清零项（基础）+ 行业增强（Wx） | 退出标志（三道闸全绿 + 附加） | 状态 |
|---|---|---|---|
| **Phase 1** | P1：A-02 / T-03 / G-01 + 测试核心增强（W2/W9/W10 假通过治理·永真断言·覆盖率闭环） | stale 解耦 64/64 复绿；6 治理门标注；severity-graded ASR；"AI 假通过清单"落成 | ✅（69/69·drift0·port40/73）|
| **Phase 2** | P2：S-01 + 用例生成质量深化（W7 三级推导·8 维交叉·资损 L1-L4 / W2 步骤对照·调试三轮 / W8 五类样本） | test-case-gen 重定位；测试点中间层；gen_task 五类样本 | ✅（72/72·drift0·port40/73）|
| **Phase 3** | P2：A-01 / A-03 / G-03 + 编排与执行增强（W3 Run 对象·事件流 / W7 领域插槽 / W9 Workflow×Agent 边界·原子操作 / W5 定位金字塔·locator-health） | checkpoint 文档；横切 opt-in 入 release；桥接信号；Run 对象模型 | ✅（80/80·drift0·port40/78）|
| **Phase 4** | P2：G-02 / G-04 + Agent 评测深化（W6 六维度·轨迹效率·红队攻击面 / W8 判定规则·错误分类·版本化 / W9 能力探针基线） | 真实 trace 导入；6 维评分卡；分桶 delta 度量 | ✅（89/89·drift0·port40/79）|
| **Phase 5** | P3：S-02 / S-03 / S-04 / A-04 / T-02 + 收尾（W4 触发场景 description） | frontmatter 归一；死链校验；英文触发；verified_by 人工；V10 文档 + 复评 V13（≥8.5） | ⬜ |

> 行业增强项（Wx）均来自 §5 附录萃取，标注于各阶段便于追溯。保留项（真实执行深度）见 §4，不强制本轮。

---

## 2. 各阶段关键落地（file:line + golden + 行业来源）

### Phase 1 — P1 清零 + 测试核心增强（假通过 / 永真断言 / 覆盖率闭环）

- **A-02 信号契约与测试解耦 stale**：`qa-release-check/scripts/gen_release_checklist.py:39`（`STALE_WINDOW_H=24`）增加 `--no-stale` 豁免或测试注入固定 `now`；确保"门禁能否生成清单"不受墙钟影响。**直接修 T-01 时间炸弹**：`tests/run_all_tests.py:287-300` 的 `t_timezone_ok` fixture 改相对 `now` 动态戳 `(now - timedelta(hours=1))`。
- **T-03 治理门命名-能力落差**：`qa-mutation/qa-chaos/qa-synthetic-monitoring/qa-a11y/qa-visual-regression/qa-code-review` 的 SKILL.md 副标题/首段显式标注"治理门禁 / 静态检查 / 不实际执行"；`SKILLS_DELIVERY.md` 增专节"本包是治理编排层，真实执行须接专业工具（mutmut/Chaos Mesh/axe-core/Percy/Semgrep）"。
- **G-01 severity-graded ASR**：`qa-agent-security/scripts/calc_asr.py` 引入 L0–L6 行动危害量级（借 arXiv 2026 action-graded-severity），输出 `harm_level`；信号可携带 severity 分级；扩充攻击面至少 + 真实 agent harness 接入说明（对照 PyRIT/garak/ADR-Bench）。
- **【W2/W9/W10 增强】AI 假通过治理（最高价值）**：新增 `references/ai-false-pass.md` 统一"AI 假通过模式清单"，并落到两处：
  - `qa-execution` / `qa-ui-automation` 的断言逻辑接入 **v2 严口径 9 条**（W9）：前置态未构造 / 单帧终态推时序 / "没看到就是通过" / 环境异常页当降级 / UI 判后端 payload / Agent 未完成关键动作就 finish / 平台不支持 / 断言意图错位 / 配置对照缺失 → 命中即判 `blocked`/`invalid`；配 **BLOCKED 快速路径**（命中即 finish，不硬滑烧 token）。**直接治愈 V9 残留**：`grade_run.py:158` 空 dict 仍假绿、`engine.py` 无 status 断言符且强制 `<400` 假绿。
  - **永真断言黑名单（W2/W10）**：断言设计自检——"如果把操作步骤全部注释掉，断言还能通过吗？能通过 = 无效，必须改"。`qa-test-case-gen`/`qa-execution` 引入 `assert` 须含语义断言符（允许 `status`/`body`/`error` 等负向断言），禁止纯"页面加载即 PASS"。
  - **覆盖率闭环（W10）**：将 T-04 的"缺覆盖率技能"在本阶段启动——`qa-unit-tdd`/`qa-mutation` 从"生成/聚合分数"升级为"覆盖率**真提升**校验"（Coverage Parser 思路：反复执行并用覆盖率报告判断是否真增覆盖，非仅生成测试）。
- golden：`t_timezone_ok`（改动态戳后复绿）/ `t_ai_false_pass_blocked`（9 条命中判 blocked）/ `t_no_trivial_assertion`（永真断言被拦）/ `t_coverage_real_increase`（覆盖真提升校验）。

### Phase 2 — 用例生成质量深化（三级推导 / 步骤对照 / 五类样本）

- **S-01 test-case-gen 重定位**：`qa-test-case-gen/SKILL.md:15-18,51-55` 副标题改"用例格式化直出"，标注非 AI 生成（与 V9 命名落差一致）。
- **【W7 增强】三级推导中间层**：`qa-analysis` + `qa-test-case-gen` 引入"功能点 → 测试点 → 测试用例"三级推导（测试点=介于需求与用例的"验证什么"单元），提升用例采纳率（对标 AliExpress 60-70%→90%+）。
- **【W7 增强】八大测试维度交叉矩阵**：`qa-risk-based` 补"资损风险分析（代码血缘 L1-L4）"维度，用例 × 8 维度（交互/服务端/安全合规/资损/性能/国际化/兼容/埋点）交叉组合。
- **【W2 增强】步骤对照表 + 调试三轮制**：`qa-test-case-gen`/`qa-ui-automation` 生成后强制"用例步骤 ↔ 代码实现"逐条对照表（防 11 步只实现 3 步）；调试三轮制（3-5 关键 → 仅失败 → 全量；超 3 轮标记待人工）。
- **【W8 增强】五类样本设计**：`qa-agent-eval/scripts/gen_task.py` 任务生成覆盖 高频/关键/边界/表达变化/风险 五类（风险类直连红队），避免任务同质性虚高 Pass@k。
- golden：`t_three_level_derivation`（三级结构）/ `t_step_mapping_table`（对照表存在）/ `t_gen_task_five_classes`（五类样本齐）。

### Phase 3 — 编排器与执行层增强（Run 对象 / 领域插槽 / 原子操作）

- **A-01 编排器补 checkpoint/resume**：`qa-orchestrator` 补断点续推文档 + 轻量失败重试，写明"半自动 + 人工确认"契约（保留零依赖/确定性/易审计优势）。
- **A-03 横切 opt-in 入发布门禁**：`qa-release-check` 支持 `--include-cross`（默认关），将 a11y/code-review/mutation 高相关横切可显式纳入聚合（回应 V10 评审 A-03）。
- **G-03 agent↔传统 QA 桥接**：agent 暴露接口自动转 `qa-api-runner` 回归信号，桥接信号接入 release-check。
- **【W3 增强】Run 对象生命周期模型**：把每次测试/变更建模为 `Run`（Run ID、模型/Prompt/工具版本、超时、取消/重试/重放/配置覆盖），升级 `qa-orchestrator` 从"目录产物状态机"到 Run 对象；明确"协议层 MCP/CLI/API 不能代替运行架构"。
- **【W3 增强】结构化事件流**：`qa-agent-eval` trace 升级为结构化事件（工具调用/状态写入/模型重试/任务结束均事件类型，关联 Run ID/步骤/参数/上下游），支撑可重放与失败分类。
- **【W7 增强】领域可扩展插槽**：`stages.json` + `route_next` 支持领域 `insert`/`replace` 节点（平台强保障节点不可改，领域节点可定制并走同一上报协议）。
- **【W9 增强】Workflow × Agent 边界声明**：`qa-execution` 明确哪些环节走预定义 workflow（环境/账号/配置函数化）、哪些给 Agent 自主（识别状态/决定动作/断言证据）——印证本包设计，补边界声明。
- **【W5 增强】定位金字塔 + locator-health**：`qa-compat-matrix`/`qa-ui-automation` 移动端定位策略 L1 accessibility-id（跨端首选）→L5 XPath（仅兜底注释原因）；`locator-health` 预警（healthIndex<65 推动开发补 data-qa 钩子）。
- **【W9 增强】8 类原子操作 + O-T-A-R 循环**：`qa-execution`/`qa-ui-automation` 收敛 aiTap/aiInput/aiScroll 等 8 原子操作 + Observation→Thought→Action→Replanning 抽象。
- golden：`t_run_object_lifecycle` / `t_structured_events` / `t_domain_slot_insert` / `t_locator_health_warn`。

### Phase 4 — Agent 评测/红队深化（六维度 / 能力探针 / 版本化）

- **G-02 导入真实 trace**：`qa-agent-eval` 支持导入真实 agent trace（非仅合成 harness）。
- **G-04 多轮渐进攻击归因**：`qa-agent-security/judge_attack` 增强多轮渐进攻击自动危害归因（威胁快照方法）。
- **【W6 增强】Agent 评测 6 维度**：`qa-agent-eval/calc_metrics.py` 从 Pass@k 扩展为 任务成功率/工具调用准确性/规划合理性/反思纠错/轨迹效率/安全合规 六维评分卡。
- **【W6 增强】轨迹效率（成本维度）**：calc_metrics 加步数/Token/耗时/成本统计。
- **【W6 增强】红队攻击面扩展**：`qa-agent-security` 参照 Giskard 增 注入/泄露/偏见 检测类攻击（45 条合成 fixture → 更宽）。
- **【W8 增强】判定规则结构化 + 错误分类 + 高风险门槛**：`grade_run.py` checkers 强化"期望动作"（拒答/转人工），治 V9 残留"拒答语掩盖真实泄露"；calc_metrics 加错误分类统计；高风险任务单独门禁（不允许用其他题高分抵消）。
- **【W8 增强】评测集版本化运营**：fixtures 运营为"稳定核心集 + 挑战集"，带版本号/维护人/更新时间。
- **【W9 增强】能力探针基线（替代跑全量看通过率）**：用分桶 delta 表 + 稳定方差<3% + "通过率与有效率一致性"度量，替代单点通过率——**直接补 T-01 时间炸弹的度量子**，并把红队置信带落到"有效率"而非"通过率"。
- golden：`t_six_dim_scorecard` / `t_trajectory_cost` / `t_error_breakdown` / `t_probe_baseline_delta`（+ 实测另增 `t_import_trace` / `t_progressive_attribution` / `t_expected_action_highrisk` / `t_attack_surface_bias` / `t_fixtures_versioned`，共 9 条）。

### Phase 5 — Skills 工程收尾 + 文档 + 复评 V13

- **S-02 frontmatter 归一化**：全技能补 `category/stage/tier`（+ 跨 agent 兼容字段），`build_registry.py` 可从 SKILL.md 直读。
- **S-03 references 死链校验**：`check_drift.py` 扩展至 references 内部存在性校验。
- **S-04 英文触发词**：各 SKILL.md description 补英文 synonym 触发（跨 agent 发现）。
- **【W4 增强】触发场景写入 description**：明确"用户上传接口文档时 / 请求生成报告时"等触发条件，提升 agent 命中。
- **A-04 _common 单例**：vendored 5 份 `_common.py` 收敛为单例共享 + 入口校验（guard 保留）。
- **T-02 verified_by 人工冒烟**：甲方验收前对 tier-1 做人工冒烟，升 `manual:*`。
- 收尾：本文 `docs/V10_UPGRADE_PLAN.md` + `reviews/CONSOLIDATED_REVIEW_V13.md`（自评 ≤ 7.8+0.3=8.1 上限，诚实不虚高）；`SKILLS_DELIVERY.md` 升 V10、自测数 64/64、治理编排层定位专节；`07-整改计划.md` 关闭 P1/P2。
- golden：`t_frontmatter_normalized` / `t_refs_no_deadlink` / `t_en_trigger_words` / `t_manual_verified`。

---

## 3. 关键纪律（不假绿，承接 V9）

- **全部修复 fail-closed 默认**：A-02 stale 豁免仅测试层；G-01 无危害分级不默认 PASS；假通过命中即 blocked；永真断言即拦。
- **golden 不得为过而改预期**：T-01 用动态戳而非删用例；假通过用真实负向 fixture 断言。
- **"通过率下降 ≠ 坏事"原则**（W9）：挤掉虚高后通过率可降，须追"通过率与有效率一致性"——文档明确，避免甲方误读。
- **真实执行深度为保留项**：qa-chaos/synthetic-monitoring/a11y-pixel/visual-pixel/mutation-injection 的"真实执行"属产品路线选择，本计划仅做"治理门禁标注 + 接口预留"，不伪称已执行。
- **复评 meta 上限**：CONSOLIDATED_REVIEW_V13 自评 ≤ 8.1，杜绝自评虚高。

---

## 4. Owner / 时间线 / 保留项

| 项 | 内容 |
|---|---|
| 计划制定 | 四专家评审 V10（07-11）+ 10 篇微信行业文章可取项萃取（07-11） |
| 执行 | 单人逐阶段闭环（Phase 1 → 5），每阶段复闸 |
| 验证 | 三道闸全程复跑：目标 compileall OK / 89/89（Phase1+2+3+4 累计） / drift 0 / portability 40/79 |
| 交付物 | `docs/V10_UPGRADE_PLAN.md`（本）、`reviews/CONSOLIDATED_REVIEW_V13.md`、`SKILLS_DELIVERY.md`(V10) |
| 后续建议 | 甲方按"治理编排层"口径验收；tier-1 人工冒烟；真实执行深度演进项另立路线 |

**保留项（明确归属，非静默丢弃）**：
- 真实执行深度（接 mutmut/Chaos Mesh/axe-core/Percy/Semgrep 或自研）—— 产品路线选择，本计划仅标注 + 接口预留。
- 多 agent 协作范式（LangGraph/AutoGen 式）—— 架构演进方向，本期不改单 agent 路由核心（保留零依赖优势）。
- 本地模型私有化（W1 Ollama+Qwen）—— 执行层演进，本期不绑定具体运行时。

---

## 5. 附录：10 篇微信文章可取项萃取表（W1–W10）

| 编号 | 文章（作者·日期） | 核心可取项 | 映射到本包 | 关联问题 |
|---|---|---|---|---|
| **W1** | LangChain+Playwright 智能测试 Agent（杨火锅·08-11） | 声明式测试（描述目标 vs 写步骤）、JSON 输出 Pass/Fail 集成 CI、本地模型私有化、自定义工具封装、探索式测试 | qa-ui-automation / qa-execution（声明式+探索式） | 演进 |
| **W2** | TestCase-UIAuto Skill 开源（木槿年·07-10） | **永真断言黑名单**、**步骤对照表**、调试三轮制、知识库回写、定位策略优先级(role>text>label>placeholder>css,禁 .first/.nth) | qa-test-case-gen / qa-execution / qa-ui-kb | 治 V9 假绿 + S-01 |
| **W3** | Agent 自动化测试不是模拟人工（企业架构研究会·08-11） | **Run 对象生命周期**（Run ID/版本/超时/取消重试重放）、**结构化事件流**、协议层(MCP/CLI/API)不替代运行架构 | qa-orchestrator / qa-agent-eval trace | A-01 增强 |
| **W4** | 三种方式玩转 Skills（辰金雨漫·06-17） | 触发场景写入 description、一个任务一个 Skill、MCP vs Skill 分工 | skills 工程（弱） | S-04 增强 |
| **W5** | 5 步打造 Cursor 自动化 Skill（辰金雨漫·07-06） | **定位金字塔**(移动端 L1-L5)、质量评分卡+失败分诊决策树+中文简报、locator-health 预警、先蓝图后 case | qa-compat-matrix / qa-ui-automation / qa-report | S 新项 |
| **W6** | AI 评测开源框架全景（硅基星尘·07-30） | **Agent 评测 6 维度**、轨迹效率(步数/Token/耗时/成本)、Giskard 红队攻击面(注入/泄露/偏见)、LLM-as-Judge 偏见 | qa-agent-eval / qa-agent-security | G 新项 |
| **W7** | AliExpress 测试 Skill 体系（明朗·06-24） | **三级推导**(功能点→测试点→用例)、**八大测试维度交叉**、资损风险 L1-L4、**领域可扩展插槽**(insert/replace)、本地+云端双阶段、用例召回(粗筛+精排)、度量反哺 | qa-analysis / qa-test-case-gen / qa-risk-based / qa-orchestrator | T/S/A 新项 |
| **W8** | AI 业务评测集完整指南（懂点点AI·08-05） | **五类样本**(高频/关键/边界/表达变化/风险)、判定规则结构化(期望要点/必须包含/期望动作)、同环境比版本+错误分类+高风险门槛、**评测集版本化**(稳定核心集+挑战集) | qa-agent-eval / qa-agent-security / grade_run | G 新项 |
| **W9** | Agent 自规划执行实践 UI 测新（简礼 AliExpress·08-10） | **AI 假通过 v2 严口径 9 条 + BLOCKED 快速路径**、**能力探针基线**(分桶 delta/方差<3%/通过率与有效率一致性)、Workflow×Agent 边界、**8 类原子操作 + O-T-A-R**、"通过率下降≠坏事" | qa-execution / qa-ui-automation / qa-agent-eval 度量 / 断言治理 | 治 V9 假绿 + T/G 新项 |
| **W10** | Cover-Agent 覆盖缺口变回归用例（小肥胖子·07-27） | **覆盖率闭环**(Coverage Parser 验证覆盖真提升)、QA 保留判断、按文件级小步推进、覆盖率增加≠断言有效 | qa-unit-tdd / qa-mutation / qa-coverage(T-04) | T-04 增强 |

**取舍判断**：
- **强采纳（直接补 V9/V10 痛点）**：W2 永真断言+步骤对照、W9 假通过治理+能力探针、W10 覆盖率闭环、W7 三级推导+领域插槽、W6 六维度、W8 五类样本+判定规则——均命中 V10 评审 P1/P2 或 V9 残留缺陷。
- **弱采纳/演进**：W1 本地模型私有化、W4 入门向触发词（并入 S-04）、W3 Run 对象（作为 A-01 增强而非重写）。
- **不采纳**：纯营销/重复概念（如"Skill=工作说明书"已在 V9 落实）、与"治理编排层"定位冲突的"真跑执行器"诉求（保留为产品路线选择，见 §4）。
