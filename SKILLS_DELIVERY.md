# WorkBuddy 全栈测试技能套件 — 功能介绍与使用手册（甲方交付版）

> 文档版本：V10（治理一致性收口版）+ 验收整改补丁 · 生成日期：2026-08-11（验收整改 2026-08-13） · 适用范围：WorkBuddy 平台（内核兼容 Anthropic Agent Skills 开放标准，可跨 agent 安装）
> 技能总量：**40 个**（38 个传统 QA 生命周期技能 + 2 个 Agent 测试专属技能）。**依赖分层（诚实声明）**：零第三方依赖 **36 个技能**（治理/编排层 34 + Agent 测试层 2，均为纯标准库）；执行层 **4 技能**（qa-api-runner / qa-report / qa-test-case-gen / qa-ui-automation）需运行时依赖，详见 §8.1。各技能 `runtime_dependencies` 以 `SKILL.md` frontmatter 声明、由 `build_registry.py` 派生进 `REGISTRY.json` 单一真相源（已补齐此前漏派生的字段）。

---

## 文档信息

| 项 | 内容 |
|---|---|
| 套件名称 | WorkBuddy QA Skills（全栈测试技能套件） |
| 交付形态 | `skills/` 技能目录 + 安装脚本 + 本手册 |
| 运行环境 | WorkBuddy（已内置 Python 3.13 托管运行时）；治理/编排层零第三方依赖，执行层 4 技能需运行时依赖（见 §8.1） |
| 质量保障 | 全量脚本 `py_compile` 通过；自测 **120/120**（含 R-27 功能用例 + 负向/门禁/横切/一致性/方法论回归用例 + P1×9 整改新增 7 条回归）；六道闸 **全绿**；漂移检查 **无漂移**；注册中心 **40** 技能（36 零依赖 + 4 执行层需依赖）；跨 agent 校验 **PASS**（40 技能 / 80 脚本 name/description/license 齐全、零 `lib/` 引用、零编译失败） |
| 配套文档 | `README.md`、`docs/ADR.md`（架构决策）、`docs/DEPENDENCY_GRAPH.md`（依赖图）、`references/signal-schema.md`（信号契约） |

---

# 上篇：功能介绍

## 1. 产品定位与价值

本套件是一套**轻量的、覆盖完整 QA 生命周期的测试技能系统**，目标是在 WorkBuddy 中把"从需求到归档"的测试活动标准化、可编排、可门禁化。

**解决的核心痛点**

- **测试资产散落**：用例、报告、缺陷常丢在临时聊天里，不可追溯。→ 每轮变更建立标准化产物树，强制落盘。
- **重复造轮子**：每个测试类型都从零写脚本。→ 38 个成熟技能直接复用，编排器只做路由。
- **门禁形同虚设**：发布靠人工判断。→ 数据驱动硬门禁，质量信号 `blocking=true` 即 `sys.exit(1)`。
- **扩维度要改代码**：新增质量维度（如无障碍、视觉回归）需改门禁逻辑。→ 信号契约解耦，新增维度零改门禁。

**适用对象**

- 测试负责人：用 `qa-orchestrator` 规划一轮变更、跟踪进度、卡发布门禁。
- 测试工程师：按路由表选用对应技能（接口/UI/性能/安全/探索/兼容/移动）产出标准化产物。
- 工程效能 / DevOps：把信号契约接入 CI，实现质量门禁自动化。
- AI 应用团队：用 `qa-agent-eval` / `qa-agent-security` 评测自家 Agent 的能力与安全性。

## 2. 设计哲学与关键约束

| 原则 | 含义 | 对甲方的价值 |
|---|---|---|
| **轻量技能** | 每个技能 = `SKILL.md` + `scripts/` + `references/`；治理/编排层零第三方依赖（纯标准库），执行层 4 技能按需 `runtime_dependencies` | 即装即用；治理层无 `pip install`、无环境冲突、无供应链风险 |
| **可追溯优先** | 每轮变更建立标准化产物目录，禁止产物进临时聊天 | 交付审计可追溯、可复盘、可还原 |
| **路由而非重做** | `qa-orchestrator` 只做编排与落盘，逻辑下沉到子技能 | 单一事实源，改一处全局生效 |
| **数据驱动硬门禁** | 发布门禁消费真实产物 + `signals/` 质量信号，任一 `blocking` → 退出码 1 | 门禁不可绕过、可自动化 |
| **信号契约解耦** | 质量技能写 `signals/<skill>.json`，门禁聚合 | 新增质量维度无需改门禁代码 |
| **诚实边界** | 能力边界（如"不做像素级比对""不做键盘可达性"）在 SKILL.md 显式标注 | 不夸大、不假绿，甲方对能力有准确预期 |

> **与"平台化"的边界（重要）**：本套件是**技能集合**，不是测试平台。它不提供集中式调度、分布式执行、数据库存储或 Web 控制台（这些属于用户另一个独立项目 `agent-eval-v2` 的范围）。本套件的所有产物以**文件**形式落盘，可被任意 CI / 平台消费。

## 3. 能力全景图

### 3.1 八阶段生命周期地图

```mermaid
flowchart TD
    S1[01 需求结构化<br/>qa-req-spec] --> S2[02 需求分析+测试点<br/>qa-test-analysis]
    S2 --> S3[03 用例设计<br/>qa-test-case-gen]
    S3 --> S4[04 测试数据+环境<br/>qa-test-data · qa-env-config]
    S4 --> S5[05 接口文档<br/>qa-api-doc]
    S5 --> S6[06 执行<br/>API/UI/性能/安全/探索/兼容/移动]
    S6 --> S7[07 报告+缺陷+上线<br/>qa-report · qa-bug-* · qa-release-check]
    S7 --> S8[08 归档+CI+策略<br/>qa-archive · qa-ci · qa-test-strategy]

    subgraph EXEC[06 执行阶段可路由技能]
        E1[qa-api-runner] ~ E2[qa-ui-automation]
        E3[qa-perf-locust] ~ E4[qa-perf-jmeter]
        E5[qa-security-scan] ~ E6[qa-exploratory]
        E7[qa-compat-matrix] ~ E8[qa-api-contract]
        E9[qa-mobile-autotest] ~ E10[qa-perf-design]
        E11[qa-ui-testid] ~ E12[qa-ui-kb] ~ E13[qa-execution]
    end

    subgraph CROSS[横切关注点 贯穿全周期]
        C1[qa-risk-based] ~ C2[qa-test-strategy]
        C3[qa-ci] ~ C4[qa-mutation]
        C5[qa-flaky-detect] ~ C6[qa-a11y]
        C7[qa-visual-regression] ~ C8[qa-unit-tdd]
        C9[qa-chaos] ~ C10[qa-code-review]
        C11[qa-synthetic-monitoring]
    end
```

