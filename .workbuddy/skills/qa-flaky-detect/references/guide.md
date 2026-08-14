# 易碎测试检测指南 — qa-flaky-detect

## 1. 目的
根据同一用例的多轮重跑结果，计算 flaky 率，超阈值即阻断，防止「偶发红」污染 CI 信号。

## 2. 阻断规则
- `flaky_rate = 不稳定用例数 / 总用例数`
- `flaky_rate > --threshold` → 写 `signals/qa-flaky-detect.json` 的 `flaky_detected`，`blocking=true`。
- 默认阈值 `--threshold 0.05`（5%）；`--min-runs 2`（少于 2 轮不判定）。

## 3. CLI 约定
```bash
python qa-flaky-detect/scripts/flaky_detect.py \
  --runs ci/runs.json --signals-dir signals --fail-on
# --runs 为各用例多轮 pass/fail 的 JSON
```

## 4. 输入格式（`--runs`）
```json
[{"name":"t_login","results":[true,true,false,true]},
 {"name":"t_pay","results":[true,true,true,true]}]
```
- 只要出现 pass/fail 不一致即计入不稳定。

## 5. 常见坑
- 轮数过少（<2）统计无意义，先确保 `--min-runs` 满足再采信结论。
- 本技能不识别 flaky 根因（并发/时序/环境），只定量；根因定位需结合日志。
