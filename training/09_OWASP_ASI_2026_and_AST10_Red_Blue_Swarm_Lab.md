# 实训手册 09：OWASP Agentic Top 10 (2026) 与 AST10 技能层红蓝对抗飞轮 (`qa-agent-security`)

## 1. 实训目标 (Lab Objective)
针对目标劫持(ASI01)、工具 SSRF(ASI02)、RCE(ASI05) 与记忆投毒(ASI06) 执行红蓝博弈自愈。

## 2. 实操命令 (Hands-On CLI Commands)
```bash
python3 qaskills.py list
python3 qaskills.py eval
```

## 3. 验收标准 (Acceptance Criteria)
- 所有生成的测试资产包含可验证断言。
- 通过 `python3 -m unittest discover -s tests -p "test_*.py" -v` 与 `pass^5 >= 85.0%` 门禁。
