---

name: qa-archive
description: |-
  在一次变更 / 测试周期结束时使用，把全部产物（需求、用例、执行结果、报告、缺陷）
  打包成一个带时间戳与清单 manifest 的归档，使整个测试生命周期可追溯、可复盘、
  可还原交付审计。触发词："归档"、"一键归档"、"测试归档"、"关闭变更"，或在
  qa-release-check 通过之后使用。
  英文触发词（English triggers）：test archive, change closure, test artifacts.
license: MIT
compatibility: "WorkBuddy / Claude / 通用 Agent（零依赖标准库）"

metadata:
  version: "1.0.0"
  category: traditional
  stage: 08-archive
  tier: 1
---
# qa-archive — 一键归档

一个变更走完「需求→设计→测试→缺陷→上线」后，把整套产物**打包成一个带清单的归档**，
保证全流程可追溯、可复盘、可交付审计。

> 测试的价值一半在结论，一半在可追溯。归档让每次发布都有完整证据链。

## 何时使用

- 变更关闭 / 上线完成 / 版本发布。
- 用户说「归档」「一键归档」「测试归档」「关闭变更」。

## 操作流程

### 步骤 1 — 指定变更目录

变更目录由 `qa-orchestrator` 的 `init_change.py` 创建，含 01-requirement … 08-archive。

### 步骤 2 — 归档

```bash
python scripts/archive_change.py --change changes/登录模块v2 --out ./archives
```

产出 `./archives/登录模块v2_20260805_215200.zip`（含全部产物，排除缓存）+
`登录模块v2_..._manifest.md`（目录树 + 文件数 + 大小 + 关键结论摘要占位）。

### 步骤 3 — 交付 / 审计

归档文件可作版本发布附件、等保/审计证据、团队知识库沉淀。

## 与上下游衔接

- 输入：`qa-orchestrator` 变更目录（上游所有产物）。
- 上游触发：`qa-release-check` 通过后归档。
- 事后：`qa-report` 结论已落进归档，便于回溯质量趋势。

## 参考资料

- 检查项、阈值、CLI 用法与常见坑：见 [`references/guide.md`](references/guide.md)。

## 阶段产物契约（stages.json artifacts）

本阶段主技能须产出的文件名（与 `qa-orchestrator/stages.json` 契约一致）：

- archive.zip
- ci.yaml
- test-strategy.md
