# 实训手册 08：生产流量镜像去噪重放（Shadow QA）与混沌工程故障注入 (`qa-shadow-replay`)

## 1. 实训目标 (Lab Objective)
剥离动态时间戳与 Nonce 噪声，零代码校验新旧版本接口响应结构与数值偏移。

## 2. 实操命令 (Hands-On CLI Commands)
```bash
python3 qaskills.py list
python3 qaskills.py eval
```

## 3. 验收标准 (Acceptance Criteria)
- 所有生成的测试资产包含可验证断言。
- 通过 `python3 -m unittest discover -s tests -p "test_*.py" -v` 与 `pass^5 >= 85.0%` 门禁。
