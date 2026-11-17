# 实训手册 02：等价类、边界值、正交矩阵与状态机测试分析 (`qa-test-analysis`)

## 1. 实训目标 (Lab Objective)
结合 Pairwise 正交法与状态迁移图拆解复杂支付及订单履约链路。

## 2. 实操命令 (Hands-On CLI Commands)
```bash
python3 qaskills.py list
python3 qaskills.py eval
```

## 3. 验收标准 (Acceptance Criteria)
- 所有生成的测试资产包含可验证断言。
- 通过 `python3 -m unittest discover -s tests -p "test_*.py" -v` 与 `pass^5 >= 85.0%` 门禁。
