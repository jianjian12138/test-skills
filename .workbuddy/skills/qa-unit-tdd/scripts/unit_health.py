#!/usr/bin/env python3
"""单元/TDD 方法学健康度评估：基于测试金字塔占比、覆盖率、失败用例、测试/代码比，
识别方法学失衡与门禁不达标，存在高危项时发阻断信号。零外部依赖（仅标准库）。"""
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


BLOCKING = {"critical", "high"}


def evaluate(m, min_cov, min_unit_ratio):
    unit = m.get("unit", 0) or 0
    integ = m.get("integration", 0) or 0
    e2e = m.get("e2e", 0) or 0
    total = unit + integ + e2e
    unit_ratio = unit / total if total else 0.0
    line_cov = m.get("line_coverage", 0) or 0.0
    failed = m.get("failed_tests", 0) or 0
    code_loc = m.get("code_loc", 0) or 0
    test_loc = m.get("test_loc", 0) or 0
    tcr = test_loc / code_loc if code_loc else 0.0

    findings = []
    if failed > 0:
        findings.append({"rule": "UT-FAIL", "severity": "critical",
                         "detail": f"存在 {failed} 个失败用例（红着上线）", "value": failed})
    if unit_ratio < min_unit_ratio:
        findings.append({"rule": "UT-PYRAMID", "severity": "high",
                         "detail": f"单元测试占比 {unit_ratio:.0%} < 门槛 {min_unit_ratio:.0%}（金字塔倒挂）",
                         "value": round(unit_ratio, 3)})
    if line_cov < min_cov:
        findings.append({"rule": "UT-COVERAGE", "severity": "high",
                         "detail": f"行覆盖率 {line_cov:.0%} < 门槛 {min_cov:.0%}", "value": round(line_cov, 3)})
    if tcr < 0.3:
        findings.append({"rule": "UT-TCR", "severity": "medium",
                         "detail": f"测试/代码比 {tcr:.2f} 偏低（建议 ≥0.3）", "value": round(tcr, 3)})

    blocking = [f for f in findings if f["severity"] in BLOCKING]
    n_block = len(blocking)
    N_DIM = 4  # 方法学维度总数
    score = max(0.0, 1.0 - n_block / N_DIM)
    return findings, n_block, bool(blocking), score, {
        "unit_ratio": round(unit_ratio, 3), "line_coverage": round(line_cov, 3),
        "tcr": round(tcr, 3), "failed": failed,
    }


def main():
    ap = argparse.ArgumentParser(description="单元/TDD 方法学健康度评估")
    ap.add_argument("--metrics", required=True, help="测试指标 JSON")
    ap.add_argument("--out", default="unit_health.md", help="报告输出路径")
    ap.add_argument("--signals-dir", default=None, help="信号输出目录（接门禁）")
    ap.add_argument("--min-coverage", type=float, default=0.7, help="行覆盖率门槛")
    ap.add_argument("--min-unit-ratio", type=float, default=0.6, help="单元测试占比门槛")
    ap.add_argument("--fail-on", action="store_true", help="存在高危项时 sys.exit(1)")
    args = ap.parse_args()

    m = load_json(args.metrics)
    findings, n_block, blocked, score, summ = evaluate(m, args.min_coverage, args.min_unit_ratio)

    lines = [
        "# 单元/TDD 方法学健康度报告",
        "",
        f"**结论：{'⛔ 方法学不健康，阻断' if blocked else '✅ 方法学健康'}**",
        "",
        f"- 单元测试占比：{summ['unit_ratio']:.0%}（门槛 {args.min_unit_ratio:.0%}）",
        f"- 行覆盖率：{summ['line_coverage']:.0%}（门槛 {args.min_coverage:.0%}）",
        f"- 测试/代码比：{summ['tcr']:.2f}",
        f"- 失败用例：{summ['failed']}",
        f"- 健康度趋势分：{score:.3f}（高危项 {n_block}/4）",
        "",
        "## 门禁明细",
        "",
        "| 规则 | 级别 | 说明 |",
        "| --- | --- | --- |",
    ]
    sev_map = {"UT-FAIL": "critical", "UT-PYRAMID": "high", "UT-COVERAGE": "high", "UT-TCR": "medium"}
    for r in ("UT-FAIL", "UT-PYRAMID", "UT-COVERAGE", "UT-TCR"):
        hit = next((f for f in findings if f["rule"] == r), None)
        if hit:
            lines.append(f"| {r} | {sev_map[r]} | {hit['detail']} |")
    lines.append("")

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    if blocked:
        blocking = [f for f in findings if f["severity"] in BLOCKING]
        top = "critical" if any(f["severity"] == "critical" for f in findings) else "high"
        emit_signal("qa-unit-tdd", [{
            "signal": "unit_health_low",
            "severity": top,
            "count": n_block,
            "blocking": True,
            "detail_ref": os.path.basename(args.out),
            "rules": sorted({f["rule"] for f in blocking}),
        }], args.signals_dir)
    else:
        # RK-02 修复：健康运行也须产出 verified 信号（blocking:false），使发布门禁
        # 能区分“跑了且过” vs “没跑”，消除 DEFAULT_REQUIRED 误杀。
        if args.signals_dir:
            emit_signal("qa-unit-tdd", [{
                "signal": "unit_health_verified",
                "severity": "info",
                "count": 0,
                "blocking": False,
                "detail_ref": os.path.basename(args.out),
                "verdict": "no_findings",
            }], args.signals_dir)

    print(f"[RESULT] unit_ratio={summ['unit_ratio']} cov={summ['line_coverage']} "
          f"failed={summ['failed']} blocked={blocked} score={score:.3f}")
    if args.fail_on and blocked:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
