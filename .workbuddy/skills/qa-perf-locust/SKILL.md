---

name: qa-perf-locust
description: |-
  当已有性能测试方案（来自 qa-perf-design），需要生成可直接运行的 Locust 压测脚本时
  使用。本技能根据场景 JSON 渲染出 Locust 的 .py 脚本，包含 User/TaskSet 任务类、
  思考时间 think-time、任务权重 weight、爬坡 ramp-up 参数，并给出运行命令。
  触发词："生成压测脚本"、"Locust脚本"、"性能脚本"，或在 qa-perf-design 之后使用。
  英文触发词（English triggers）：Locust, load testing, performance script.
license: MIT
compatibility: "WorkBuddy / Claude / 通用 Agent（零依赖标准库）"

metadata:
  version: "1.0.0"
  category: traditional
  stage: 06-execution
  tier: 1
---
# qa-perf-locust — Locust 压测脚本生成

把 `qa-perf-design` 的场景 JSON 渲染成**可直接运行**的 Locust 脚本：
自动生成 `User` / `TaskSet`、`@task`、权重、思考时间、爬坡参数，
并把每个接口的请求方法、路径、断言写进任务。

> 选型说明：性能压测用 Locust 而非 JMeter —— 纯 Python、可版本化、易与 CI 集成，
> 适合测试工程师写代码而非拖拽组件。复杂分布式再上分布式 master/worker。

## 何时使用

- 已有 `qa-perf-design` 方案（场景 JSON）。
- 用户说「生成压测脚本」「Locust 脚本」「性能脚本」。
- 需要在 CI / 容器里跑压测。

## 操作流程

### 步骤 1 — 准备接口清单

在场景 JSON 里给每个 scenario 挂 `endpoints`（也可以全局共享）：

```json
{
  "base_url": "https://api.example.com",
  "endpoints": {
    "create_order": {"method": "POST", "path": "/order", "weight": 5,
                     "json": {"sku": "A1", "qty": 1}},
    "query_order": {"method": "GET", "path": "/order/{id}", "weight": 3}
  },
  "scenarios": [
    {"name": "load_peak", "type": "load", "users": 500, "spawn_rate": 50,
     "duration": 600, "think_time": 1.0, "endpoints": ["create_order", "query_order"]}
  ]
}
```

### 步骤 2 — 生成脚本

```bash
python scripts/gen_locust.py --scenarios scenarios.json --out locustfile.py
```

生成的 `locustfile.py` 包含：
- 全局 `BASE_URL` / 默认请求头。
- 每个 scenario 一个 `User` 类（类名 `LoadPeakUser` 等），`@task` 按 `weight` 分布。
- 思考时间用 `between(think_time*0.5, think_time*1.5)`。
- 每个请求带 `name=` 便于统计，catch 异常并 `self.environment.runner` 上报。

### 步骤 3 — 运行

```bash
# 命令行（无 UI）
locust -f locustfile.py --headless -u 500 -r 50 -t 600s \
    --csv=results --html=report.html

# 或带 Web UI
locust -f locustfile.py
```

## 进阶

- 关联参数（如登录 token）：在 `on_start` 里拿 token 存 `self.token`。
- 数据驱动：把 `json`/`params` 换成从 `csv` 循环读取（`references/locust-guide.md`）。
- 断言：用 `response.status_code` + `response.elapsed` 自行记录失败。

## 与上下游衔接

- 输入：`qa-perf-design` 的场景 JSON。
- 输出：运行产物 `results_stats.csv` / `results_history.csv` 交给 `qa-perf-analysis`。
