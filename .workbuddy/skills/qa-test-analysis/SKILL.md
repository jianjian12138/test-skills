---

name: qa-test-analysis
description: |-
  当已有结构化需求文档（由 qa-req-spec 产出），需要把它拆解成可测项、识别风险与
  模糊点，并生成覆盖正向 / 负向 / 边界的测试点清单时使用。本技能在写用例之前，
  会针对待澄清项主动发起澄清对话，避免默认猜测导致漏测。触发词："需求分析"、
  "出测试点"、"分析一下这个需求怎么测"、"帮我拆解测试点"，或在 qa-req-spec 产出
  之后立即使用。
  英文触发词（English triggers）：test analysis, test point, requirement analysis.
license: MIT
compatibility: "WorkBuddy / Claude / 通用 Agent（零依赖标准库）"

metadata:
  version: "1.0.0"
  category: traditional
  stage: 02-analysis
  tier: 3
---
# qa-test-analysis — 需求分析与测试点

直接从需求跳到用例，是漏测的主因。本技能先把需求**结构化拆解**为可测项、风险点、
待澄清项，澄清后再生成覆盖正向 / 负向 / 边界的**测试点清单**，作为 `qa-test-case-gen`
的输入。

## 三级推导模型（功能点 → 测试点 → 测试用例，W7 增强）

本技能位于「测试点」这一中间层，是提升用例采纳率的核心：

- **L1 功能点**：`qa-req-spec` 产出的需求条目（"要做什么"）。
- **L2 测试点**（本技能产出，`testpoints.md`）："验证什么"——把功能点拆成可验证单元，
  去重、归并、标注类型（正/负/边界/专项）与优先级。这是介于需求与用例之间的**中间层**，
  先想清「验证什么」再写步骤，可把用例采纳率从 60–70% 提升到 90%+（对标 AliExpress 实践）。
- **L3 测试用例**：`qa-test-case-gen` 基于本技能产物格式化落盘（"怎么验"，步骤/预期/优先级/Excel/Xmind）。

> 三层边界：L1 是需求语言，L2 是验证语言（可跨项目复用），L3 是实现语言。
> 不要把 L2 直接写成 L3 步骤（易漏「为什么验这条」），也不要跳过 L2 从 L1 直跳 L3（易漏测）。

## 何时使用

- 已有 `requirement.md`（来自 `qa-req-spec`）或等价结构化需求。
- 用户说「需求分析」「出测试点」「拆解测试点」「这个需求怎么测」。

## 操作流程

### 步骤 1 — 结构化拆解（产出 analysis.md）

对 `requirement.md` 的每个功能点，按 `references/analysis-method.md` 拆解：

- **可测项**：把功能点转成「可验证的陈述」（给定条件 → 操作 → 可观测结果）。
- **风险点**：哪些地方易出错 / 历史易漏 / 逻辑复杂（标注高/中/低）。
- **依赖与前置**：数据、环境、账号、第三方。
- **待澄清项**：需求中仍模糊/矛盾/缺失的部分。

### 步骤 2 — 对话澄清（关键）

对待澄清项，**主动发起澄清对话**，不要默认猜测。参考 `references/clarify-patterns.md`
生成具体、可答的问题（一次列 3–6 个，避免刷屏）。澄清结果写回 `clarifications.md`
并回填 `requirement.md` 第 7 节。

### 步骤 3 — 生成测试点（产出 testpoints.md）

澄清后，对每个可测项按 `references/testpoint-patterns.md` 衍生测试点，至少覆盖：

- **正向**：符合预期的正常路径。
- **负向**：非法输入、越权、异常流程、错误提示。
- **边界**：等价类边界、长度/数值极值、空值、并发边界。
- **专项**（若需求涉及）：性能 / 安全 / 兼容视角切入。

每个测试点用一行描述，标注：所属模块、类型（正/负/边界/专项）、关联风险、优先级（P0–P3）。

### 步骤 4 — 落盘与衔接

- `analysis.md`、`clarifications.md`、`testpoints.md` 写入变更工作区 `02-analysis/`。
- 提示用户下一步调用 `qa-test-case-gen` 将测试点转为 Excel/Xmind 用例。

## 质量要求

- 测试点**可追溯**到具体可测项与需求章节。
- 高风险的模块测试点密度应更高（高风险 → 更多负向/边界）。
- 澄清未完成前，不得生成依赖该项的用例。

## 与下游衔接

`testpoints.md` 是 `qa-test-case-gen` 的直接输入；接口相关的测试点应同步触发
`qa-api-doc` 准备接口文档。

## 阶段产物契约（stages.json artifacts）

本阶段主技能须产出的文件名（与 `qa-orchestrator/stages.json` 契约一致）：

- analysis.md
- testpoints.md
