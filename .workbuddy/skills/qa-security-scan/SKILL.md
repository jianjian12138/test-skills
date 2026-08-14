---

name: qa-security-scan
description: |-
  当测试工程师需要执行或规划应用安全测试（AST）时使用。本技能提供 OWASP Top 10
  人工核查清单，以及 DAST（ZAP）、SAST（Semgrep）、依赖 CVE 扫描（Trivy）的使用指引，
  并自带确定性的本地密钥 / PII 泄露扫描脚本。触发词："安全测试"、"安全扫描"、
  "漏洞扫描"、"OWASP"、"代码安全"、"密钥泄露检查"。
  英文触发词（English triggers）：security scanning, OWASP, SAST, DAST.
license: MIT
compatibility: "WorkBuddy / Claude / 通用 Agent（零依赖标准库）"

metadata:
  version: "1.0.0"
  category: traditional
  stage: 06-execution
  tier: 1
---
# qa-security-scan — 安全测试与漏洞扫描

覆盖应用安全测试（AST）的四层扫描 + 一份 OWASP Top 10 人工核查清单：

1. **DAST**（动态 / 黑盒）：OWASP ZAP 扫运行中的应用。
2. **SAST**（静态 / 白盒）：Semgrep 扫源码。
3. **依赖扫描**：Trivy / pip-audit 扫三方库 CVE。
4. **密钥 / PII 泄露**：本地确定性正则扫描（本技能自带脚本）。

> 安全测试不是「跑一个工具出报告」。DAST 看运行时、SAST 看代码、依赖看供应链、
> 人工核查看业务逻辑（越权、逻辑漏洞工具扫不出来）。

## 何时使用

- 上线前安全门禁、定期安全巡检、合规（等保 / SOC2）准备。
- 用户说「安全测试」「安全扫描」「漏洞扫描」「OWASP」「代码安全」。
- 代码库里怀疑有硬编码密钥、日志打了手机号/身份证。

## 操作流程

### 步骤 1 — 人工核查清单（必做）

先过 `references/owasp-checklist.md` 的 OWASP Top 10 业务侧核查（越权、逻辑漏洞等工具盲区）。

### 步骤 2 — 跑工具扫描

按 `references/tool-guide.md` 启动四类扫描：
- ZAP：`zap-cli` / `zap-baseline.py` 跑 baseline。
- Semgrep：`semgrep --config auto`。
- Trivy：`trivy fs .` 或 `pip-audit`。
- 本技能脚本（确定性、无需联网）：

```bash
python scripts/scan_secrets.py --path ./src --out secrets_findings.json
```

`scan_secrets.py` 扫描常见密钥（AWS/TK/GitHub/私钥）、密码赋值、以及
PII（中国大陆手机号 / 身份证 / 邮箱 / 银行卡）并标注位置，**默认只读不产生误删**。

### 步骤 3 — 汇总

把四类产出（含 `secrets_findings.json`）交给 `qa-security-report` 做风险评级与整改建议。

## 深化能力（V2）

- ZAP 报告解析：`scripts/parse_zap.py` 把 ZAP XML / JSON 报告归一为
  `qa-security-report` 的 findings JSON（含 CWE 映射）。
- OWASP Top 10 覆盖清单与安全扫描常见坑见 `references/checklist.md`。

## 与上下游衔接

- 输入：被测代码 / 运行中的应用地址。
- 输出：`qa-security-report`（风险评级 + 整改）；高危项转 `qa-bug-report`（安全缺陷）。
