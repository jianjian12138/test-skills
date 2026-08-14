---

name: qa-synthetic-monitoring
description: 合成监控规格治理门禁技能：校验合成监控旅程规格是否「受治理」——业务关键旅程必须有断言(预期状态/文本)、告警阈值与探测频率；缺失则产出阻断信号，避免无断言/无告警的"哑"监控上线后漏报。触发词："合成监控", "synthetic monitoring", "拨测", "探针", "黑盒监控", "监控门禁", or after qa-perf-analysis. 英文触发词（English triggers）：synthetic monitoring, black-box monitoring, probe.
license: MIT
metadata:
  version: "1.0.0"
  category: traditional
  stage: cross_cutting
  tier: 2
compatibility: "WorkBuddy / Claude / 通用 Agent（零依赖标准库）"
---
# qa-synthetic-monitoring 合成监控治理门禁

用**脚本化探针模拟用户关键旅程**（登录、下单、支付），在受控环境持续探测以发现可用性 / 性能回归。本技能是一个**治理门禁**：它不实际对生产发起探测，而是校验你设计的合成监控规格是否「受治理」——业务关键旅程必须补齐断言、告警阈值与探测频率，否则视为"哑监控"（上线后既不报警也不验证），阻断发布。

> ⚠️ **治理门禁 · 不执行外部工具**：本技能仅校验合成监控**规格**是否受治理，不实际对生产/线上发起任何探测；所有判定基于你提供的 YAML/JSON 规格，不做运行时拨测。

## 何时使用
- 你准备为关键用户旅程配置合成监控 / 拨测。
- 你写好了监控 YAML/JSON，想先卡一道「是否真能告警」的门禁。
- 在 `qa-perf-analysis` 之后，或作为发布前线上可观测性保障的一环。

## 规则（治理三要素）
| 规则 | 含义 | 严重度 |
|---|---|---|
| SM-ASSERT | 每步须有断言（expected_status 或 expected_text） | 缺则 high；业务关键缺则 critical |
| SM-ALERT | 业务关键旅程须有告警阈值（alert_p95_s） | 缺则 high；业务关键缺则 critical/blocking |
| SM-FREQ | 旅程须有探测频率（frequency） | 缺则 high |

业务关键（`business_critical: true`）旅程缺断言或告警阈值 → 产出 `blocking=true` 信号，门禁失败。

## 使用方式
```bash
python qa-synthetic-monitoring/scripts/monitor_gate.py --spec monitor.json --out signals
```

## 诚实边界（重要）
- 本技能**只校验监控规格的治理完整性**，不实际对生产 / 预发发起任何 HTTP 探测（无网络依赖）。
- 实际探测由黑盒监控 / ATS（如 Playwright 定时任务、云拨测）在受控环境执行；本技能确保「先治理、再上线」。
- 它不验证探测本身能否到达目标，只保证监控定义具备可告警的闭环。

## 参考资料

- 检查项、阈值、CLI 用法与常见坑：见 [`references/guide.md`](references/guide.md)。