**阶段明细表**

| 阶段 | 目录 | 主技能 | 备选/关联技能 | 产出产物 |
|---|---|---|---|---|
| 01 需求结构化 | `01-requirement` | `qa-req-spec` | — | `requirement.md` / `reqs.json` |
| 02 需求分析 | `02-analysis` | `qa-test-analysis` | — | `analysis.md` / `testpoints.md` |
| 03 用例设计 | `03-cases` | `qa-test-case-gen` | — | `cases.xlsx` / `cases.xmind` / `cases.json` |
| 04 测试数据+环境 | `04-testdata` | `qa-test-data` | `qa-env-config` | `data.csv` / `.env` / `testdata.json` |
| 05 接口文档 | `05-api` | `qa-api-doc` | — | `api-doc.md` / `openapi.json` |
| 06 执行 | `06-execution` | `qa-api-runner` | `qa-ui-automation` `qa-perf-locust` `qa-perf-jmeter` `qa-security-scan` `qa-exploratory` `qa-compat-matrix` `qa-api-contract` `qa-mobile-autotest` `qa-perf-design` `qa-ui-testid` `qa-ui-kb` `qa-execution` | `results.json` / `locustfile.py` / `plan.jmx` / `report.md` / `security_findings.json` |
| 07 报告+缺陷+上线 | `07-report` | `qa-report` | `qa-perf-analysis` `qa-security-report` `qa-bug-report` `qa-bug-verify` `qa-release-check` | `test-report.md` / `bug_report.json` |
| 08 归档+CI+策略 | `08-archive` | `qa-archive` | — | `archive.zip` / `ci.yaml` / `test-strategy.md` |

### 3.2 横切关注点（11 技能，贯穿全周期）

> 注：tier 以 `REGISTRY.json` 为唯一真相源（由 `build_registry.py` 从各 SKILL.md `metadata.tier` 派生，`check_drift` 规则守护一致性），下表与 REGISTRY 逐项一致。T1=执行级（有脚本 + references，开箱即用）；T2=治理级（规格治理门禁，仅校验规格完整性，不实际执行故障注入 / 探测 / 扫描）。

| 技能 | 提供的质量门禁 / 能力 | tier（源 `REGISTRY.json`） |
|---|---|---|
| `qa-risk-based` | 基于风险量化（Impact×Probability）定测试密度 | T1（执行级） |
| `qa-test-strategy` | 测试计划 / 策略（范围、类型覆盖、准入准出） | T1（执行级） |
| `qa-ci` | 生成 GitHub Actions / GitLab CI / Jenkinsfile 流水线 | T1（执行级） |
| `qa-mutation` | 变异分数门禁（衡量测试"杀缺陷"真实能力） | T1（执行级） |
| `qa-flaky-detect` | 不稳定测试（flaky）检测门禁 | T1（执行级） |
| `qa-a11y` | WCAG 2.1 A 级无障碍静态检查门禁 | T1（执行级） |
| `qa-visual-regression` | 视觉回归（DOM+关键视觉属性）门禁 | T1（执行级） |
| `qa-unit-tdd` | 单元/TDD 方法学健康度门禁（金字塔/覆盖率） | T1（执行级） |
| `qa-chaos` | 混沌实验治理门禁（业务关键实验须受治理，否则阻断） | T2（治理级） |
| `qa-code-review` | 代码评审启发式门禁（硬编码密钥等阻断，其余待处理） | T2（治理级） |
| `qa-synthetic-monitoring` | 合成监控治理门禁（关键旅程须有断言+告警，否则阻断） | T2（治理级） |

### 3.3 Agent 测试专属类（2 技能，不接入 8 阶段路由）

| 技能 | 能力 | tier（源 `REGISTRY.json`） |
|---|---|---|
| `qa-agent-eval` | 评测被测 Agent 能力：Pass@1/Pass^k、工具准确率、规划/记忆/可靠性五维、轨迹崩溃分析、自包含评测任务生成 | T1（执行级） |
| `qa-agent-security` | 对 Agent 做红队评测：提示注入/越权/数据泄露/长程崩溃，ASR + 效用保持率双轴定级 | T1（执行级） |

### 3.4 能力分类速查（按测试类型）

| 测试类型维度 | 涵盖技能 | 方法学广度进度 |
|---|---|---|
| 功能 / 用例 | `qa-req-spec` `qa-test-analysis` `qa-test-case-gen` `qa-test-data` `qa-test-strategy` `qa-risk-based` `qa-exploratory` `qa-execution` `qa-report` `qa-archive` `qa-bug-report` `qa-bug-verify` `qa-release-check` | — |
| 接口 API | `qa-api-doc` `qa-api-runner` `qa-api-contract` | — |
| UI / 移动 | `qa-ui-kb` `qa-ui-testid` `qa-ui-automation` `qa-mobile-autotest` `qa-visual-regression` `qa-a11y` | — |
| **性能 Performance** | `qa-perf-design` `qa-perf-locust` `qa-perf-jmeter` `qa-perf-analysis` | ✅ 已覆盖（1/8） |
| **安全 Security** | `qa-security-scan` `qa-security-report` | ✅ 已覆盖（2/8） |
| **无障碍 Accessibility** | `qa-a11y` | ✅ 已覆盖（3/8） |
| **视觉回归 Visual** | `qa-visual-regression` | ✅ 已覆盖（4/8） |
| **单元/TDD** | `qa-unit-tdd` | ✅ 已覆盖（5/8） |
| **混沌工程 Chaos** | `qa-chaos` | ✅ 已覆盖（6/8，本轮补齐） |
| **代码评审 Code Review** | `qa-code-review` | ✅ 已覆盖（7/8，本轮补齐） |
| **合成监控 Synthetic Monitoring** | `qa-synthetic-monitoring` | ✅ 已覆盖（8/8，本轮补齐） |
| 工程效能 / 质量门禁 | `qa-ci` `qa-mutation` `qa-flaky-detect` `qa-unit-tdd` `qa-env-config` `qa-compat-matrix` | — |
| Agent 测试 | `qa-agent-eval` `qa-agent-security` | — |
| 编排入口 | `qa-orchestrator` | — |

