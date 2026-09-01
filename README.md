# 通用测试技能套件（Universal QA Skills）

> 一套**轻量、零依赖、可独立调用**的 QA 测试技能集合，覆盖「需求 → 分析 → 用例 → 数据/环境 → 接口文档 → 执行 → 报告/缺陷/发布 → 归档」完整生命周期，外加 11 项横切质量门禁与 2 个 AI Agent 测试专属技能。**共 40 个技能**，内核符合 [Anthropic Agent Skills 开放标准](https://docs.anthropic.com/en/docs/agents-and-tools/agent-skills)，可在任意支持该标准的 agent（Claude Code / Cursor / Codex / WorkBuddy 等）上加载。

---

## 一键安装

```bash
# 在「目标项目」根目录执行，指向本仓库的安装脚本（默认 flavor=generic，装到 ./skills）
/path/to/test-skills/install.sh

# 其他宿主
/path/to/test-skills/install.sh --flavor claude    # → ./.claude/skills
/path/to/test-skills/install.sh --flavor workbuddy # → ./.workbuddy/skills
```

> 装，本质上就是「把技能文件夹复制过去」。安装后重新加载宿主 agent，直接在对话里说需求即可调用，无需理解编排器或 CI。

---

## 它解决什么问题

- **通用**：技能 = 一份 `SKILL.md` + 几个 Python 脚本，符合开放标准，跨 agent 安装，不绑定任何平台。
- **轻量**：治理/编排层 36 个技能**零第三方依赖**，纯 Python 标准库即可运行；仅 4 个执行层技能需运行时依赖。
- **可独立调用**：38 个传统 QA 技能彼此不耦合，想用哪个装哪个，不强制全装。
- **有质量门禁**：11 项横切门禁（风险/策略/CI/变异/flaky/无障碍/视觉回归/单测-TDD/混沌/代码评审/合成监控）可挂进 CI 做发布卡点。

---

## 40 技能速查表

### ① 需求 · 需求 → 测试追溯（1）

| 技能 | 一句话能力 | 依赖 |
|---|---|---|
| `qa-req-spec` | 当用户手上是零散、非结构化的原始需求材料（PRD 片段、用户故事、会议记录、 蓝湖/Figma 原型标注文字… | 零依赖 |

### ② 分析 · 测试分析（1）

| 技能 | 一句话能力 | 依赖 |
|---|---|---|
| `qa-test-analysis` | 当已有结构化需求文档（由 qa-req-spec 产出），需要把它拆解成可测项、识别风险与 模糊点… | 零依赖 |

### ③ 用例 · 用例生成（1）

| 技能 | 一句话能力 | 依赖 |
|---|---|---|
| `qa-test-case-gen` | 当用户已有测试点（来自 qa-test-analysis）或需求，希望直接产出可执行的用例文件… | 需：openpyxl |

### ④ 数据/环境 · 测试数据与环境（2）

| 技能 | 一句话能力 | 依赖 |
|---|---|---|
| `qa-env-config` | 当用户搭建或管理接口/UI 自动化的测试环境，需要把多环境配置（base URL、账号、 token… | 零依赖 |
| `qa-test-data` | 当用户需要为执行或自动化准备测试数据时使用——边界值 / 等价类取值、异常输入、 批量造数… | 零依赖 |

### ⑤ 接口文档 · 接口文档（1）

| 技能 | 一句话能力 | 依赖 |
|---|---|---|
| `qa-api-doc` | 当用户需要一份可用的接口规范来驱动接口测试或自动化，却缺少规范文档… | 零依赖 |

### ⑥ 执行 · 测试执行（接口/UI/移动/性能/安全）（13）

| 技能 | 一句话能力 | 依赖 |
|---|---|---|
| `qa-api-contract` | 接口契约测试技能：对比新旧两份 OpenAPI 规范，自动识别破坏性变更（Breaking Change）… | 零依赖 |
| `qa-api-runner` | 当用户已有接口文档（来自 qa-api-doc），需要真正执行接口自动化测试而不只是生成 用例时使用。… | 需：requests/mysql/allure |
| `qa-compat-matrix` | 兼容性测试矩阵生成技能：根据 OS × 浏览器 × 设备 × 分辨率 × 网络 维度配置… | 零依赖 |
| `qa-execution` | 当一个版本需要把多类测试（UI / API / 性能 / 安全）统一编排与跟踪时使用。… | 零依赖 |
| `qa-exploratory` | 探索性测试引导技能：把功能 / 风险点转化为一组结构化测试章程（charter），并给出 HTSM 启发式… | 零依赖 |
| `qa-mobile-autotest` | 移动端 App 自动化测试技能：把「摸清现状→列清单→生成资产→自检→中文交付」整成标准流水线。… | 零依赖 |
| `qa-perf-design` | 当测试工程师需要把需求、NFR 或容量目标翻译成可执行的性能测试方案时使用… | 零依赖 |
| `qa-perf-jmeter` | 性能测试 JMeter 技能（与 qa-perf-locust 平级… | 零依赖 |
| `qa-perf-locust` | 当已有性能测试方案（来自 qa-perf-design），需要生成可直接运行的 Locust 压测脚本时 使用。… | 零依赖 |
| `qa-security-scan` | 当测试工程师需要执行或规划应用安全测试（AST）时使用。本技能提供 OWASP Top 10 人工核查清单… | 零依赖 |
| `qa-ui-automation` | 当已有 UI 知识库（qa-ui-kb）、选择器也已用 data-testid 稳定（qa-ui-testid）… | 需：playwright |
| `qa-ui-kb` | 当用户启动或维护 UI 自动化，需要沉淀一份稳定、可供 AI 读取的被测页面知识库… | 零依赖 |
| `qa-ui-testid` | 当用户希望通过给前端代码批量补加稳定的 data-testid 属性来让 UI 自动化选择器更耐用… | 零依赖 |

### ⑦ 报告/缺陷/发布 · 报告 · 缺陷 · 发布（6）

| 技能 | 一句话能力 | 依赖 |
|---|---|---|
| `qa-bug-report` | 当测试发现缺陷、需要产出结构化缺陷单，或需要提交到 TAPD / 禅道 / Jira 时使用。… | 零依赖 |
| `qa-bug-verify` | 在缺陷（来自 qa-bug-report）修复之后使用，规划并执行验证与回归。本技能生成验证 计划… | 零依赖 |
| `qa-perf-analysis` | 在 Locust 压测（来自 qa-perf-locust）执行完成后使用，把原始 CSV 产物转成可读结论… | 零依赖 |
| `qa-release-check` | 在生产发布前后使用，核验是否具备上线条件：生成上线门禁清单（构建/DB 迁移/配置/ 依赖/回滚方案）… | 零依赖 |
| `qa-report` | 当测试执行完成（功能用例已在 Excel 填好执行结果… | 需：openpyxl |
| `qa-security-report` | 在安全扫描（qa-security-scan）完成之后使用… | 零依赖 |

### ⑧ 归档 · 归档（1）

| 技能 | 一句话能力 | 依赖 |
|---|---|---|
| `qa-archive` | 在一次变更 / 测试周期结束时使用，把全部产物（需求、用例、执行结果、报告、缺陷）… | 零依赖 |

### Ⓣ 横切质量门禁 · 贯穿全流程的质量卡点（11）

| 技能 | 一句话能力 | 依赖 |
|---|---|---|
| `qa-a11y` | 无障碍(WCAG 2.1)静态检查治理门禁：扫描 HTML 源码/标记（不实际渲染… | 零依赖 |
| `qa-chaos` | 混沌工程治理门禁技能：校验混沌实验规格是否「受治理」——业务关键实验必须定义稳态假设、终止条件… | 零依赖 |
| `qa-ci` | 用于生成 CI/CD 流水线配置… | 零依赖 |
| `qa-code-review` | 代码评审启发式门禁技能：纯标准库扫描源码，识别评审期高危反模式——硬编码密钥(critical/阻断)… | 零依赖 |
| `qa-flaky-detect` | 不稳定测试（flaky）检测技能：基于同一测试集的多轮重跑结果，识别「时过时不过」的 flaky 用例… | 零依赖 |
| `qa-mutation` | 变异测试分数治理门禁：本技能**不注入变异体、不运行测试**… | 零依赖 |
| `qa-risk-based` | 基于风险的测试（RBT）量化技能… | 零依赖 |
| `qa-synthetic-monitoring` | 合成监控规格治理门禁技能：校验合成监控旅程规格是否「受治理」——业务关键旅程必须有断言(预期状态/文本)… | 零依赖 |
| `qa-test-strategy` | 在项目 / 版本测试启动时使用，产出测试计划 / 测试策略：测试范围、目标… | 零依赖 |
| `qa-unit-tdd` | 单元/TDD 方法学健康度评估技能：基于测试金字塔占比、行覆盖率、失败用例、测试/代码比等指标… | 零依赖 |
| `qa-visual-regression` | 视觉回归治理门禁：对比已落盘的基线快照与当前快照（DOM 结构 + 关键视觉属性，**不截图、不调浏览器**）… | 零依赖 |

### ⓐ Agent 测试 · AI Agent 专项评测（2）

| 技能 | 一句话能力 | 依赖 |
|---|---|---|
| `qa-agent-eval` | 评估被测 Agent 本身的能力与可靠性（与被测业务系统区分）。提供任务完成率 Pass@1/Pass^k… | 零依赖 |
| `qa-agent-security` | 对 Agent 做安全 / 红队评测（区别于传统业务系统安全扫描）。覆盖提示注入（直接 / 间接）、越权… | 零依赖 |

### Ⓞ 编排 · 可选生命周期编排（1）

| 技能 | 一句话能力 | 依赖 |
|---|---|---|
| `qa-orchestrator` | 半自动 QA 测试全生命周期编排脚手架：当用户开启一轮测试工作… | 零依赖 |

---

## 生命周期全景

```
需求(qa-req-spec) → 分析(qa-test-analysis) → 用例(qa-test-case-gen)
   → 数据/环境(qa-test-data, qa-env-config) → 接口文档(qa-api-doc)
   → 执行(qa-api-runner / qa-ui-automation / qa-mobile-autotest / qa-perf-* / qa-security-scan)
   → 报告·缺陷·发布(qa-report / qa-bug-* / qa-release-check / qa-security-report)
   → 归档(qa-archive)
```
横切门禁（Ⓣ）与 Agent 测试（ⓐ）可插在任意阶段；`qa-orchestrator`（Ⓞ）为可选的半自动全生命周期编排脚手架。

---

## 依赖分层（诚实声明）

| 分层 | 数量 | 依赖 | 说明 |
|---|---|---|---|
| 治理/编排层 | 34 | 零依赖 | 纯 Python 标准库，开箱即用 |
| Agent 测试层 | 2 | 零依赖 | 纯 Python 标准库 |
| 执行层 | 4 | 需运行时依赖 | `qa-api-runner`(requests/mysql-connector/allure)、`qa-report` & `qa-test-case-gen`(openpyxl)、`qa-ui-automation`(playwright) |

> **诚实边界**：可移植性校验仅做「声明 = 现实」的静态校验（脚本 import 与 `runtime_dependencies` 是否一致），不实际安装/运行第三方包。执行层 4 个技能在落地环境须确保对应依赖真实可用。

---

## 跨 Agent 安装

| flavor | 目标目录 | 适用 |
|---|---|---|
| `generic`（默认） | `./skills` | 任意通用 agent |
| `claude` | `./.claude/skills` | Claude Code / Cursor 等 |
| `workbuddy` | `./.workbuddy/skills` | WorkBuddy 等兼容宿主 |

也可 `--target <dir>` 显式指定目录。详见 [`skills/README.md`](skills/README.md)。

---

## 分层采用

| 套餐 | 你得到什么 | 适合谁 |
|---|---|---|
| **Starter** | 复制单个/几个技能目录，直接调用 | 只想解决单点测试任务 |
| **Gates** | 接入 `signals/` 契约 + `qa-release-check`，质量门禁挂进 CI | 想给流水线加发布卡点 |
| **Full** | 再引入 `qa-orchestrator`，按 8 阶段路由整轮变更 | 想标准化「从需求到归档」全过程 |

---

## 文档导航

- **使用手册（完整）**：[`SKILLS_DELIVERY.md`](SKILLS_DELIVERY.md) — 功能介绍、能力全景、门禁接线、FAQ、命令清单
- **使用手册（精简）**：[`skills/README.md`](skills/README.md) — 三步上手、跨 agent 安装、分层采用、可直接跑的命令
- **维护者命令**：[`skills/MAINTAINERS.md`](skills/MAINTAINERS.md) — 编译体检 / 自测 / 注册中心 / 漂移校验 / 加新技能
- **教程**：[`training/`](training/) — 从安装到跑通一条测试的 10 篇手把手教程
- **架构决策**：[`skills/docs/ADR.md`](skills/docs/ADR.md)、[`skills/docs/DEPENDENCY_GRAPH.md`](skills/docs/DEPENDENCY_GRAPH.md)
- **信号契约**：[`skills/references/signal-schema.md`](skills/references/signal-schema.md)

---

## 质量保障

- 全量脚本 `py_compile` 通过；自测 **120/120** 通过。
- 跨 agent 可移植性校验 **PASS**（40 技能 / 80 脚本，name/description/license/compatibility 齐全、零 `lib/` 引用、依赖全声明、零编译失败）。

---

## 许可

MIT —— 见 [`LICENSE`](LICENSE)。
