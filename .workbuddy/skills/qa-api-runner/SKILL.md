---

name: qa-api-runner
description: |-
  当用户已有接口文档（来自 qa-api-doc），需要真正执行接口自动化测试而不只是生成
  用例时使用。本技能以配置驱动的场景文件运行，支持单接口测试、多接口业务串联
  （变量 extract 提取 + ${var} 注入）、MySQL 数据库双校验断言，以及 Allure 报告。
  触发词："执行接口自动化"、"跑接口用例"、"接口串联测试"、"接口加数据库校验"，
  或在 qa-api-doc / qa-test-case-gen 之后使用。
  英文触发词（English triggers）：API automation, interface testing, API test runner.
license: MIT
runtime_dependencies: requests, mysql, allure
compatibility: "WorkBuddy / Claude / 通用 Agent（编排层零依赖；执行层 requests/mysql/allure 运行期依赖，见 runtime_dependencies）"

metadata:
  version: "1.0.0"
  category: traditional
  stage: 06-execution
  tier: 1
---
# qa-api-runner — 接口自动化执行框架

把「接口文档 → 用例 → 配置 → 执行 → 报告」做成配置驱动、低代码的闭环。
借鉴 ApiAutoTest 思路，用 WorkBuddy 原生技能重写：场景化用例、多接口串联、MySQL 双校验。

## 何时使用

- 已有接口文档（来自 `qa-api-doc`）或接口清单。
- 用户说「执行接口自动化」「跑接口用例」「接口串联」「接口加数据库校验」。
- 要做回归 / 冒烟 / 业务流程校验。

## 核心能力

- **单接口**：常规请求 + 响应断言。
- **多接口串联**：前接口 `extract` 变量 → 后接口 `${var}` 注入（登录→业务→查询）。
- **MySQL 双校验**：接口返回成功不代表数据落地，用 `db_assert` 校验库表。
- **两种运行**：轻量 `run.py`（无需 pytest）/ `test_api.py` + Allure（可视化）。

## 操作流程

### 步骤 1 — 准备场景文件

按 `references/scenario-schema.md` 编写场景 JSON（可由 AI 基于 `api-doc.json` + 业务链生成）。
参考 `references/example_scenario.json`。

### 步骤 2 — 准备环境配置

复制 `.env` 模板（见 `references/runner-config.md`），填 `BASE_URL`；
开启 DB 断言则填数据库连接并置 `DB_ASSERT_ENABLED=true`。

### 步骤 3 — 执行

轻量运行：
```bash
python scripts/run.py --scenario scenario.json --env-file config/.env \
    --outdir <变更目录>/06-execution
```
Allure 报告：
```bash
export QA_SCENARIO=scenario.json QA_ENV_FILE=config/.env
pytest scripts/test_api.py --alluredir=allure-results && allure serve allure-results
```

### 步骤 4 — 读结果

- `06-execution/results.json`：逐用例通过/失败、失败断言详情、提取变量。
- `06-execution/report.md`：通过率、失败点汇总。
- Allure：用例时长、请求/响应、失败定位。

## 深化能力（V2）

- 断言类型扩展：除 `eq/ne/gt/lt/ge/le/contains/in/exists` 外，新增 `regex`（正则）、
  `len`/`len_eq`/`len_gt`/`len_lt`/`len_ge`/`len_le`（长度）、`schema`（轻量结构校验）。
  详见 `references/assert-guide.md`。
- 测试清单与常见坑见 `references/checklist.md`。

## 依赖

- 必装：`requests`。
- 可选：`mysql-connector-python`（DB 断言）、`pytest` + `allure-pytest`（可视化）。
- 安装命令见 `references/runner-config.md`。

## 与上下游衔接

- 输入：来自 `qa-api-doc` 的接口文档、`qa-test-case-gen` 的接口用例思路。
- 输出：交给 `qa-report` 汇总；失败用例在 Phase 4 转 `qa-bug-report` 提交缺陷。
- 串联场景设计的「业务链」思维，与 `qa-test-analysis` 的测试点一脉相承。

## 阶段产物契约（stages.json artifacts）

本阶段主技能须产出的文件名（与 `qa-orchestrator/stages.json` 契约一致）：

- results.json
- locustfile.py

## 假通过治理（V10 / W2·W9·W10）
`scripts/engine.py` 的断言引擎已落实 AI 假通过治理：
- **支持负向测试**：用例可声明 `expect_status`（如 403）或 `allow_error_status: true`，不再被「强制 <400」闷杀（旧逻辑无法写 4xx/5xx 负向用例）。
- **永真断言告警**：无语义断言的用例标 `no_assert_warn`；设环境变量 `QA_API_STRICT_ASSERT=1` 时直接判失败（fail-closed）。
- 完整 9 模式 + 永真黑名单见 `references/ai-false-pass.md`（通用红线，qa-execution/qa-ui-automation 同样适用）。
- plan.jmx
- report.md
- security_findings.json

## Agent 暴露接口桥接（G-03 增强）

当被测 Agent 同时暴露确定 HTTP 接口（即「有确定接口的业务系统」），`scripts/bridge_agent_regression.py`
把该接口回归结果转译为 `signals/qa-api-runner-bridge.json`（signal=`agent_api_regression`），
使其与接口 / UI / 性能 / 安全信号走同一阻断协议、被 `qa-release-check` 直接聚合——
不再让「Agent 接口回归」游离在传统 QA 门禁之外。回归检出 → `blocking=true`（high）；通过 → 信息信号（info）。