> **方法学广度说明**：测试技术维度共规划 8 类（性能、安全、无障碍、视觉回归、单元/TDD、混沌工程、代码评审、合成监控）。第四轮补齐无障碍、视觉回归、单元/TDD 三类后达 5/8；本轮（第五轮）补齐混沌工程、代码评审、合成监控三类，**已达成 8/8 方法学门禁覆盖**。其中 3 项（混沌工程 / 代码评审 / 合成监控）为**纯治理门禁**（仅校验规格完整性，不实际注入/探测/扫描）、2 项（无障碍 / 视觉回归）为**快照/指标级**校验，其余为执行级；所有方法学技能均接 `signals/` 契约、可接 CI 门禁。详见 §16 边界口径。

## 4. 质量信号契约（门禁接线方式）

每个质量技能在变更工作区写入 `signals/<skill>.json`，结构如下：

```json
{
  "source": "qa-a11y",
  "generated_at": "2026-08-09T22:00:00",
  "signals": [
    {
      "signal": "a11y_violation",
      "severity": "critical",
      "count": 3,
      "blocking": true,
      "detail": "3 处 <img> 缺 alt 文本"
    }
  ]
}
```

**门禁聚合规则**（见 `qa-release-check`）：
- 扫描 `signals/` 目录内全部 `*.json`；
- 任一 `blocking=true` 的信号存在 → 发布门禁失败（`sys.exit(1)`）；
- 全部 `blocking=false` / 无信号 → 放行。

**解耦价值**：新增质量维度（如未来加混沌工程门）只需该技能按 schema 写 `signals/*.json`，`qa-release-check` 无需任何改动即可生效。完整 schema 见 `references/signal-schema.md`。

## 5. trust-tier 成熟度分级

`REGISTRY.json` 中每个技能带成熟度字段，便于甲方区分"可直接用"与"需增强"：

| tier | 含义 | 本套件数量 |
|---|---|---|
| **1** | 有脚本且有 references（最成熟，开箱即用） | 35（含编排器 `qa-orchestrator`） |
| **2** | 规格治理门禁（校验规格完整性，不实际执行故障注入/探测/扫描） | 3（`qa-chaos` / `qa-code-review` / `qa-synthetic-monitoring`） |
| **3** | 文档/轻执行型（方法学/知识库 + 轻量分析，无重执行脚本） | 2（`qa-test-analysis` / `qa-ui-kb`） |

> 字段还包括 `verified_by`、`last_verified`、`orchestrated`（是否纳入 8 阶段路由）。**诚实验证模型（V10 / T-02 收口）**：35 个 tier-1 技能 `verified_by="manual:smoke+ci:run_all_tests"`（人工冒烟 + `tests/run_all_tests.py` 全绿回填，CI 失败则标记 `:fail`）；3 个 tier-2 治理门禁 + 2 个 tier-3 文档技能 `verified_by="pending:see-§7"`（诚实声明"规格校验/文档型，未做真实破坏性执行"，非"未验证=自评"）。`check_drift.py --require-verified` 可在 CI 阶段性严格化——T1 为空即报漂移。

### 5.1 治理 / 编排层专节（零依赖 + 一致性骨架）

本套件**零第三方依赖 36 个技能（治理/编排层 34 + Agent 测试层 2，均为纯标准库）**（即装即用、无 `pip`、无供应链风险），仅 4 个执行层技能（qa-api-runner / qa-report / qa-test-case-gen / qa-ui-automation）按需 `runtime_dependencies`（详见 §8.1）；各技能依赖以 `SKILL.md` frontmatter 声明、`REGISTRY.json` 单一真相源派生（此前 `build_registry.py` 漏派生该字段，已修复，S-08）。在此分层之上，V10 进一步把"一致性"做成了可校验的工程骨架，而非靠人工约定：

- **frontmatter 单一真相源（S-02）**：40 个 `SKILL.md` 的 `metadata.{category,stage,tier}` 与 `REGISTRY.json` 逐字段一致，`build_registry.py` 直读 SKILL.md `metadata` 派生注册中心，不再双源推导；`check_drift` 死链/入口守卫同步覆盖。
- **vendored `_common` 一致性（A-04）**：5 份 vendored `_common.py`（a11y/chaos/code-review/synthetic-monitoring/unit-tdd）**字节完全一致**，导入期含 `schema_version` 自检，消费脚本对 `_common` 缺失/损坏采用 **fail-closed 守卫导入**（`emit_signal`/`read_text` 导入失败即 `exit(2)`，不静默降级）。
- **跨 agent 可发现（S-04）**：40 个 `SKILL.md` 的 `description` 均含「英文触发词（English triggers）」后缀，避免纯中文描述在英文 query 下不可见。
- **引用零死链（S-03）**：`references/` 的 Markdown 链接、显式路径提及、references 内部互引统一做存在性校验，全仓零死链（渐进披露不沦为断链）。
- **四项回归守卫**：上述四点各有一条 `tests/run_all_tests.py` golden 用例（`t_frontmatter_normalized` / `t_en_trigger_words` / `t_manual_verified` / `t_refs_no_deadlink`），随三道 CI 闸必跑，防止一致性回潮。

## 6. 第四轮优化要点（本轮交付差异）

相对第三轮复审（9.4/10），本轮聚焦复审 backlog 的"方法学广度 + 工程化 + 分发 + 手册"四块：

