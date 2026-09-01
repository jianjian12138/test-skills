#!/usr/bin/env python3
"""Compare multiple test rounds into a trend report (pass rate / defects).

Usage:
    python scripts/trend_compare.py --csv rounds.csv --out trend.md

rounds.csv columns: round,total,passed,failed,blocked,defects_open,defects_closed
"""
import argparse
import csv
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="多轮汇总 CSV")
    ap.add_argument("--out", required=True, help="趋势 Markdown")
    args = ap.parse_args()

    try:
        with open(args.csv, "r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
    except Exception as e:
        print(f"[ERROR] 读取失败: {e}", file=sys.stderr)
        return 2
    if not rows:
        print("[ERROR] 无数据", file=sys.stderr)
        return 2

    lines = ["# 多轮测试趋势对比\n",
             "| 轮次 | 总数 | 通过 | 失败 | 阻塞 | 通过率 | 缺陷(开/关) |",
             "| --- | --- | --- | --- | --- | --- | --- |"]
    prev_rate = None
    for r in rows:
        total = int(r.get("total", 0) or 0)
        passed = int(r.get("passed", 0) or 0)
        blocked = int(r.get("blocked", 0) or 0)
        rate = (passed / (total - blocked)) * 100 if (total - blocked) > 0 else 0
        do = r.get("defects_open", "0")
        dc = r.get("defects_closed", "0")
        trend = ""
        if prev_rate is not None:
            diff = rate - prev_rate
            trend = " ↑" if diff > 0.5 else (" ↓" if diff < -0.5 else " →")
        prev_rate = rate
        lines.append(f"| {r.get('round')} | {total} | {passed} | {r.get('failed')} | "
                     f"{blocked} | {rate:.1f}%{trend} | {do}/{dc} |")

    # verdict
    last = rows[-1]
    last_total = int(last.get("total", 0) or 0)
    last_blocked = int(last.get("blocked", 0) or 0)
    last_rate = (int(last.get("passed", 0) or 0) / (last_total - last_blocked)) * 100 \
        if (last_total - last_blocked) > 0 else 0
    lines.append("")
    lines.append("## 结论\n")
    lines.append(f"- 最新轮通过率：**{last_rate:.1f}%**")
    lines.append("- 通过率持续上升且缺陷收敛 → 质量向好，可考虑发布。" if last_rate >= 95
                 else "- 通过率未达 95% 或缺陷未收敛 → 需继续修复与回归。")
    md = "\n".join(lines) + "\n"
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"[OK] 已生成趋势报告: {args.out}（{len(rows)} 轮）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
