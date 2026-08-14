# Locust 使用指南（qa-perf-locust）

## 安装

```bash
pip install locust
locust -V   # 验证
```

## 生成的脚本结构

```python
from locust import HttpUser, task, between

BASE_URL = "https://api.example.com"

class LoadPeakUser(HttpUser):
    host = BASE_URL
    wait_time = between(0.5, 1.5)

    @task(5)
    def create_order(self):
        self.client.post("/order", json={"sku": "A1", "qty": 1}, name="create_order")

    @task(3)
    def query_order(self):
        self.client.get("/order/{id}", name="query_order")
```

## 常用运行方式

```bash
# 无头模式，500 并发，50/s 爬坡，跑 600 秒，导出 CSV + HTML
locust -f locustfile.py --headless -u 500 -r 50 -t 600s \
    --csv=results --html=report.html

# Web UI 模式（默认 8089 端口）
locust -f locustfile.py
```

## 关键参数

| 参数 | 含义 |
| --- | --- |
| -u / --users | 并发用户数（`users`） |
| -r / --spawn-rate | 每秒启动用户数（`spawn_rate`） |
| -t / --run-time | 运行时长（`duration` 秒，可写 `600s`） |
| --csv | 导出 stats 与 history（前缀） |
| --html | 导出 HTML 报告 |

## 进阶技巧

### 1. 登录态（token 关联）

```python
def on_start(self):
    r = self.client.post("/login", json={"u": "x", "p": "y"})
    self.token = r.json().get("token")

@task
def me(self):
    self.client.get("/me", headers={"Authorization": f"Bearer {self.token}"})
```

### 2. 数据驱动

```python
import csv
data = list(csv.DictReader(open("users.csv")))
@task
def login(self):
    row = data[self.user_id % len(data)]
    self.client.post("/login", json=row)
```

### 3. 自定义断言 / 失败上报

```python
@task
def create_order(self):
    with self.client.post("/order", json={...}, catch_response=True) as r:
        if r.status_code != 201:
            r.failure(f"status {r.status_code}")
        elif r.elapsed.total_seconds() > 1.0:
            r.failure(f"slow {r.elapsed.total_seconds():.2f}s")
```

## 结果文件

- `results_stats.csv`：聚合统计（请求数、失败数、P50/P95/P99、RPS）。
- `results_history.csv`：时间序列（用于画图 / 趋势）。
- `report.html`：可视化报告。

交给 `qa-perf-analysis` 解析上述 CSV。