- **D1 方法学补齐**：新增 `qa-a11y`、`qa-visual-regression`、`qa-unit-tdd` 三个方法学技能，方法学广度 **2/8 → 5/8**。
- **D2 工程化**：公共能力下沉为每个技能 `scripts/_common.py` **自包含 vendoring**（统一 `emit_signal`/`load_json`/`wilson_ci` 等），不使用跨目录 `lib/` 包，保证单目录可分解、可独立分发；新增 `tools/gen_deps.py` 生成依赖图；新增 `docs/ADR.md` 记录 8 条架构决策。
- **D3 分发**：新增 `install.sh` / `install.ps1` 安装脚本；`README.md` 分发章节补"安装脚本 / 手动复制 / zip 整包 + 生态路线图"三方式。
- **D4 手册**：即本文档（甲方交付版）。
- **D5 质量保障**：全量 `py_compile` 通过；自测 17/17；漂移检查无漂移（stages=34 / REGISTRY=37）；注册中心重建 37 技能；并修复"qa-ui-kb/qa-ui-testid/qa-execution 未入 06 执行编排"的真实缺口。

### 6.1 方法学最终补齐（5/8 → 8/8，本手册对应轮次）

在第四轮基础上，补齐最后三类方法学技能，使测试技术维度达到 **8/8 全覆盖**：

- **`qa-chaos`（混沌工程治理门）**：校验混沌实验规格是否「受治理」——业务关键实验必须定义稳态假设、终止条件、回退方案、爆炸半径；未受治理的关键实验产出 `blocking` 信号。诚实标注：仅校验规格治理完整性，不实际注入故障（无基础设施依赖）。
- **`qa-code-review`（代码评审启发式门）**：纯标准库扫描源码，识别硬编码密钥（critical/阻断）、SQL 拼接、超长函数、无工单 TODO、遗留调试打印；存在硬编码密钥产出 `blocking` 信号。诚实标注：启发式 linter，非完整 SAST，与 `qa-security-scan` 互补。
- **`qa-synthetic-monitoring`（合成监控治理门）**：校验合成监控旅程规格是否「受治理」——业务关键旅程必须有断言、告警阈值、探测频率；缺失产出 `blocking` 信号。诚实标注：仅校验规格治理完整性，不实际探测生产。

三者均带 fixture + 阻断/放行双场景实测，入 `cross_cutting`，接 `signals/` 契约；自测新增 3 用例后 **20/20 全过**（全量累计至 25/25）；`build_registry.py` → **40 技能**；`check_drift.py` → 无漂移（stages=37 / REGISTRY=40）。

## 7. 五轮复审历程（演进脉络）

| 轮次 | 评分 | 核心主题 | 关键交付 |
|---|---|---|---|
| V1 | 基线 | 技能初建 | 27 传统技能骨架 |
| V2 | 升级 | 深化 + 编排闭环 | 新增 perf-jmeter/exploratory/compat-matrix；orchestrator 重写为 8 阶段闭环路由 |
| V3 | 9.4/10 | 复审 + Agent 类 | 扩 scope 新增 `qa-agent-eval`/`qa-agent-security`；方法学广度仅 2/8 被列为 backlog |
| **V4（本轮）** | 交付版 | backlog 清理 + 甲方手册 | 方法学 5/8、工程化（公共库/依赖图/ADR）、安装脚本、本手册 |
| **V5（本手册轮）** | 交付版 | 方法学全覆盖 + 手册完善 | 补齐 `qa-chaos`/`qa-code-review`/`qa-synthetic-monitoring`，方法学 **8/8**；注册中心 40 技能；自测 20/20；手册更新至 V5 |
| **V6（本轮）** | 复评 9.5+ | 四专家评审回应 + 可移植/诚实化 | 回应 V6 评审（通用性/易用性）：门禁契约唯一权威化（修 P0 假绿）、vendored `_common` 去 `lib/`、frontmatter 归一化、`install --flavor` 跨 agent；编排器输出机器可读 JSON + 失败回退；建 README/MAINTAINERS 降噪；自测 25/25、跨 agent 校验 PASS |
| **V9（本轮验收整改）** | 验收 7.9→9.5+ | 清零甲方验收 P0×4 + P1×9 | 四专家评审（面板 7.9/10，4×P0 + 9×P1）→ 6 阶段 V9 计划逐阶段清零；P0-A/B 编排 fail-closed（max-step+证据硬闸）、P0-C/D 红队多轮 harness+stub 防呆、P1-2/5 文档"零依赖"清零+契约语义、P1-1/4/6 信任证据回填+信号 SSOT(19 处字节一致)+两 agent 接入信号、P1-3/7/8 生成器行为测试+checkers 强制 fail-closed+指标 bootstrap 置信带/小样本告警、P1-9 横切调度；三道闸 **64/64**、drift 0、portability 40/72 全过 |
| **V10（治理一致性收口）** | 收口 | frontmatter SSOT + 引用零死链 + 跨 agent 发现 + 一致性回归 | S-02 frontmatter 归一化（40 技能 metadata 与 REGISTRY 单源）、S-03 references 零死链（check_drift 规则11 + golden 复跑）、S-04 英文触发词全覆盖（40/40）、A-04 vendored `_common` 五份字节一致 + fail-closed 守卫导入、T-02 verified_by 诚实模型（35×T1 `manual:smoke+ci` / 5×T2·T3 `pending`）；新增四条 golden 后自测 **93/93**、drift 0、portability **40/79** 全过（计划 `UPGRADE_PLAN_V10.md`，复评 `CONSOLIDATED_REVIEW_V13.md`） |
| **V11（验收整改）** | 验收 9.5+ 冲刺 | P1×9 全闭环 + P2 诚实化 + 自测口径统一 | T-01 Markdown 空壳 fail-closed、S-01/S-02/S-03 references 零死链（REF_RE 反引号盲点修复 + 仓库根回退）、AR-01/AR-02 信号落点 CWD 无关（`--out` 绝对化）、AG-01 作用域 bug、AG-02 macro bootstrap 95%CI、AG-03 Unicode/casefold 归一；S-07 自测数字统一 120/120、S-08 依赖口径含 2 Agent、S-04 安装交付范围澄清、`build_registry` 补齐 `runtime_dependencies` 派生；六道闸全绿、自测 **120/120**（新增 7 条回归） |

