#!/usr/bin/env python3
"""qa-chaos: 混沌实验治理门禁。
检查混沌实验规格是否「受治理」：业务关键实验必须定义稳态假设、终止条件、回退方案、爆炸半径。
未受治理的关键实验 → 产出 blocking 信号（避免在生产盲目注入故障）。
诚实边界：本技能只校验实验规格的治理完整性，不实际对目标系统注入故障（无基础设施/网络依赖）。
"""
import argparse
import os
import sys

try:
    from _common import emit_signal, load_json
except ImportError as _imp_err:
    import sys as _sys
    _sys.stderr.write(
        "FATAL: _common.py 缺失/损坏，技能不可用（fail-closed）\n")
    _sys.exit(2)


REQUIRED = ["fault", "target", "blast_radius", "steady_state", "abort_conditions", "fallback"]


def evaluate(spec):
    """返回 findings 列表，每条含 experiment/severity/detail。"""
    findings = []
    for exp in spec.get("experiments", []):
        name = exp.get("name", "<unnamed>")
        missing = [k for k in REQUIRED if not exp.get(k)]
        if not missing:
            continue
        critical = bool(exp.get("business_critical", False))
        sev = "critical" if critical else "high"
        findings.append({
            "experiment": name,
            "severity": sev,
            "detail": "实验[{}]缺少治理字段: {}".format(name, ", ".join(missing)),
        })
    return findings


def main():
    ap = argparse.ArgumentParser(description="混沌实验治理门禁")
    ap.add_argument("--spec", required=True, help="混沌实验规格 JSON")
    ap.add_argument("--out", required=True, help="signals/ 输出目录")
    ap.add_argument("--fail-on", action="store_true", help="存在未治理关键实验时 sys.exit(1)")
    args = ap.parse_args()
    # AR-01：--out 绝对化，确保信号落点不依赖调用方 CWD（fail-closed 确定性）。
    args.out = os.path.abspath(args.out)

    spec = load_json(args.spec)
    findings = evaluate(spec)
    blocking = [f for f in findings if f["severity"] == "critical"]

    if blocking:
        emit_signal("qa-chaos", [{
            "signal": "chaos_ungoverned",
            "severity": "critical",
            "count": len(blocking),
            "blocking": True,
            "detail": "{} 个业务关键混沌实验未受治理(缺稳态/终止/回退)".format(len(blocking)),
        }], args.out)
        print("qa-chaos: BLOCKING — {} 个未治理关键实验".format(len(blocking)))
        if args.fail_on:
            sys.exit(1)
    elif findings:
        emit_signal("qa-chaos", [{
            "signal": "chaos_governed",
            "severity": "high",
            "count": len(findings),
            "blocking": False,
            "detail": "{} 个非关键实验待补治理字段".format(len(findings)),
        }], args.out)
        print("qa-chaos: OK — 待补={}".format(len(findings)))
    else:
        print("qa-chaos: OK — 治理完整")
    sys.exit(0)


if __name__ == "__main__":
    main()
