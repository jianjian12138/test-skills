# qa-release-check (生产发布多重上线红线门禁核查（Go/No-Go）) — 领域深度参考指南

## 1. 核心检查清单 (Core Verification Checklist)
- **正向主链路覆盖**：验证标准输入下的状态流转、返回值契约与响应耗时 SLA。
- **边界与异常分支**：覆盖空值、极值、重复提交幂等性、超时重试与跨租户权限边界。
- **安全与隐私防线**：确保所有测试输入经过 `sanitize_sensitive_data` 脱敏，遵循 OWASP ASI:2026 与 AST10 规范。

## 2. 关联工具与阶段协同
- **生命周期阶段**：`release_ops`
- **推荐协同技能**：可通过 `python3 qaskills.py route "生产发布多重上线红线门禁核查（Go/No-Go）"` 检索上下游联动技能。
