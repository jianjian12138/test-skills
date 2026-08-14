#!/usr/bin/env python3
"""Turn normalized security findings into a risk-rated markdown report.

Usage:
    python scripts/gen_sec_report.py --findings findings.json --out sec_report.md

Severity inferred from `type` when not given (see TYPE_SEVERITY).
"""
import argparse
import json
import sys

SEV_ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "Info": 4}
SEV_SCORE = {"Critical": 9.5, "High": 7.5, "Medium": 5.0, "Low": 2.0, "Info": 0.0}

# CVSS v3.1 基础分向量 → 严重级
CVSS_SEV = [(9.0, "Critical"), (7.0, "High"), (4.0, "Medium"), (0.1, "Low"), (0.0, "Info")]

TYPE_SEVERITY = {
    "AWS_ACCESS_KEY": "Critical", "PRIVATE_KEY": "Critical", "GITHUB_TOKEN": "Critical",
    "SLACK_TOKEN": "High", "API_KEY_ASSIGN": "High", "PASSWORD_ASSIGN": "High",
    "AWS_SECRET": "Critical",
    "CN_IDCARD": "High", "BANK_CARD": "High",
    "CN_MOBILE": "Medium", "EMAIL": "Medium",
    "SQLI": "Critical", "RCE": "Critical", "SSRF": "Critical",
    "XSS": "High", "SENSITIVE_INFO": "High", "COMMAND_INJECTION": "High", "EVAL": "High",
    "CVE_CRITICAL": "Critical", "CVE_HIGH": "High",
}

# CVSS v3.1 基础指标权重（简化近似官方公式）
_CVSS_VAL = {
    "AV": {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.2},
    "AC": {"L": 0.77, "H": 0.44},
    "PR": {"U": {"N": 0.85, "L": 0.62, "H": 0.27}, "C": {"N": 0.85, "L": 0.68, "H": 0.5}},
    "UI": {"N": 0.85, "R": 0.62},
    "S": {"U": 6.42, "C": 7.52},
    "C": {"H": 0.56, "L": 0.22, "N": 0.0},
    "I": {"H": 0.56, "L": 0.22, "N": 0.0},
    "A": {"H": 0.56, "L": 0.22, "N": 0.0},
}


def cvss_base_score(vector: str):
    """Parse a CVSS v3.1 vector like AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H -> (score, severity)."""
    try:
        parts = dict(p.split(":") for p in vector.strip().split("/") if ":" in p)
        av = _CVSS_VAL["AV"][parts["AV"]]
        ac = _CVSS_VAL["AC"][parts["AC"]]
        pr = _CVSS_VAL["PR"][parts["S"]][parts["PR"]]
        ui = _CVSS_VAL["UI"][parts["UI"]]
        s = parts["S"]
        c = _CVSS_VAL["C"][parts["C"]]
        i = _CVSS_VAL["I"][parts["I"]]
        a = _CVSS_VAL["A"][parts["A"]]
        iss = 1 - (1 - c) * (1 - i) * (1 - a)
        if s == "U":
            impact = 6.42 * iss
        else:
            impact = 7.52 * (iss - 0.029) - 3.25 * (iss - 0.02) ** 15
        exploit = 8.22 * av * ac * pr * ui
        if impact <= 0:
            return 0.0, "Info"
        if s == "U":
            base = min(impact + exploit, 10.0)
        else:
            base = min(1.08 * (impact + exploit), 10.0)
        base = round(base, 1)
        sev = "Info"
        for thr, name in CVSS_SEV:
            if base >= thr:
                sev = name
                break
        return base, sev
    except Exception:
        return None, None


def _sev(finding: dict) -> str:
    # CVSS 优先
    vec = finding.get("cvss_vector")
    if vec:
        _, sev = cvss_base_score(vec)
        if sev:
            return sev
    s = (finding.get("severity") or "").capitalize()
    if s in SEV_ORDER:
        return s
    t = (finding.get("type") or "").upper()
    if t.startswith("CVE") or "CRITICAL" in t:
        return "Critical"
    return TYPE_SEVERITY.get(t, "Medium")


def render(data: dict) -> str:
    findings = data.get("findings", [])
    for f in findings:
        f["_sev"] = _sev(f)
        vec = f.get("cvss_vector")
        if vec:
            sc, _ = cvss_base_score(vec)
            f["_cvss"] = sc
    findings.sort(key=lambda x: (SEV_ORDER.get(x["_sev"], 9), -(x.get("_cvss") or 0),
                                 x.get("source", "")))

    counts = {k: 0 for k in SEV_ORDER}
    for f in findings:
        counts[f["_sev"]] += 1

    lines = []
    lines.append("# 安全测试风险评级报告\n")
    lines.append("## 风险总览\n")
    lines.append(f"- 发现总数：**{len(findings)}**")
    lines.append(f"- Critical：{counts['Critical']} ｜ High：{counts['High']} ｜ "
                 f"Medium：{counts['Medium']} ｜ Low：{counts['Low']} ｜ Info：{counts['Info']}")
    top = findings[0]["_sev"] if findings else "无"
    lines.append(f"- 最高风险级别：**{top}**")
    lines.append("")

    lines.append("## 发现明细（按级别排序）\n")
    cur = None
    for f in findings:
        if f["_sev"] != cur:
            cur = f["_sev"]
            lines.append(f"### {cur}\n")
        loc = f.get("location", "-")
        src = f.get("source", "-")
        title = f.get("title", f.get("type", "未命名"))
        cvss = f.get("_cvss")
        cvss_s = f" ｜ CVSS {cvss}" if cvss is not None else ""
        epss = f.get("epss")
        epss_s = f" ｜ EPSS 利用概率 {epss*100:.1f}%" if isinstance(epss, (int, float)) else ""
        lines.append(f"- **[{src}] {title}**  (`{loc}`){cvss_s}{epss_s}")
        if f.get("detail"):
            lines.append(f"  - 说明：{f['detail']}")
        if f.get("evidence"):
            lines.append(f"  - 证据：{f['evidence']}")
        if f.get("cvss_vector"):
            lines.append(f"  - CVSS 向量：{f['cvss_vector']}")
        if f.get("compliance"):
            lines.append(f"  - 合规：{', '.join(f['compliance'])}")
        lines.append(f"  - 整改：{f.get('remediation', '待补充')}")
        lines.append("")

    # 合规映射汇总
    comp = {}
    for f in findings:
        for c in (f.get("compliance") or []):
            comp.setdefault(c, []).append(f.get("title", f.get("type", "?")))
    if comp:
        lines.append("## 合规映射\n")
        for c, items in comp.items():
            lines.append(f"- **{c}**：{len(items)} 项相关（{', '.join(items[:5])}）")
        lines.append("")

    lines.append("## 整改排期建议\n")
    lines.append("- **Critical / High**：上线前必须修复或具备临时缓解措施（如 WAF 规则）。")
    lines.append("- **Medium**：纳入当前迭代排期修复并回归验证。")
    lines.append("- **Low / Info**：登记 backlog，按节奏清理。")
    lines.append("- 密钥类泄露：无论级别，**立即轮转**。")
    lines.append("- EPSS 高（>10%）的 High 项优先于 EPSS 低的 Critical 同类项。")
    lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--findings", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    try:
        with open(args.findings, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[ERROR] 读取 findings 失败: {e}", file=sys.stderr)
        return 2

    md = render(data)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"[OK] 已生成安全报告: {args.out}（{len(data.get('findings', []))} 项）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
