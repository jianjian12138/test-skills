#!/usr/bin/env python3
"""Deterministic local scanner for leaked secrets and PII in source/text files.

Read-only. Reports file:line:type:masked-match. Never modifies files.

Usage:
    python scripts/scan_secrets.py --path ./src --out secrets_findings.json
    python scripts/scan_secrets.py --path ./src --text    # print to stdout
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime

# (type, compiled regex, severity) — secret 类为高危 blocking，PII 类为中等非阻断
PATTERNS = [
    ("AWS_ACCESS_KEY", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("AWS_SECRET", re.compile(r"(?i)aws_secret_access_key\s*[:=]\s*['\"][A-Za-z0-9/+=]{40}['\"]")),
    ("GITHUB_TOKEN", re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}")),
    ("PRIVATE_KEY", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("SLACK_TOKEN", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("PASSWORD_ASSIGN", re.compile(r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"][^'\"\s]{6,}['\"]")),
    ("API_KEY_ASSIGN", re.compile(r"(?i)(api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token)\s*[:=]\s*['\"][^'\"\s]{8,}['\"]")),
    ("CN_MOBILE", re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")),
    ("CN_IDCARD", re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)")),
    ("EMAIL", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    ("BANK_CARD", re.compile(r"(?<!\d)\d{16,19}(?!\d)")),
]

# 高危（密钥/凭据泄露）→ 发布门禁 blocking；PII 类 → 中等非阻断，仅记录
SECRET_TYPES = {
    "AWS_ACCESS_KEY", "AWS_SECRET", "GITHUB_TOKEN", "PRIVATE_KEY",
    "SLACK_TOKEN", "PASSWORD_ASSIGN", "API_KEY_ASSIGN",
}


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
# Files / dirs to skip
SKIP_DIRS = {".git", "node_modules", "venv", "__pycache__", ".workbuddy", "dist", "build"}
TEXT_EXT = {".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rb", ".php",
            ".json", ".yaml", ".yml", ".env", ".txt", ".md", ".xml", ".html",
            ".sql", ".sh", ".properties", ".conf", ".ini", ".toml", ".csv"}


def _mask(s: str) -> str:
    s = s.strip()
    if len(s) <= 6:
        return s[:2] + "***"
    return s[:2] + "***" + s[-2:]


def scan_file(path: str):
    findings = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except (UnicodeDecodeError, OSError):
        return findings
    for ln, text in enumerate(lines, 1):
        for ftype, rx in PATTERNS:
            for m in rx.finditer(text):
                findings.append({
                    "file": path,
                    "line": ln,
                    "type": ftype,
                    "match": _mask(m.group(0)),
                    "snippet": text.strip()[:160],
                })
    return findings


def scan_tree(root: str):
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            ext = os.path.splitext(fn)[1].lower()
            if ext not in TEXT_EXT:
                continue
            full = os.path.join(dirpath, fn)
            out.extend(scan_file(full))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", required=True, help="file or directory to scan")
    ap.add_argument("--out")
    ap.add_argument("--text", action="store_true", help="print to stdout")
    ap.add_argument("--signals-dir", default="signals",
                    help="质量信号输出目录（接发布门禁，默认 ./signals）")
    args = ap.parse_args()

    if os.path.isfile(args.path):
        findings = scan_file(args.path)
    elif os.path.isdir(args.path):
        findings = scan_tree(args.path)
    else:
        print(f"[ERROR] path not found: {args.path}", file=sys.stderr)
        return 2

    # de-dup by (file,line,type,match)
    seen = set()
    uniq = []
    for f in findings:
        k = (f["file"], f["line"], f["type"], f["match"])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(f)

    # summary by type
    summary = {}
    for f in uniq:
        summary[f["type"]] = summary.get(f["type"], 0) + 1

    result = {"total": len(uniq), "summary": summary, "findings": uniq}

    if args.text or not args.out:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"[OK] 扫描完成：{len(uniq)} 处命中，已写入 {args.out}")
        if summary:
            print("  按类型：" + "，".join(f"{k}={v}" for k, v in summary.items()))

    # ---- 质量信号契约（RK-01 修复：零依赖自带扫描器必须真出信号 + fail-closed）----
    # 每次运行都产出一条信号：干净运行→verified（blocking:false），泄露→blocking（rc=1）。
    high = [f for f in uniq if f["type"] in SECRET_TYPES]
    sigs = []
    if high:
        sigs.append({
            "signal": "secret_leak", "severity": "high", "count": len(high),
            "blocking": True, "detail": "发现疑似密钥/凭据泄露",
            "types": sorted({f["type"] for f in high}),
        })
    else:
        # 干净或无高危：产出 verified 信号（blocking:false），使发布门禁能区分
        # “跑了且过” vs “没跑”，消除 DEFAULT_REQUIRED 误杀（RK-02）。
        sigs.append({
            "signal": "secret_scan_verified", "severity": "info",
            "count": len(uniq), "blocking": False,
            "verdict": "no_findings" if not uniq else "pii_only",
        })
    emit_signal("qa-security-scan", sigs, args.signals_dir)

    # 高危密钥泄露 → 非零退出（fail-closed）；其余静默通过。
    return 1 if high else 0


if __name__ == "__main__":
    sys.exit(main())