**已知未决项（诚实披露）**
- 分发仍为 zip/复制 + 安装脚本，下一轮评估 MCP server 或 `skills add` 兼容包（ADR-007）。
- **诚实验证模型（V10/T-02 收口）**：35 个 tier-1 技能 `verified_by="manual:smoke+ci:run_all_tests"`（人工冒烟 + 自测全绿回填，CI 失败标 `:fail`）；3 个 tier-2 治理门禁 + 2 个 tier-3 文档技能 `verified_by="pending:see-§7"`（诚实声明"规格校验/文档型，未做真实破坏性执行"）。甲方可据 REGISTRY.json 逐项追溯（详见 §5.1）。
- 各质量技能的 `blocking` 阈值（如 flaky 率、变异分数、覆盖率、混沌治理要素）采用内置默认值，甲方应按自身 SLA 调参。
- tier-2 的 3 个规格治理门禁（`qa-chaos` / `qa-code-review` / `qa-synthetic-monitoring`）的 `references/` 文档已补齐（检查项/阈值/CLI/常见坑），并在 §16 诚实标注"仅校验规格完整性，不实际注入故障/探测生产/解析 AST"。
- `qa-chaos`/`qa-code-review`/`qa-synthetic-monitoring` 为**规格治理门禁**，仅校验规格完整性，不实际注入故障/探测生产/解析 AST（已在 §16 标注）。

---

# 下篇：使用手册

## 8. 环境要求

- **平台**：WorkBuddy（技能由平台加载执行）。
- **运行时**：内置 Python 3.13（已托管）。**零第三方依赖 36 技能（治理/编排 34 + Agent 测试 2）纯标准库，无需 `pip install`；执行层 4 技能需运行时依赖，见 §8.1**。
- **系统**：Windows / macOS / Linux 均可（安装脚本提供 bash 与 PowerShell 双版本）。

### 8.1 执行层 runtime_dependencies（pip 安装清单）

治理/编排层 34 个技能为零依赖纯标准库，直接运行。以下 **4 个执行层**技能需要运行时第三方依赖，请按需在目标环境安装：

| 技能 | 运行时依赖 | 安装命令 |
|---|---|---|
| `qa-api-runner` | requests / mysql-connector-python / allure-pytest | `pip install requests mysql-connector-python allure-pytest` |
| `qa-report` | openpyxl | `pip install openpyxl` |
| `qa-test-case-gen` | openpyxl | `pip install openpyxl` |
| `qa-ui-automation` | playwright | `pip install playwright && playwright install` |

> 每个技能的 `runtime_dependencies` 字段已在 `REGISTRY.json` 中声明；CI 的 `validate_portability.py` 据此校验"第三方 import 均有声明"，杜绝未声明的隐式依赖。

## 9. 安装与分发

### 方式一：安装脚本（推荐）

仓库根提供跨平台安装脚本，自动把整套 `skills/` 复制到目标 WorkBuddy 技能目录：

```bash
# macOS / Linux（Git Bash）
./install.sh --flavor generic                                # 装到 ./skills（通用/任意 agent）
./install.sh --flavor claude                                 # 装到 ./.claude/skills（Claude/Cursor 等）
./install.sh --target /path/to/project/.workbuddy/skills    # 显式指定（WorkBuddy 项目级）

# Windows（PowerShell）
.\install.ps1 -Flavor generic
.\install.ps1 -Target D:\path\to\project\.workbuddy\skills
```

> **注意（R-10）**：默认 `flavor=workbuddy` 会把技能装到 `./.workbuddy/skills`，与源目录相同，安装脚本会主动拦截并提示改用 `--flavor` 或 `--target`，避免原地复制失败。跨 agent 安装用 `--flavor generic` / `--flavor claude` 即可。

### 方式二：手动复制

将 `skills/` 目录整体复制到 WorkBuddy 技能目录：
- **项目级**：`<workspace>/.workbuddy/skills/`（仅当前项目生效）
- **用户级**：`~/.workbuddy/skills/`（跨项目生效）

复制后刷新技能列表即可。**治理/编排层技能无需 pip；执行层 4 技能按其 `runtime_dependencies` 安装依赖（见 §8.1）。**

### 方式三：整包分发（zip）

将 `skills/` 目录打包为 zip 交付；甲方解压后通过方式一或方式二落位。仓库根提供 `make_dist.sh`（R-21）自动产出**干净分发包**——显式排除 `.git` / `.tmp_test_phase5` / `node_modules` / `__pycache__` / `*.pyc` / 内部维护评审过程稿（`.workbuddy/skills/reviews/`，根目录 `reviews/` 亦不随包）；**保留 `tools/` 验收闸门与 `tests/` 自测**——因自测套件 `run_all_tests.py` 依赖 `tools/validate_portability.py`，甲方需能独立复跑完成签字验收。仅保留技能目录与交付文档：

```bash
./make_dist.sh                       # 输出 dist/qa-skills-<日期>.zip
./make_dist.sh --out /tmp/bundle.zip # 显式指定输出路径
```

> **生态路线图**：当前为 zip / 复制分发；下一轮评估 MCP server 或 `skills add` 兼容包，实现"一条命令安装 + 跨平台 + 版本管理"（详见 `docs/ADR.md` ADR-007）。

> **验收范围说明（S-04 澄清）**：`install.sh` / `install.ps1` 产出的**精简分发包**会刻意剔除维护类文件（`REGISTRY.json` / `build_registry.py` / `check_drift.py` / `tools/`），以实现 lean-ship；而 §17 所列交付物与甲方**验收（签字）须基于完整源码树**（保留 `REGISTRY.json` 与全部验收闸门），二者口径不同、并非矛盾。本手册所有"自测 120/120 / 六道闸全绿"均指完整源码树上的复跑结果。

## 10. 快速上手：编排闭环

