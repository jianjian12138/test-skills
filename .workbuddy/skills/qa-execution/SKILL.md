---

name: qa-execution
description: |-
  当一个版本需要把多类测试（UI / API / 性能 / 安全）统一编排与跟踪时使用。本技能
  从用例 + 结果 JSON 生成执行进度矩阵（按模块 / 类型 / 状态交叉统计），并把每个
  失败项路由到对应的下游技能处理。触发词："执行编排"、"测试进度矩阵"、
  "跨类型执行"、"测试进度跟踪"。
  英文触发词（English triggers）：test execution, test progress, orchestration.
license: MIT
compatibility: "WorkBuddy / Claude / 通用 Agent（零依赖标准库）"

metadata:
  version: "1.0.0"
  category: traditional
  stage: 06-execution
  tier: 1
---
# qa-execution — 跨类型测试执行编排

把 UI / 接口 / 性能 / 安全 多类测试**统一编排、统一跟踪**：一张进度矩阵，
看清「哪些模块、哪类测试、什么状态、谁负责、卡在哪」，并自动把失败项路由到下游。

> 一个大版本往往同时跑多类测试。没有编排，结果散落各处，复盘靠人肉拼。本技能统一视角。

## 何时使用

- 一个版本涉及 UI + 接口 + 性能 + 安全多类测试。
- 用户说「执行编排」「测试进度矩阵」「跨类型执行」「测试进度跟踪」。
- 要在 `qa-report` 之前先摸清整体进度与阻塞。

## 操作流程

### 步骤 1 — 汇总用例与结果

各专项技能跑完后，把用例 + 结果归一成如下 JSON（`references/matrix-schema.md`）：

```json
{"change": "订单v2", "cases": [
  {"module":"下单","type":"api","name":"创建订单-正常","priority":"P0","status":"passed","owner":"张三"},
  {"module":"下单","type":"ui","name":"下单页-冒烟","priority":"P1","status":"failed","owner":"李四"}
]}
```

### 步骤 2 — 生成矩阵

```bash
python scripts/gen_matrix.py --cases cases.json --out matrix.md
```

产出 `matrix.md`：总览（总数/通过/失败/阻塞/未执行 + 通过率）、
按模块×类型交叉统计、逐用例明细表，以及**失败项路由建议**
（api/ui 失败→`qa-bug-report`；性能不达标→`qa-perf-analysis` 归因；安全高危→`qa-security-report`）。

### 步骤 3 — 衔接

- 失败项转 `qa-bug-report` 提缺陷。
- 整体结论交给 `qa-report` 出质量评估。
- 阻塞项标记，等 `qa-bug-verify` / `qa-release-check`。

## Workflow × Agent 边界与原子操作（W9 增强）

明确哪些环节走**预定义 Workflow**、哪些交给 **Agent 自主**（印证本包设计，补边界声明）：
- **Workflow（确定性、可断言）**：环境准备、账号 / 配置函数化、用例编排、结果汇总——走固定脚本，产出可审计证据。
- **Agent 自主（需观察与决策）**：识别被测系统状态、决定动作、对结果做断言证据采集——交给 Agent 的 O-T-A-R 循环。

8 类原子操作（aiTap / aiInput / aiScroll / aiHover / aiWait / aiAssert / aiNavigate / aiScreenshot）统一接口，
每个动作返回结构化证据；Workflow 与 Agent 共用同一原子操作层，保证证据可被发布门禁聚合。

## 与上下游衔接

- 输入：各专项技能的产物（用例 + 结果）。
- 输出：`qa-report`（汇总）、`qa-bug-report`（失败项）、`qa-release-check`（上线门禁）。
