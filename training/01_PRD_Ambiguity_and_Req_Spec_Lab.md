# 实训手册 01：非结构化 PRD 模糊点挖掘与可测试规格提取 (`qa-req-spec`)

## 1. 实训目标 (Lab Objective)
掌握如何从一句话需求中识别缺失的限额、幂等锁、状态机逆向流与并发边界。

## 2. 实操命令 (Hands-On CLI Commands)
```bash
python3 qaskills.py list
python3 qaskills.py eval
```

## 3. 验收标准 (Acceptance Criteria)
- 所有生成的测试资产包含可验证断言。
- 通过 `python3 -m unittest discover -s tests -p "test_*.py" -v` 与 `pass^5 >= 85.0%` 门禁。
