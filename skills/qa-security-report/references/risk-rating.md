# 安全风险评级标准（qa-security-report）

## 级别定义（参考 CVSS 思路）

| 级别 | 分值区间 | 含义 | 上线策略 |
| --- | --- | --- | --- |
| Critical | 9.0–10.0 | 可直接被利用、造成数据泄露/接管 | 强制上线前修复 |
| High | 7.0–8.9 | 较易被利用、影响核心资产 | 上线前修复或临时缓解 |
| Medium | 4.0–6.9 | 需一定条件利用 | 排期修复、跟踪 |
| Low | 0.1–3.9 | 利用难、影响小 | backlog |
| Info | 0 |  informational | 知悉即可 |

## 类型 → 默认级别映射

脚本在 findings 未给 `severity` 时按类型推断（可覆盖）：

| 类型 | 默认级别 |
| --- | --- |
| AWS_ACCESS_KEY / PRIVATE_KEY / GITHUB_TOKEN | Critical |
| SLACK_TOKEN / API_KEY_ASSIGN / PASSWORD_ASSIGN | High |
| CN_IDCARD / BANK_CARD（PII 明文） | High |
| CN_MOBILE / EMAIL（PII 明文） | Medium |
| ZAP: SQLi / RCE / SSRF | Critical |
| ZAP: XSS / 敏感信息泄露 | High |
| Semgrep: 命令注入 / eval | High |
| Trivy: CRITICAL CVE | Critical |
| Trivy: HIGH CVE | High |

## 整改通用动作

- **密钥泄露**：立即轮转 + 移入密钥管理（Vault / KMS / 环境变量）。
- **PII 明文**：脱敏存储 + 传输加密 + 日志屏蔽。
- **注入**：参数化查询 / 输入校验 / 白名单。
- **XSS**：输出编码 + CSP + 输入过滤。
- **依赖 CVE**：升级到修复版本 / 替换组件。
- **越权（人工核查）**：加资源归属校验 + 服务端鉴权。

## 报告排序

报告按 Critical → High → Medium → Low → Info 排序，同级按来源聚合，
便于安全负责人一眼看到最高优先项。