`qa-orchestrator` 是入口，把一轮变更标准化并路由到各子技能。

**典型对话流**

```
用户：开始一轮测试（附需求/PRD）
  → qa-orchestrator 建立变更产物目录，推荐从 qa-req-spec 开始

用户：下一步用什么技能？
  → qa-orchestrator 的 route_next.py 按 stages.json 推荐下一阶段技能

用户：一键推进全流程
  → qa-orchestrator 的 close_loop.py 顺序驱动 8 阶段（人工确认节点暂停）
```

**产物目录约定**（每轮变更）

```
<change_workspace>/
├── 01-requirement/   requirement.md
├── 02-analysis/      testpoints.md
├── 03-cases/         cases.xlsx
├── 04-testdata/      data.csv  .env
├── 05-api/           api-doc.json
├── 06-execution/     results.json  signals/
├── 07-report/        test-report.md  bug_report.json
└── 08-archive/       archive.zip
```

> **R-25 工作目录（CWD）约定（统一声明）**：所有脚本均以**技能根目录**（含 `qa-*/` 的目录，即仓库根或 `skills/`）为当前工作目录调用，形如 `python qa-xxx/scripts/xxx.py ...`。脚本内部一律用相对路径读写产物与 `signals/` 目录，不依赖绝对路径；请勿在子目录内直接 `python xxx.py` 调用（会导致 `signals/` 与相对引用错位）。`--signals-dir` 可覆盖默认输出位置。

## 11. 典型工作流（场景化）

### 11.1 接口自动化全流程

`qa-api-doc`（拉取 Swagger）→ `qa-api-runner`（执行场景，支持串联变量与 DB 双校验）→ `qa-api-contract`（改接口时卡破坏性变更）→ `qa-report`（汇总）。

```bash
# 文档（Markdown + JSON 双落盘）
python qa-api-doc/scripts/swagger_fetch.py --url https://api.example.com/openapi.json --output 05-api/api-doc.md --save-json 05-api/api-doc.json
# 执行（产物写入目录）
python qa-api-runner/scripts/run.py --scenario 06-execution/scenario.json --outdir 06-execution
# 契约（新旧对比，阻断破坏性变更并写信号）
python qa-api-contract/scripts/contract_diff.py --old old.json --new new.json --signals-dir signals --fail-on
```

### 11.2 UI 自动化闭环

`qa-ui-kb`（沉淀页面知识库）→ `qa-ui-testid`（扫描补 `data-testid` 稳定选择器）→ `qa-ui-automation`（生成 Playwright Page Object + 冒烟）→ `qa-visual-regression`（视觉回归门禁）→ `qa-a11y`（无障碍门禁）。

### 11.3 性能压测

`qa-perf-design`（设计负载/压力/疲劳/尖峰场景）→ `qa-perf-locust` 或 `qa-perf-jmeter`（生成脚本/jmx）→ `qa-perf-analysis` 或 `qa-perf-jmeter` 的 analyze（吞吐/P95/P99/错误率/SLA 判定）。

### 11.4 安全测试

`qa-security-scan`（OWASP 清单 + ZAP/SAST/依赖 CVE 指引 + 本地密钥/PII 泄露扫描）→ `qa-security-report`（归一化风险评级 Critical/High/Medium/Low/Info）。

### 11.5 发布门禁

`qa-release-check` 扫描 `signals/` 全部 `*.json`，任一 `blocking=true` → `sys.exit(1)` 阻断发布；并通过 `qa-archive` 归档整轮产物。

```bash
python qa-release-check/scripts/gen_release_checklist.py \
    --release release.json --signals-dir 06-execution/signals \
    --out 07-report/release-checklist.md --fail-on
echo $?   # 0=放行, 1=阻断
```
> `release.json` 为发布元数据（version / env / services / 冒烟结果 / 监控 / 人工确认布尔），字段说明见 `qa-release-check` 技能。门禁唯一权威：**任一 `blocking=true` 信号即 exit 1**。

### 11.6 韧性 / 评审 / 可观测性治理门禁

本轮新增的三个方法学技能均为**规格治理门禁**，建议在「合并前 / 发布前」接入：

- **混沌工程治理**（`qa-chaos`）：在故障演练前校验实验规格是否受治理，未治理的关键实验阻断。
  ```bash
  python qa-chaos/scripts/chaos_gate.py --spec chaos.json --out signals --fail-on
  ```
- **代码评审门禁**（`qa-code-review`）：在 PR 合并前扫描硬编码密钥等反模式，命中密钥阻断。
  ```bash
  python qa-code-review/scripts/review_scan.py --src ./src --out signals --fail-on
  ```
- **合成监控治理**（`qa-synthetic-monitoring`）：在监控上线前校验关键旅程是否具备断言+告警，未治理阻断。
  ```bash
  python qa-synthetic-monitoring/scripts/monitor_gate.py --spec monitor.json --out signals --fail-on
  ```

三者与 §12 的 CI 门禁机制一致：任一 `--fail-on` 即退出码 1，CI 自动标红；不实际注入故障 / 不实际扫描生产 / 不实际发起探测，仅治理规格。

## 12. CI 门禁接线

把信号契约接进 CI，实现质量门禁自动化。以 GitHub Actions 为例（亦可用 `qa-ci` 生成 GitLab/Jenkins 配置）：

```yaml
# .github/workflows/qa-gate.yml
name: QA Gate
on: [push, pull_request]
jobs:
  qa:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.13" }
      - name: Run quality skills
        run: |
          python qa-a11y/scripts/a11y_check.py --in web/ --signals-dir signals --fail-on
          python qa-unit-tdd/scripts/unit_health.py --metrics metrics.json --signals-dir signals --fail-on
          python qa-release-check/scripts/gen_release_checklist.py --release release.json --signals-dir signals --out qa-gate.md --fail-on
      # 任一 blocking 即 exit 1，CI 自动标红
```

**门禁维度一览**（均通过 `signals/*.json` 的 `blocking` 字段生效）

