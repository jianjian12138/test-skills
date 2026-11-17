# 实训手册 04：OpenAPI 3.1 递归 $ref 解析与 3D BOLA 越权模糊测试 (`qa-api-contract`)

## 1. 实训目标 (Lab Objective)
构建 4 角色 × 3 HTTP 动词 × 3 资源状态的 36 向量有状态越权探测矩阵。

## 2. 实操命令 (Hands-On CLI Commands)
```bash
python3 qaskills.py list
python3 qaskills.py eval
```

## 3. 验收标准 (Acceptance Criteria)
- 所有生成的测试资产包含可验证断言。
- 通过 `python3 -m unittest discover -s tests -p "test_*.py" -v` 与 `pass^5 >= 85.0%` 门禁。
