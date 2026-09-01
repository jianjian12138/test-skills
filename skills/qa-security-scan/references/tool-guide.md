# 安全扫描工具指南（qa-security-scan）

四类扫描的安装与基本命令。密钥/PII 扫描用本技能自带脚本（离线、确定性）。

## 1. DAST — OWASP ZAP（动态/黑盒）

```bash
# 基线扫描（快速、适合 CI）
docker run --rm -t zaproxy/zap-stable zap-baseline.py -t https://target.example.com -r zap_report.html

# 全量主动扫描（慢，覆盖深）
docker run --rm -t zaproxy/zap-stable zap-full-scan.py -t https://target.example.com
```
- 输出 HTML/XML/JSON 报告，含风险等级与证据。
- CI 集成：用 `-J zap.json` 导出 JSON 交给 `qa-security-report`。

## 2. SAST — Semgrep（静态/白盒）

```bash
pip install semgrep
semgrep --config auto --json -o semgrep.json ./src
# 或只用某类规则
semgrep --config p/owasp-top-ten ./src
```
- 规则覆盖常见注入、硬编码、危险函数。
- `--config p/ci` 适合接入流水线。

## 3. 依赖扫描 — Trivy / pip-audit

```bash
# 文件系统/镜像扫描（含语言依赖）
trivy fs --severity HIGH,CRITICAL --format json -o trivy.json .

# Python 专用
pip install pip-audit
pip-audit -f json -o pipaudit.json
```

## 4. 密钥 / PII 泄露 — 本技能脚本（离线）

```bash
python scripts/scan_secrets.py --path ./src --out secrets_findings.json
```
- 扫描：AWS/TK/GitHub/私钥等密钥模式、密码赋值、`password=` 等。
- PII：中国大陆手机号、身份证、邮箱、银行卡。
- 默认只读，列出文件:行:匹配，不修改任何文件。

## 优先级建议

1. 先跑本技能 `scan_secrets.py`（快、零依赖、零联网）。
2. CI 里加 Semgrep + Trivy（每次提交）。
3. 上线前加 ZAP baseline（每次发版）。
4. 高危项进 `qa-security-report` 评级，再转 `qa-bug-report`。
