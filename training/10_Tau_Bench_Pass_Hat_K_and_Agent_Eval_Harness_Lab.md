# 实训手册 10：3D 黄金基准构建与 τ-bench pass^k (k=5) 多轮一致性门禁 (`qa-agent-eval`)

## 1. 实训目标 (Lab Objective)
彻底理解 Pass@k 与 pass^k 的幂次衰减差异，搭建 CI 自动化防回归跑分飞轮。

## 2. 实操命令 (Hands-On CLI Commands)
```bash
python3 qaskills.py list
python3 qaskills.py eval
```

## 3. 验收标准 (Acceptance Criteria)
- 所有生成的测试资产包含可验证断言。
- 通过 `python3 -m unittest discover -s tests -p "test_*.py" -v` 与 `pass^5 >= 85.0%` 门禁。
