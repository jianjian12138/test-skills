---

name: qa-perf-analysis
description: |-
  在 Locust 压测（来自 qa-perf-locust）执行完成后使用，把原始 CSV 产物转成可读结论：
  总吞吐、延迟分位（P50/P95/P99）、错误率、瓶颈定位归因，以及 SLA 是否达标的判定。
  触发词："分析压测结果"、"性能结果分析"、"瓶颈定位"、"Locust报告解读"，或在
  qa-perf-locust 之后使用。
  英文触发词（English triggers）：performance analysis, latency, SLA, bottleneck.
license: MIT
compatibility: "WorkBuddy / Claude / 通用 Agent（零依赖标准库）"

metadata:
  version: "1.0.0"
  category: traditional
  stage: 07-report
  tier: 1
---
# qa-perf-analysis — 性能结果分析与瓶颈定位

把 Locust 跑出来的 CSV（`results_stats.csv` + `results_history.csv`）变成
**可读结论**：总吞吐、P50/P95/P99 延迟、错误率、瓶颈在哪、SLA 是否达标。

> 性能结果不是「看个平均数就完」。看分位延迟、看拐点、看资源趋势，才能定位瓶颈。

## 何时使用

- Locust 跑完，拿到 `results_stats.csv` / `results_history.csv`。
- 用户说「分析压测结果」「性能结果分析」「瓶颈定位」「Locust 报告解读」。

## 操作流程

### 步骤 1 — 运行产物就位

确保 Locust 用 `--csv=results` 导出了：
- `results_stats.csv`（聚合 + 每接口统计）
- `results_history.csv`（时间序列）

### 步骤 2 — 分析

```bash
python scripts/analyze_locust.py \
    --stats results_stats.csv \
    --history results_history.csv \
    --sla sla.json \
    --out analysis.md
```

`sla.json`（可选）格式：
```json
{"p95_ms": 500, "error_rate": 0.01, "min_tps": 1000}
```

### 步骤 3 — 读结论

`analysis.md` 含：
- **总览**：总请求数、失败率、峰值 RPS、P95/P99。
- **逐接口**：吞吐、延迟分位、失败数。
- **瓶颈诊断**：基于启发式规则给出可能瓶颈（见下）。
- **SLA 判定**：达标 / 不达标。

### 瓶颈启发式（自动判定）

| 信号 | 可能瓶颈 |
| --- | --- |
| 错误率随并发上升 | 服务端过载 / 依赖限流 / 连接池耗尽 |
| 延迟高但 RPS 上不去 | 单请求重（DB 慢查询 / 序列化 / 外部调用） |
| 用户涨、RPS  plateau | 到达系统饱和点（CPU/线程/连接） |
| history 中响应时间持续上涨 | 内存泄漏 / 缓存失效 / 连接堆积 |
| P99 远高于 P95 | 长尾（GC / 锁竞争 / 慢依赖） |

## 深化能力（V2）

- 拐点（Knee）检测：在总览中输出 RPS 峰值出现的并发点，并判断是否已越过系统饱和点；
  资源维度关联建议（CPU / 内存 / 连接）辅助定位瓶颈根因。
- 瓶颈启发式、拐点检测说明与测试清单见 `references/checklist.md`。

## 与上下游衔接

- 输入：`qa-perf-locust` 的 CSV 产物。
- 输出：结论进入 `qa-report` / 上线评审；不达标项转 `qa-bug-report`。
- JMeter 路线：请用 `qa-perf-jmeter`（`gen_jmx.py` + `analyze_jmeter.py`），
  与本技能同口径但专用于 `.jmx` 与 JMeter 结果 CSV。