| 门禁 | 触发阻断的条件 |
|---|---|
| 接口契约 | 检测到破坏性 API 变更 |
| 无障碍 | 存在 WCAG 2.1 A 级违规 |
| 视觉回归 | 存在布局级 DOM/视觉属性回归 |
| 单元/TDD | 测试金字塔倒挂 / 覆盖率或失败数不达标 |
| 变异测试 | 变异分数低于阈值 |
| flaky 检测 | flaky 率超过阈值 |
| 发布检查 | `signals/` 内存在任一 `blocking=true` |

## 13. 扩展新质量维度（零改门禁）

若甲方要新增质量维度（如"代码评审门禁"）：
1. 新建 `qa-xxx/SKILL.md` 与 `scripts/xxx.py`；
2. 脚本按 `references/signal-schema.md` 写入 `signals/qa-xxx.json`（`blocking` 按需置真）；
3. 在 `stages.json` 的 `cross_cutting` 或对应阶段 `alternates` 追加该技能；
4. 运行 `build_registry.py` 与 `check_drift.py` 刷新并校验一致性。

`qa-release-check` 无需任何改动即可消费新信号。

## 14. 单人接手与运维指南

维护者命令（编译体检 / 自测 / 刷新注册中心 / 漂移校验 / 加新技能 / 发布分发）已统一抽到 **[`MAINTAINERS.md`](.workbuddy/skills/MAINTAINERS.md)**，避免本手册随维护细节频繁变动；此处仅保留使用者需要了解的原则。

> **单一事实源**：`stages.json` 是编排的唯一事实源；`REGISTRY.json` 是技能注册中心；二者与 `SKILL.md` 路由表须保持一致，`check_drift.py` 为 CI 卡点。

**公共代码约定**：每个带脚本的方法学技能在 `scripts/_common.py` **自包含**公共能力（`emit_signal` / `load_json` / `save_json` / `read_text` / `wilson_ci` / `two_prop_z`）。刻意采用 vendoring 而非跨目录 `lib/` 包，以保证每个技能目录可单目录分解、可独立分发（详见 MAINTAINERS.md §2）。

**轻量上手**：普通使用者无需读本节——直接调用任意技能即可，见 **[`README.md`](README.md)** 三步上手与分层采用套餐。

## 15. 常见问题 FAQ

| 问题 | 解答 |
|---|---|
| 需要装什么依赖吗？ | 零第三方依赖 36 个技能（治理/编排 34 + Agent 测试 2）纯标准库、无需安装；执行层 4 个技能（qa-api-runner / qa-report / qa-test-case-gen / qa-ui-automation）需按需安装运行时依赖，见 §8.1。 |
| 门禁误杀怎么办？ | 各技能 `blocking` 阈值有内置默认，可按甲方 SLA 调参（如覆盖率阈值、flaky 率）。 |
| 能接我们现有 CI 吗？ | 能。信号契约是文件，任意 CI 读 `signals/*.json` 判断 `blocking` 即可；也可用 `qa-ci` 生成配置。 |
| 技能能离线跑吗？ | 能。无联网依赖；唯一例外是 `qa-api-doc` 拉取远程 Swagger 时可改用本地 JSON。 |
| 和测试平台冲突吗？ | 不冲突。本套件产出文件，可被任意平台消费，不替代平台。 |

## 16. 能力边界与诚实声明（务必阅读）

> **本包定位：治理编排层（Governance & Orchestration Layer），不是测试执行器（Test Executor）。** 核心交付是「标准化测试活动 + 路由编排 + 信号门禁 + 诚实边界」；凡涉及真实注入/扫描/渲染/探测的环节，均**显式标注为治理门禁并预留专业工具接口**——真实执行须接入 mutmut/cosmic-ray（变异）、Chaos Mesh/Litmus（混沌）、axe-core/pa11y（a11y）、Percy/Chromatic（视觉回归）、Semgrep/ZAP（代码/安全）、黑盒监控/ATS（合成监控）。甲方验收请按此口径，避免"治理门禁"被误读为"已跑过真实测试"。

为不误导甲方，以下能力边界在对应 SKILL.md 中已显式标注：

- **qa-mutation（变异测试分数）**：**治理门禁**——消费变异工具(mutmut/cosmic-ray/pit)已有产出、计算并门禁变异分数；**不注入变异体、不执行测试套件**。真实变异注入须接专业工具。
- **qa-a11y（无障碍）**：仅做 WCAG 2.1 **A 级静态检查（治理门禁）**，扫描源码/标记识别违规，**不实际在浏览器渲染、不调用 axe-core 等渲染引擎**；真实渲染级校验须接 axe-core/pa11y。
- **qa-visual-regression（视觉回归）**：**治理门禁**——对比已落盘快照做结构/布局断言，**不截图、不调浏览器**；真实像素级 diff 须接 Percy/Chromatic。
- **qa-unit-tdd（单测方法学）**：基于指标（金字塔占比/覆盖率/失败数/测试比）做**方法学健康度门禁**，不替代单测框架本身。
- **qa-api-runner / qa-ui-automation 等**：生成配置驱动的执行脚本与产物，**执行依赖被测系统可达**（目标服务/浏览器需就绪）。
- **qa-agent-eval / qa-agent-security**：评测**被测 Agent 自身**，不是评测业务系统；ASR 等统计基于提供的运行样本。
- **qa-chaos（混沌工程）**：仅校验混沌实验**规格的治理完整性**，不实际对目标系统注入任何故障（无基础设施/网络依赖）；真实注入须配合 Chaos Mesh/Litmus 等在受控环境执行。
- **qa-code-review（代码评审）**：是**启发式静态检查（治理门禁）**（正则扫描），不解析 AST、不理解数据流/语义，误报漏报均可能；与 `qa-security-scan`（ZAP/Semgrep/Trivy）互补而非替代。
- **qa-synthetic-monitoring（合成监控）**：仅校验监控**规格的治理完整性**，不实际对生产/预发发起探测（无网络依赖）；真实探测由黑盒监控/ATS 在受控环境执行。
- **公共库与脚本**：均为确定性逻辑，**不涉及模型推理**；AI 能力来自 WorkBuddy 平台加载 SKILL.md 后的规划执行。

