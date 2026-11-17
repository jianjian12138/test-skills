# 实训手册 03：大陆合规造数工厂、跨表订单链与主动 PII 脱敏 (`qa-test-data`)

## 1. 实训目标 (Lab Objective)
手写 GB 11643-1999 18 位身份证校验位算法与 Users-Orders-Payments-Inventory 外键关联造数。

## 2. 实操命令 (Hands-On CLI Commands)
```bash
python3 qaskills.py list
python3 qaskills.py eval
```

## 3. 验收标准 (Acceptance Criteria)
- 所有生成的测试资产包含可验证断言。
- 通过 `python3 -m unittest discover -s tests -p "test_*.py" -v` 与 `pass^5 >= 85.0%` 门禁。
