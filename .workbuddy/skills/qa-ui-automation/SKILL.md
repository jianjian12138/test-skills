---

name: qa-ui-automation
description: |-
  当已有 UI 知识库（qa-ui-kb）、选择器也已用 data-testid 稳定（qa-ui-testid），用户
  需要真正搭建并运行 UI 自动化（Playwright）时使用。本技能根据页面描述 JSON 生成
  Page Object 页面对象骨架与冒烟用例，并说明如何用 Playwright + Allure 执行出报告。
  触发词："生成 UI 自动化"、"写 Playwright 脚本"、"UI 页面对象"、"UI 冒烟测试"，
  或在 qa-ui-kb / qa-ui-testid 之后使用。
  英文触发词（English triggers）：UI automation, Playwright, page object.
license: MIT
runtime_dependencies: playwright
compatibility: "WorkBuddy / Claude / 通用 Agent（编排层零依赖；执行层 playwright 运行期依赖，见 runtime_dependencies）"

metadata:
  version: "1.0.0"
  category: traditional
  stage: 06-execution
  tier: 1
---
# qa-ui-automation — UI 自动化执行

在「知识库 + 稳定 testid」地基之上，把页面描述转为可维护的 Playwright 页面对象与用例，
并执行、出报告。与 `qa-ui-kb`（理解页面）、`qa-ui-testid`（稳定选择器）配套使用。

## 何时使用

- 已有 UI 知识库 / 元素清单，或已补 data-testid。
- 用户说「生成 UI 自动化」「写 Playwright 脚本」「UI 页面对象」「UI 冒烟测试」。

## 操作流程

### 步骤 1 — 准备页面描述 JSON

按 `references/po-schema.md` 编写页面描述（可由 AI 基于 `qa-ui-kb` 知识库生成）。
参考 `references/example-pages.json`。

### 步骤 2 — 生成页面对象

```bash
python scripts/page_object_gen.py --input pages.json --outdir <变更>/06-execution/ui_tests
```
产出 `pages.py`（所有 PO 类，元素集中、选择器只在此处）与 `test_smoke.py`（示例冒烟）。

### 步骤 3 — 安装与执行

```bash
pip install playwright && playwright install
pytest <变更>/06-execution/ui_tests --alluredir=allure-results
allure serve allure-results
```
详细环境/等待/Allure 见 `references/playwright-setup.md`。

### 步骤 4 — 维护

- 页面结构变化 → 只改 `pages.py` 的元素层，用例不动。
- 新增页面 → 在 `pages.json` 追加，重新生成或手动补类。
- 陷阱笔记来自 `qa-ui-kb` 知识库，写入用例注释避免重踩。

### 步骤 5 — 五维质量评分（覆盖率量化 + 失败分桶）

交付前用 `quality_score.py` 把「覆盖了什么」量化为可复查分数，避免「红绿一片说不清覆盖」。

```bash
python scripts/quality_score.py --input ui_inventory.json --out ui_score.md
```

五维（screen/behavior/endpoint/journey/locator，权重可配）综合成 composite：
- composite < 70 → **不强行当流水线硬门槛，但必须按 gaps 补测后重评**（与发布门禁哲学一致）。
- 失败自动分桶 triage（targeting/timing/session），先按桶修再重跑：targeting 高→改定位与
  Screen Model；timing 高→查等待与异步；session 高→查登录态/权限夹具。

`ui_inventory.json` 由 Screen Model / 路由 / 接口清单汇总（详见脚本 docstring 字段说明）。

## 落地纪律（W2 增强）

- **步骤对照表**：生成 Page Object / 用例后，产出「用例步骤 ↔ 代码实现（`pages.py` 元素/方法）」
  逐条对照表，缺失对应实现的步骤标红。禁止「步骤全写但 PO 只实现部分」——这是 UI 自动化
  「11 步只实现 3 步」假绿的高发区，对照表须随用例一并交付。
- **调试三轮制**：UI 自动化落地采用三轮收敛，避免一次性全量跑浪费：
  - 第 1 轮：跑 3–5 条关键路径（核心流程 + 1 条边界）。
  - 第 2 轮：仅重跑第 1 轮失败项 + 同类扩展。
  - 第 3 轮：全量回归。
  - 超 3 轮仍未稳定：标记「待人工」，不强行刷绿，记录阻塞原因。

## 定位金字塔与 locator-health（W5 增强）

选择器优先用 **L1 accessibility-id**（data-testid / getByTestId），逐级降级到 **L5 XPath**（仅兜底且注释原因）；
详见 `qa-compat-matrix` 的定位金字塔。用 `scripts/locator_health.py --inventory locators.json` 计算
`healthIndex`，低于 65 即预警，列出 L4/L5 弱定位器推动补 `data-qa` 钩子。

## 原子操作与 O-T-A-R（W9 增强）

收敛 8 类原子操作（aiTap / aiInput / aiScroll / aiHover / aiWait / aiAssert / aiNavigate / aiScreenshot），
每个原子操作自带「预期证据」。Agent 执行遵循 **O-T-A-R** 循环：
**Observation**（观察当前状态）→ **Thought**（决定下一步）→ **Action**（调用原子操作并采集证据）→
**Replanning**（基于证据重规划），避免「盲点连点」式假绿。

## 与上下游衔接

- 前置：`qa-ui-kb`（知识库）、`qa-ui-testid`（补 testid，保证 `getByTestId` 可用）。
- 输入：来自 `qa-test-analysis` 的 UI 测试点。
- 输出：失败截图/用例转 `qa-bug-report`（Phase 4）；执行结果纳入 `qa-report`。
- 选择器规范遵循 `qa-ui-kb` 的 selector-rules（语义优先、禁索引）。

## 注意
- 生成的 PO 是骨架，业务断言（预期结果校验）需按用例补充。
- 首次运行需 `playwright install` 下载浏览器，属一次性成本。
