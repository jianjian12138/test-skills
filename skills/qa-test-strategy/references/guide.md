# 测试计划 / 策略指南 — qa-test-strategy

## 1. 策略范围
- 输入：策略输入 JSON，含 `project` / `version` / `scope` / `objectives` / `types`（ui/api/perf/security 等）/ `schedule` / `entry`（准入）/ `exit`（准出）/ `risks`。
- 输出：`test_strategy.md`——项目概述、测试范围、目标、各类型测试策略、进度、准入准出、风险与应对。后续 `qa-req-spec` / `qa-test-analysis` / `qa-execution` 的总纲。

## 2. 阻断规则
- 本技能**不产出质量信号**（纯规划文档），无 `blocking` 门禁。
- 失败即 `sys.exit(1)` 的情形：`--strategy` 文件不存在或 JSON 非法。

## 3. CLI 约定
```bash
python qa-test-strategy/scripts/gen_strategy.py --strategy strategy.json --out test_strategy.md
```
- `--strategy`：策略输入 JSON（必填）。
- `--out`：Markdown 输出（必填）。

## 4. 常见坑（诚实边界）
- `types` 漏写某类（如只写 ui/api 漏 perf/security）会导致后续执行阶段覆盖不全——策略是"测试合同"，类型覆盖须经干系人确认。
- 准出标准（`exit`）须可量化（如"用例执行率 100%""无 P0 遗留"），避免"测试充分"这类不可验证表述。
- 策略文档生成后需人工评审签字，本技能不代判策略合理性。
