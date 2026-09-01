#!/usr/bin/env python3
"""Rate a bug's severity from impact x likelihood (or direct S-level).

Usage:
    python scripts/rate_severity.py --impact block --likelihood high --out sev.md
    python scripts/rate_severity.py --impact major --likelihood med --cwe "CWE-79" --epss 0.3

Matrix (impact x likelihood -> S-level):
  impact: block(阻断) / major(严重) / minor(一般) / trivial(提示)
  likelihood: high / med / low
"""
import argparse
import json
import os
import sys
from datetime import datetime

MATRIX = {
    ("block", "high"): "S1-致命", ("block", "med"): "S1-致命", ("block", "low"): "S2-严重",
    ("major", "high"): "S2-严重", ("major", "med"): "S2-严重", ("major", "low"): "S3-一般",
    ("minor", "high"): "S3-一般", ("minor", "med"): "S3-一般", ("minor", "low"): "S4-提示",
    ("trivial", "high"): "S4-提示", ("trivial", "med"): "S4-提示", ("trivial", "low"): "S4-提示",
}

SUGGEST = {
    "S1-致命": "立即修复，阻塞发布，需负责人介入。",
    "S2-严重": "上线前必须修复，优先排期。",
    "S3-一般": "本迭代内修复并回归。",
    "S4-提示": "登记 backlog，按节奏处理。",
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
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--impact", required=True, choices=["block", "major", "minor", "trivial"])
    ap.add_argument("--likelihood", required=True, choices=["high", "med", "low"])
    ap.add_argument("--cwe", help="关联 CWE，用于上下文说明")
    ap.add_argument("--epss", type=float, help="被利用概率 0~1，影响修复优先级")
    ap.add_argument("--out", help="输出 Markdown")
    ap.add_argument("--signals-dir", default="signals", help="质量信号输出目录（默认 ./signals）")
    args = ap.parse_args()

    level = MATRIX.get((args.impact, args.likelihood), "S3-一般")
    note = SUGGEST.get(level, "")
    lines = ["# 缺陷严重级判定\n",
             f"- 影响（impact）：{args.impact}",
             f"- 可能性（likelihood）：{args.likelihood}",
             f"- **严重级：{level}**",
             f"- 处理建议：{note}"]
    if args.cwe:
        lines.append(f"- 关联：{args.cwe}")
    if args.epss is not None:
        pr = "高" if args.epss >= 0.1 else ("中" if args.epss >= 0.01 else "低")
        lines.append(f"- EPSS 利用概率：{args.epss*100:.1f}%（{pr}）→ "
                     f"{'建议提前修复' if args.epss >= 0.1 else '按级别常规排期'}")
    md = "\n".join(lines) + "\n"
    print(md.strip())
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"[OK] 已写出: {args.out}")
    # 质量信号契约：判定为 S1/S2 致命/严重 → blocking 信号，门禁据此阻塞发布
    if level in ("S1-致命", "S2-严重"):
        emit_signal("qa-bug-report", [{
            "signal": "open_critical_bug", "severity": "critical", "count": 1,
            "blocking": True, "detail_ref": args.out or "stdout",
        }], args.signals_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
