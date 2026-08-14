# JMeter 运行与集成指南（qa-perf-jmeter）

## 1. 安装

```bash
# 官网下载 5.x，或
brew install jmeter        # macOS
choco install jmeter       # Windows
# 校验
jmeter --version
```

## 2. 无 GUI 运行（推荐 / CI 用）

```bash
jmeter -n -t plan.jmx -l result.csv -e -o report_html
```

- `-n` 非 GUI 模式
- `-t plan.jmx` 测试计划
- `-l result.csv` 结果 CSV（`analyze_jmeter.py` 解析源）
- `-e -o report_html` 生成 HTML 报告（人工查看）

## 3. 参数化（与 qa-perf-design 对应）

gen_jmx 已将场景映射为：

| 场景字段 | JMeter 元素 |
| --- | --- |
| `users` | ThreadGroup.num_threads（并发线程） |
| `spawn_rate` | ThreadGroup.ramp_time（爬坡秒数 ≈ users/spawn_rate） |
| `duration` | ThreadGroup Scheduler duration |
| `think_time` | ConstantTimer（毫秒） |
| `endpoints[].weight` | Throughput Controller 百分比 |

路径里的 `{id}` 已转为 JMeter 变量 `${id}`，可由 CSV Data Set Config 或用户变量提供。

## 4. 分布式压测

单节点线程上限建议 ≤ 1000（视 CPU/内存）。超过时：

```bash
# 在 jmeter.properties 配 remote_hosts=ip1:port,ip2:port
jmeter -n -t plan.jmx -r -l result.csv
```

gen_jmx 在 `users` 超过 `--threads-cap` 时，会在 `plan.jmx.distributed_note.txt` 给出提示。

## 5. 与 CI 集成

```yaml
# GitHub Actions 片段
- name: Performance (JMeter)
  run: |
    jmeter -n -t plan.jmx -l result.csv -e -o report_html
    python qa-perf-jmeter/scripts/analyze_jmeter.py --csv result.csv --sla sla.json --out analysis.md
- uses: actions/upload-artifact@v4
  with:
    name: jmeter-report
    path: report_html/
```

## 6. 常见坑

- **CSV 路径**：分布式时 CSV 需各 slave 都存在，建议用绝对路径或共享存储。
- **端口占用**：HTML 报告 `-o` 目录必须为空，否则报错。
- **编码**：请求体含中文时，HTTP Request 的 `contentEncoding` 设为 `utf-8`。
- **结果列**：`-l result.csv` 默认列含 `timeStamp,elapsed,label,success,...`，analyze_jmeter 已兼容。
