#!/usr/bin/env python3
"""qa-synthetic-monitoring: 合成监控规格治理门禁。
校验合成监控旅程规格是否「受治理」：每个业务关键旅程必须有断言(预期状态/文本)、告警阈值与探测频率；
缺失 → 产出 blocking 信号（避免无断言/无告警的"哑"监控上线后漏报）。
诚实边界：本技能校验监控规格治理完整性，不实际对生产发起探测（无网络依赖）。实际探测由黑盒/ATS 在受控环境执行。
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



def evaluate(spec):
    findings = []
    for j in spec.get("journeys", []):
        name = j.get("name", "<unnamed>")
        crit = bool(j.get("business_critical", False))
        steps = j.get("steps", [])
        if steps:
            lacks_assert = any(("expected_status" not in s and "expected_text" not in s) for s in steps)
        else:
            lacks_assert = True
        lacks_alert = crit and ("alert_p95_s" not in j and not any("alert_p95_s" in s for s in steps))
        lacks_freq = not j.get("frequency")

        issues = []
        if not steps:
            issues.append("无探测步骤")
        if lacks_assert:
            issues.append("缺断言(expected_status/expected_text)")
        if lacks_alert:
            issues.append("缺告警阈值(alert_p95_s)")
        if lacks_freq:
            issues.append("缺探测频率(frequency)")
        if issues:
            sev = "critical" if crit else "high"
            findings.append({
                "journey": name,
                "severity": sev,
                "detail": "旅程[{}]: {}".format(name, "; ".join(issues)),
            })
    return findings


def main():
    ap = argparse.ArgumentParser(description="合成监控规格治理门禁")
    ap.add_argument("--spec", required=True, help="合成监控规格 JSON")
    ap.add_argument("--out", required=True, help="signals/ 输出目录")
    ap.add_argument("--fail-on", action="store_true", help="存在未治理关键旅程时 sys.exit(1)")
    args = ap.parse_args()
    # AR-01：--out 绝对化，确保信号落点不依赖调用方 CWD（fail-closed 确定性）。
    args.out = os.path.abspath(args.out)

    spec = load_json(args.spec)
    findings = evaluate(spec)
    blocking = [f for f in findings if f["severity"] == "critical"]

    if blocking:
        emit_signal("qa-synthetic-monitoring", [{
            "signal": "monitor_ungoverned",
            "severity": "critical",
            "count": len(blocking),
            "blocking": True,
            "detail": "{} 个业务关键监控旅程未受治理(缺断言/告警)".format(len(blocking)),
        }], args.out)
        print("qa-synthetic-monitoring: BLOCKING — {} 个未治理关键旅程".format(len(blocking)))
        if args.fail_on:
            sys.exit(1)
    elif findings:
        emit_signal("qa-synthetic-monitoring", [{
            "signal": "monitor_governed",
            "severity": "high",
            "count": len(findings),
            "blocking": False,
            "detail": "{} 个非关键旅程待补治理字段".format(len(findings)),
        }], args.out)
        print("qa-synthetic-monitoring: OK — 待补={}".format(len(findings)))
    else:
        print("qa-synthetic-monitoring: OK — 治理完整")
    sys.exit(0)


if __name__ == "__main__":
    main()
