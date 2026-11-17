# 实训手册 06：Git Diff + Python AST + Coverage.py 动静融合精准测试 (`qa-risk-based`)

## 1. 实训目标 (Lab Objective)
穿透 FastAPI Depends 依赖注入与动态 Fixture，精准计算每次提交的受影响测试集。

## 2. 实操命令 (Hands-On CLI Commands)
```bash
python3 qaskills.py list
python3 qaskills.py eval
```

## 3. 验收标准 (Acceptance Criteria)
- 所有生成的测试资产包含可验证断言。
- 通过 `python3 -m unittest discover -s tests -p "test_*.py" -v` 与 `pass^5 >= 85.0%` 门禁。
