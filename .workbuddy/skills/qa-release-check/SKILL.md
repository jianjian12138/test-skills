---

name: qa-release-check
description: |-
  在生产发布前后使用，核验是否具备上线条件：生成上线门禁清单（构建/DB 迁移/配置/
  依赖/回滚方案）、上线冒烟 smoke 清单，以及发布后监控清单。触发词："上线验证"、
  "发布检查"、"上线冒烟"、"发布后监控"，或在 qa-archive 关闭变更之前使用。
  英文触发词（English triggers）：release checklist, go-live, smoke test.
license: MIT
compatibility: "WorkBuddy / Claude / 通用 Agent（零依赖标准库）"

metadata:
  version: "1.0.0"
  category: traditional
  stage: 07-report
  tier: 1
---
# qa-release-check — 上线验证与发布后核对

上线不是「部署完就完」。本技能生成**上线门禁 + 冒烟 + 发布后监控**三张清单，
把「能不能发、发完有没有事」变成可勾选、可追溯的动作。

> 上线事故 80% 来自配置/依赖/数据，而非代码。门禁清单就是为拦这些。

## 何时使用

- 版本准备发布，需做上线前把关。
- 用户说「上线验证」「发布检查」「上线冒烟」「发布后监控」。

## 操作流程

### 步骤 1 — 填发布信息

```json
{"version":"v2.0.0","env":"prod","services":["order","pay"],"smoke":["下单冒烟","支付冒烟"],
 "db_migrations":true,"config_ok":true,"monitoring":["错误率告警","核心接口SLA"]}
```

### 步骤 2 — 生成清单

```bash
python scripts/gen_release_checklist.py --release release.json --out release_check.md
```

产出 `release_check.md`：
- **上线门禁**：构建/DB 迁移/配置/依赖/回滚方案（任一不过 → 不发）。
- **上线冒烟**：核心链路最小验证（部署后立刻跑）。
- **发布后监控**：错误率/延迟/资源/业务指标（灰度与全量后各看一轮）。

### 步骤 3 — 判定与归档

门禁全过 + 冒烟通过 → 允许上线；上线后监控无异常 → 关闭变更（`qa-archive`）。

## 与上下游衔接

- 输入：`qa-execution` 进度（测试全过才到上线）、`qa-bug-report` 已关闭。
- 输出：上线结论 → `qa-archive` 归档；异常回滚并重开缺陷。

## 横切质量门 opt-in（A-03 增强）

默认发布门禁仅强制 `DEFAULT_REQUIRED`（qa-security-scan / qa-a11y / qa-unit-tdd）。
显式 `--include-cross`（可跟具体技能名，省略则启用 `DEFAULT_CROSS`：qa-code-review / qa-mutation /
qa-flaky-detect / qa-visual-regression / qa-unit-tdd / qa-a11y）时，**主动收紧**发布门槛——
所列横切信号来源缺失即注入 `missing_cross_signal`（blocking）阻断。opt-in 是「提高门槛」而非「放宽」，
回应 V10 评审 A-03：让高相关横切质量门可显式纳入聚合，而非默认游离在门禁外。

## 参考资料

- 检查项、阈值、CLI 用法与常见坑：见 [`references/guide.md`](references/guide.md)。
