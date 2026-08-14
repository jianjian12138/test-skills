#!/usr/bin/env python3
"""Backfill the requirements traceability matrix from generated cases + test results.

修复 P0-C「追溯矩阵开环」：gen_trace_matrix.py 只生成「待补充/未覆盖」骨架，从不被回写。
本脚本消费真实用例（含 req_id）与执行结果，回填「测试点 / 用例ID / 执行结果 / 状态」，
并输出需求覆盖率，可纳入发布门禁（覆盖率不达标 → 禁止发布）。

Usage:
    python scripts/update_trace.py \
        --trace trace_matrix.csv \
        --cases cases.json \
        --results results.json \
        --out trace_matrix.filled.csv [--md trace_matrix.filled.md] \
        [--fail-on-uncovered]

cases.json:  [{"id":"C1","req_id":"R1","title":"...", ...}, ...]
results.json: {"C1":"pass","C2":"fail", ...}  # 用例ID -> pass/fail
"""
import argparse
import csv
import json
import sys

FIELDS = ["需求ID", "模块", "需求", "测试点", "用例ID", "执行结果", "状态"]


def load_cases(path):
    if not path:
        return {}
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            cases = json.load(f)
    except Exception as e:
        print(f"[WARN] 读取 cases 失败: {e}", file=sys.stderr)
        return {}
    by_req = {}
    for c in cases:
        rid = c.get("req_id")
        if rid:
            by_req.setdefault(rid, []).append(c)
    return by_req


def load_results(path):
    if not path:
        return {}
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARN] 读取 results 失败: {e}", file=sys.stderr)
        return {}


def backfill(trace_rows, by_req, results):
    out = []
    for row in trace_rows:
        rid = row.get("需求ID", "")
        cases = by_req.get(rid, [])
        if not cases:
            row["测试点"] = "待补充"
            row["用例ID"] = "待补充"
            row["执行结果"] = "待执行"
            row["状态"] = "未覆盖"
            out.append(row)
            continue
        titles = [c.get("title", c.get("id", "")) for c in cases]
        ids = [c.get("id", "") for c in cases]
        row["测试点"] = "; ".join(str(t) for t in titles)
        row["用例ID"] = "; ".join(str(i) for i in ids)
        if results:
            states = [results.get(i, "unknown") for i in ids]
            passed = sum(1 for s in states if s == "pass")
            failed = sum(1 for s in states if s == "fail")
            if failed:
                row["执行结果"] = f"{passed}通过/{failed}失败"
                row["状态"] = "已执行(有失败)"
            elif passed:
                row["执行结果"] = f"{passed}通过"
                row["状态"] = "已覆盖"
            else:
                row["执行结果"] = "待执行"
                row["状态"] = "已设计"
        else:
            row["执行结果"] = "待执行"
            row["状态"] = "已设计"
        out.append(row)
    return out


def render_md(rows):
    lines = ["# 需求可追溯矩阵（已回填）\n",
             "| " + " | ".join(FIELDS) + " |",
             "| " + " | ".join(["---"] * len(FIELDS)) + " |"]
    for r in rows:
        lines.append("| " + " | ".join(str(r.get(f, "")) for f in FIELDS) + " |")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trace", required=True, help="现有追溯矩阵 CSV")
    ap.add_argument("--cases", help="用例 JSON（含 req_id）")
    ap.add_argument("--results", help="执行结果 JSON（用例ID->pass/fail）")
    ap.add_argument("--out", required=True, help="回填后 CSV 输出")
    ap.add_argument("--md", help="回填后 Markdown 输出（可选）")
    ap.add_argument("--fail-on-uncovered", action="store_true",
                    help="存在未覆盖需求时 sys.exit(1)")
    args = ap.parse_args()

    with open(args.trace, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = [dict(r) for r in reader]

    by_req = load_cases(args.cases)
    results = load_results(args.results)
    filled = backfill(rows, by_req, results)

    with open(args.out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(filled)

    total = len(filled)
    covered = sum(1 for r in filled if r["状态"] in ("已覆盖", "已执行(有失败)"))
    designed = sum(1 for r in filled if r["状态"] == "已设计")
    uncovered = [r["需求ID"] for r in filled if r["状态"] == "未覆盖"]
    rate = (covered / total * 100) if total else 0.0

    print(f"[OK] 已回填追溯矩阵: {args.out}")
    print(f"[STAT] 需求总数={total} 已覆盖={covered} 已设计={designed} 未覆盖={len(uncovered)} 覆盖率={rate:.1f}%")
    if uncovered:
        print(f"[WARN] 未覆盖需求: {', '.join(uncovered)}")

    if args.md:
        with open(args.md, "w", encoding="utf-8") as f:
            f.write(render_md(filled))
        print(f"[OK] 已生成 Markdown: {args.md}")

    if args.fail_on_uncovered and uncovered:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