### 验收口径与 `verified_by` 语义（R-16）
- 甲方验收的**唯一判定依据**是：自测套件 **真实通过（当前基线 120/120，含 P1×9 整改新增 7 条回归用例）** + 各技能 **fixture 实测**，而非任何"声明达标"。历史轮次自测为各时点快照：V4 17/17、V5 25/25、V10 93/93、V11 验收整改 120/120。
- `REGISTRY.json` 中信任分级的 `verified_by` 字段**仅作来源标注**（如 `manual:smoke`、`ci`、`pending`），表示"该成熟度等级的核实方式/来源"，**不代表已自动跑通、也不构成验收结论**。高阶（T2/T3）技能显式标 `pending` 即诚实暴露"尚未实测"，不虚标成熟度。
- 任何"通过 / 达标"结论，必须以可复跑的脚本产物（信号 JSON / fixture 实测输出）为准，不得仅凭文档声明。

### 执行就绪清单（依赖 + 可达性）（R-18）
在调用任一**执行层 / 真实执行类**技能前，请先确认以下就绪项，避免"脚本就位但跑不起来"：
1. **依赖就绪**：执行层 4 技能（qa-api-runner / qa-report / qa-test-case-gen / qa-ui-automation）已按 §8.1 安装运行时依赖（requests / openpyxl / playwright 等）；第三方 import 须与 `REGISTRY.json` 的 `runtime_dependencies` 声明一致（`validate_portability.py` 会校验，未声明即阻断）。
2. **目标可达**：接口 / UI / 性能 / 安全类执行依赖**被测系统可达**（服务地址、认证凭证、浏览器驱动、网络连通性已就绪）；治理 / 编排层 34 技能纯标准库、无外部依赖、无需可达性检查。
3. **产物落盘**：执行产物目录（如 `changes/<slug>/06-execution/`）已创建且可写；门禁信号将写入 `signals/<skill>.json`。
4. **编排态**：用 `qa-orchestrator` 推进时，确认 `stages.json` 阶段目录与 `change_meta.json` 的 `qa_required` 声明一致（避免 P0-B 证据硬闸误判）。

## 17. 交付清单

| 交付物 | 路径 | 状态 |
|---|---|---|
| 技能套件（40 技能） | `skills/`（即 `.workbuddy/skills/`） | ✅ |
| 安装脚本 | `install.sh` / `install.ps1` | ✅ |
| 注册中心 | `skills/REGISTRY.json`（40 技能 + trust-tier） | ✅ |
| 架构决策 | `skills/docs/ADR.md`（ADR-001~008） | ✅ |
| 依赖图 | `skills/docs/DEPENDENCY_GRAPH.md` | ✅ |
| 信号契约 | `skills/references/signal-schema.md` | ✅ |
| 公共代码 | `skills/*/scripts/_common.py`（vendored，5 份字节一致 + schema_version 自检 + 消费端 fail-closed 守卫导入，无 lib/ 跨目录依赖） | ✅ |
| 自测套件 | `skills/tests/run_all_tests.py`（120/120 通过，含一致性/门禁/横切/方法论回归 golden + P1×9 整改回归） | ✅ |
| 维护者文档 | `skills/MAINTAINERS.md`（命令/加技能/发布流程） | ✅ |
| 轻量上手文档 | `README.md` / `skills/README.md`（三步上手 / 跨 agent 安装 / 分层采用） | ✅ |
| 本手册 | `SKILLS_DELIVERY.md` | ✅ |
| 开源许可 | `LICENSE`（MIT） | ✅ |

---

## 18. 行业对标与能力边界（交付前 11 篇行业文章对标 · 2026-08）

> 交付前，我们对 2026 年主流测试 Agent / AI 评测实践做了 **11 篇行业文章对标**（声明式浏览器 Agent、用例转脚本 Skill、Coding Agent 闭环、Agent 六维评测、AliExpress 测试体系、Cover-Agent、loop-me 工程纪律等）。结论：**本系统的方法学广度（需求→归档 8 阶段 + 11 横切 + Agent 测试）已覆盖其核心方法论**，全文见 `INDUSTRY_BENCHMARK_PRE_ACCEPTANCE.md`。

**为何本系统是"治理编排层"而非"测试执行器"（Conscious 的能力上限）**

- **我们刻意止于治理/编排层**：不实际驱动浏览器、不实际注入故障/探测生产/渲染比对（逐项边界见 §16）。这是**设计取舍**，不是能力缺失。
- **竞品对照（只对标、不落地）**：行业里确有"让 Agent 真实驱动 Playwright 浏览器 / 真实点击执行"的实践（如 LangChain+Playwright 声明式测试 Agent、AliExpress Agent 自规划执行）。这类**真实执行型**方案与本系统 §16 边界**正面冲突**——一旦落地会破坏 `qa-ui-automation`/`qa-execution` 的治理定位并触发零依赖校验失败，故**仅作能力边界参考，绝不转化为 skill 能力**。
- **边界合理性佐证**：行业实践本身也印证"治理/编排优先"更稳——如"Coding Agent 闭环"主张 MCP 协议层不能代替运行架构、"Agent 自规划"主张"能用函数别让 AI 点""Agent 价值上限 20%"。这些原则**恰支持**本系统把真实执行交给专业工具、自身只做编排与门禁的定位。

**交付口径建议**：若甲方问"为什么不直接帮我跑浏览器/做真实注入"，按 §16 + 本节口径回应——我们以文件化产物 + 信号门禁 + 诚实边界交付可审计、零依赖、可移植的测试治理层；真实执行由甲方既有 Playwright/ZAP/Chaos Mesh 等工具在受控环境接管。

---

*结语：本套件以"轻量、可追溯、可门禁、诚实标注边界"为设计底线，已覆盖完整 QA 生命周期与 **8/8 测试技术维度**（性能/安全/无障碍/视觉回归/单元-TDD/混沌工程/代码评审/合成监控）。甲方可直接用于接口/UI/性能/安全/探索/兼容/移动测试，及 Agent 能力与安全评测；剩余分发增强（MCP）与 verified_by 冒烟见 §7 路线图。*
