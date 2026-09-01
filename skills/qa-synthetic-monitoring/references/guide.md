# 合成监控治理门禁指南 — qa-synthetic-monitoring

## 1. 目的
审核「合成监控旅程规格」是否**受治理**：每个业务关键旅程必须有断言、告警阈值与探测频率，否则是「哑监控」——上线后不报故而不知。

## 2. 阻断规则
- 任一关键旅程缺「断言 / 告警阈值 / 探测频率」之一 → 写 `signals/qa-synthetic-monitoring.json` 的 `ungoverned_journey`，`severity=critical`、`blocking=true`。
- 三项齐全 → 放行。

## 3. CLI 约定
```bash
python qa-synthetic-monitoring/scripts/monitor_gate.py --spec monitor/spec.json --out signals --fail-on
```

## 4. 受治理要素（每项旅程须包含）
- **断言**：预期状态码 / 关键文本 / 关键元素存在。
- **告警阈值**：如 `alert_p95_s`（P95 响应秒数上限）。
- **探测频率**：如每 1/5/15 分钟一次。

## 5. 常见坑
- 只有「能访问通」的探活（无断言）= 哑监控，故障页 200 也判通过 → 必触发阻断。
- 告警阈值缺失将导致「慢死」无人知，同样判未治理。
- 本技能**不运行**探测，仅做规格门禁；真实探测由外部监控平台执行。
