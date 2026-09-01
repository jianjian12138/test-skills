# 性能场景设计模板

## 1. 性能目标（来自需求 / NFR）

- 业务峰值：______
- 目标 TPS / QPS：______
- 响应时间 SLA：P95 ≤ ___ ms，P99 ≤ ___ ms
- 错误率上限：≤ ___ %
- 数据规模：___ 万行 / ___ 并发用户

## 2. 场景矩阵

每个场景一个对象，字段含义见下：

| 字段 | 含义 |
| --- | --- |
| name | 场景名（英文 slug，用于脚本/报告） |
| type | load / stress / endurance / spike |
| users | 目标并发用户数 |
| spawn_rate | 每秒启动的用户数（爬坡速度） |
| duration | 持续时长（秒），spike 含上升/回落阶段 |
| think_time | 思考时间（秒），模拟真实操作间隔 |
| target_tps | 期望达到的吞吐（用于 load 判定） |
| sla_p95_ms | 该场景 P95 响应时间阈值 |
| sla_error_rate | 该场景错误率阈值（小数，如 0.01） |

### 示例场景 JSON

```json
{
  "target": "订单创建接口",
  "base_url": "https://api.example.com",
  "scenarios": [
    {
      "name": "load_peak",
      "type": "load",
      "users": 500,
      "spawn_rate": 50,
      "duration": 600,
      "think_time": 1.0,
      "target_tps": 1000,
      "sla_p95_ms": 500,
      "sla_error_rate": 0.01
    },
    {
      "name": "stress_ramp",
      "type": "stress",
      "users": 2000,
      "spawn_rate": 100,
      "duration": 300,
      "think_time": 0.5,
      "target_tps": null,
      "sla_p95_ms": 1000,
      "sla_error_rate": 0.05
    },
    {
      "name": "endurance_soak",
      "type": "endurance",
      "users": 400,
      "spawn_rate": 40,
      "duration": 14400,
      "think_time": 2.0,
      "target_tps": 800,
      "sla_p95_ms": 600,
      "sla_error_rate": 0.01
    },
    {
      "name": "spike_burst",
      "type": "spike",
      "users": 1500,
      "spawn_rate": 500,
      "duration": 120,
      "think_time": 0.5,
      "target_tps": null,
      "sla_p95_ms": 1500,
      "sla_error_rate": 0.10
    }
  ]
}
```

## 3. 判定口径

- **load**：实际 TPS ≥ target_tps 且 P95 ≤ sla_p95_ms 且 error ≤ sla_error_rate → 通过。
- **stress**：记录拐点（TPS 开始下降 / 错误率突增的并发点），作为容量上限依据。
- **endurance**：时长内 TPS/P95 无明显退化、资源（CPU/内存）无持续上涨 → 通过。
- **spike**：峰值后回落至基线水平且错误率回落 → 韧性达标。
