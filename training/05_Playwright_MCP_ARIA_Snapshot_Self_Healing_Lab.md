# 实训手册 05：Playwright MCP ARIA 无障碍树快照与低 Token 选择器自愈 (`qa-ui-automation`)

## 1. 实训目标 (Lab Objective)
用 200-400 Token 的 ARIA YAML 快照替代数千 Token 的原始 DOM，生成 get_by_role 语义补丁。

## 2. 实操命令 (Hands-On CLI Commands)
```bash
python3 qaskills.py list
python3 qaskills.py eval
```

## 3. 验收标准 (Acceptance Criteria)
- 所有生成的测试资产包含可验证断言。
- 通过 `python3 -m unittest discover -s tests -p "test_*.py" -v` 与 `pass^5 >= 85.0%` 门禁。
