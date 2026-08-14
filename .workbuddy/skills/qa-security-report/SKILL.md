---

name: qa-security-report
description: |-
  在安全扫描（qa-security-scan）完成之后使用，把 ZAP / Semgrep / Trivy / 密钥扫描
  产出的分散 findings 归一成一份带风险评级（参考 CVSS 思路分 Critical / High /
  Medium / Low / Info）与整改建议的安全报告，并按级别排序便于排期修复与上线门禁决策。
  触发词："安全报告"、"漏洞风险评级"、"安全整改"、"风险评级"，或在 qa-security-scan
  之后使用。
  英文触发词（English triggers）：security report, vulnerability, CVSS.
license: MIT
compatibility: "WorkBuddy / Claude / 通用 Agent（零依赖标准库）"

metadata:
  version: "1.0.0"
  category: traditional
  stage: 07-report
  tier: 1
---
# qa-security-report — 安全风险评级与整改报告

把分散的安全扫描产出（ZAP / Semgrep / Trivy / 密钥扫描）统一成
**一份带风险等级 + 整改建议**的报告。每个发现映射到一个风险级别
（参考 CVSS 思路：Critical / High / Medium / Low / Info），给出整改动作，
并按级别排序，方便排期修复与上线门禁决策。

> 漏洞不在「多」，在「等级 + 能不能修」。先修 Critical/High，再谈流程。

## 何时使用

- `qa-security-scan` 跑完，拿到各类 findings。
- 用户说「安全报告」「漏洞风险评级」「安全整改」「风险评级」。

## 输入格式（findings JSON）

各扫描器输出先归一化成本结构（脚本可接受）：

```json
{
  "findings": [
    {"source": "secret-scan", "type": "AWS_ACCESS_KEY", "title": "硬编码AWS密钥",
     "detail": "在 config.py 发现 AKIA...", "location": "src/config.py:12",
     "evidence": "AK***Y6", "remediation": "移入环境变量/密钥管理，立即轮转"},
    {"source": "zap", "type": "XSS", "title": "反射型XSS", "severity": "High",
     "location": "https://t/a?q=", "remediation": "输出编码 + CSP"}
  ]
}
```

`severity` 缺省时由 `type` 映射默认级别（见 `references/risk-rating.md`）。

## 操作流程

```bash
python scripts/gen_sec_report.py --findings findings.json --out sec_report.md
```

`sec_report.md` 含：
- **风险总览**：各级别数量、最高风险。
- **发现明细**：按级别排序，含来源/位置/证据/整改。
- **整改排期建议**：Critical/High 必须上线前修；Medium 跟踪；Low  backlog。

## 深化能力（V2）

- **CVSS 向量评级**：finding 提供 `cvss_vector`（如 `AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H`）
  时，脚本按 CVSS v3.1 近似公式计算基础分并定级，覆盖默认 type 映射。
- **利用概率（EPSS）**：提供 `epss`（0~1）时标注优先级，高 EPSS 的 High 项优先于低 EPSS 同类项。
- **合规映射**：提供 `compliance`（如 `等保2.0`）时汇总合规关联项。
- 风险评级要素、CVSS/EPSS/合规映射与测试清单见 `references/checklist.md`。

## 与上下游衔接

- 输入：`qa-security-scan` 的各类 findings。
- 输出：Critical/High 转 `qa-bug-report`（安全缺陷，标记安全标签）；
  整体结论进上线评审 / `qa-release-check` 门禁。
