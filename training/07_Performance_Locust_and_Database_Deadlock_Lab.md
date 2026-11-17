# 实训手册 07：利特尔法则容量建模、Locust 协程压测与数据库死锁复现 (`qa-perf-locust`)

## 1. 实训目标 (Lab Objective)
编写带 P99 自动熔断钩子的压测脚本并分析高并发乐观锁/悲观锁冲突。

## 2. 实操命令 (Hands-On CLI Commands)
```bash
python3 qaskills.py list
python3 qaskills.py eval
```

## 3. 验收标准 (Acceptance Criteria)
- 所有生成的测试资产包含可验证断言。
- 通过 `python3 -m unittest discover -s tests -p "test_*.py" -v` 与 `pass^5 >= 85.0%` 门禁。
