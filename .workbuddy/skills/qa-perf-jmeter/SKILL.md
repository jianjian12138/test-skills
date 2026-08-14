---

name: qa-perf-jmeter
description: |-
  性能测试 JMeter 技能（与 qa-perf-locust 平级、共用 qa-perf-design 场景 schema）。把
  场景 JSON 生成标准 JMeter .jmx，并解析 JMeter 结果 CSV 给出与 qa-perf-analysis 同口径
  的吞吐 / 延迟分位 / 错误率 / 瓶颈诊断 / SLA 判定。适合无代码 / 分布式压测 / 已有 JMeter
  资产的团队。触发词： "JMeter 压测", "生成 jmx", "JMeter 结果分析", or after
  qa-perf-design.
  英文触发词（English triggers）：JMeter, jmx, performance testing.
license: MIT
compatibility: "WorkBuddy / Claude / 通用 Agent（零依赖标准库）"

metadata:
  version: "1.0.0"
  category: traditional
  stage: 06-execution
  tier: 1
---
# qa-perf-jmeter — JMeter 性能测试（兼容 Locust 之外的另一条路线）

与 `qa-perf-locust` 平级：**两者共用 `qa-perf-design` 的场景 JSON schema**，可互换。
选 JMeter 还是 Locust，见下方「选型建议」。

> 已有 Locust 路线（qa-perf-locust / qa-perf-analysis）专注代码化与 CI；
> 本技能提供 JMeter 路线，覆盖无代码、分布式、已沉淀 JMeter 脚本的团队。

## 选型建议

| 维度 | JMeter | Locust |
| --- | --- | --- |
| 上手 | 无代码 GUI，上手快 | 需写 Python |
| 分布式 | 原生 master-slave，成熟 | 需 master/worker 编排 |
| 协议 | 多（HTTP / JDBC / JMS / FTP…） | 以 HTTP 为主 |
| CI 集成 | `-n -t x.jmx -l result.csv` | `locust -f x.py --headless` |
| 脚本版本化 | XML，diff 友好度一般 | Python，diff 友好 |

**结论**：无代码/分布式/已有 JMeter 资产 → 用本技能；代码化/深度 CI 编排 → 用 qa-perf-locust。

## 操作流程

### 步骤 1 — 生成 .jmx

```bash
python scripts/gen_jmx.py --scenarios scenario.json --out plan.jmx
# 可选：--data-csv data.csv  （CSV 数据驱动）
#       --threads-cap 1000   （单节点线程上限，超出在注释里提示走分布式）
```

产物 `plan.jmx`：每个 scenario 一个 ThreadGroup；按 weight 用 Throughput Controller
分配接口权重；含 Header Manager、Constant Timer（think_time）、Aggregate/Summary 监听器。

### 步骤 2 — 运行（无 GUI 模式）

```bash
jmeter -n -t plan.jmx -l result.csv -e -o report_html
# -l result.csv  产出 CSV（analyze_jmeter.py 解析源）
# -e -o report_html  生成 HTML 报告（人工查看）
# 分布式： jmeter -n -t plan.jmx -r -l result.csv   （需 remote_hosts 配置）
```

详见 `references/jmeter-guide.md`。

### 步骤 3 — 分析结果

```bash
python scripts/analyze_jmeter.py --csv result.csv --sla sla.json --out analysis.md
```

`analysis.md` 与 `qa-perf-analysis` 同口径：总览 / 逐接口 / 瓶颈诊断 / SLA 判定。

### 瓶颈启发式（同 qa-perf-analysis）

| 信号 | 可能瓶颈 |
| --- | --- |
| 错误率随并发上升 | 过载 / 限流 / 连接池耗尽 |
| 延迟高但吞吐上不去 | 单请求重（慢 SQL / 外部调用） |
| 用户涨、吞吐 plateau | 系统饱和点 |
| P99 远高于 P95 | 长尾（GC / 锁 / 慢依赖） |

## 与上下游衔接

- 输入：`qa-perf-design` 场景 JSON（同 schema）。
- 输出：结论进 `qa-report` / 上线评审；不达标转 `qa-bug-report`。
- 对比：`qa-perf-analysis` 专用于 Locust；本技能专用于 JMeter，口径一致便于横向比较。
