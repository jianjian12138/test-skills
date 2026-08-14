#!/usr/bin/env python3
"""Normalize a ZAP report (XML or JSON) into the findings JSON for qa-security-report.

Usage:
    python scripts/parse_zap.py --report zap_report.xml --out findings.json
    python scripts/parse_zap.py --report zap_report.json --out findings.json

Maps ZAP alert -> {type, title, severity, location, detail, evidence, source:"ZAP"}.
Severity mapped: High->High, Medium->Medium, Low->Low, Informational->Info.
"""
import argparse
import json
import os
import sys
from datetime import datetime


def emit_signal(skill, signals, signals_dir="signals"):
    """Write signals/<skill>.json per the quality-signal contract.

    No file is written when signals is empty (clean run).
    """
    if not signals:
        return
    os.makedirs(signals_dir, exist_ok=True)
    doc = {
        "source": skill,
        "generated_at": datetime.now().isoformat(),
        "schema_version": "1.0",
        "signals": signals,
    }
    with open(os.path.join(signals_dir, f"{skill}.json"), "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
def _sev_map(zap_sev):
    m = {"high": "High", "medium": "Medium", "low": "Low", "informational": "Info"}
    return m.get(str(zap_sev).lower(), "Medium")


def parse_xml(path):
    import xml.etree.ElementTree as ET
    tree = ET.parse(path)
    root = tree.getroot()
    # ZAP traditional XML: <OWASPZAPReport>...<alerts><alert><name><riskcode>...
    findings = []
    for al in root.iter("alert"):
        name = (al.findtext("name") or "").strip()
        risk = (al.findtext("riskcode") or al.findtext("risk") or "").strip()
        url = (al.findtext("url") or "").strip()
        param = (al.findtext("param") or "").strip()
        desc = (al.findtext("desc") or "").strip()
        evidence = (al.findtext("evidence") or "").strip()
        cwe = (al.findtext("cweid") or "").strip()
        findings.append({
            "type": f"ZAP_{name}".upper().replace(" ", "_"),
            "title": name,
            "severity": _sev_map(risk),
            "location": url,
            "detail": (desc[:200] + ("…" if len(desc) > 200 else "")),
            "evidence": (param + (" | " + evidence if evidence else "")).strip(" |"),
            "source": "ZAP",
            "compliance": [f"CWE-{cwe}"] if cwe else [],
        })
    return findings


def parse_json(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    # ZAP JSON: {"site":[{"alerts":[{"alert":"..","risk":"..","url":".."}]}]}
    findings = []
    sites = data.get("site", []) if isinstance(data, dict) else []
    alerts = []
    for s in sites:
        alerts.extend(s.get("alerts", []))
    if not alerts and isinstance(data, dict):
        alerts = data.get("alerts", [])
    for al in alerts:
        name = al.get("alert", "")
        risk = al.get("risk", "")
        url = al.get("url", "")
        findings.append({
            "type": f"ZAP_{name}".upper().replace(" ", "_"),
            "title": name,
            "severity": _sev_map(risk),
            "location": url,
            "detail": (al.get("desc") or "")[:200],
            "evidence": al.get("evidence", ""),
            "source": "ZAP",
            "compliance": [f"CWE-{al['cweid']}"] if al.get("cweid") else [],
        })
    return findings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--signals-dir", default="signals", help="质量信号输出目录（默认 ./signals）")
    args = ap.parse_args()

    if args.report.lower().endswith(".xml"):
        findings = parse_xml(args.report)
    else:
        findings = parse_json(args.report)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"findings": findings}, f, ensure_ascii=False, indent=2)
    # 质量信号契约：存在 Critical/High 安全项 → blocking 信号
    high = [x for x in findings if str(x.get("severity", "")).lower() in ("critical", "high")]
    if high:
        emit_signal("qa-security-scan", [{
            "signal": "security_finding", "severity": "high", "count": len(high),
            "blocking": True, "detail_ref": args.out,
        }], args.signals_dir)
    print(f"[OK] 已解析 ZAP 报告: {args.out}（{len(findings)} 项）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
