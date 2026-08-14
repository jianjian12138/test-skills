#!/usr/bin/env python3
"""Generate a requirements traceability matrix skeleton from a requirement list.

Usage:
    python scripts/gen_trace_matrix.py --reqs reqs.json --out matrix.csv --md matrix.md

reqs.json:
[
  {"id":"R1","title":"用户可登录","module":"账号"},
  {"id":"R2","title":"订单可被支付","module":"交易"}
]

Output: 每行 = 需求 → 测试点(待填) → 用例ID(待填) → 执行结果(待填) → 状态。
保证「每条需求都被测到」可追溯。
"""
import argparse
import csv
import json
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reqs", required=True, help="需求列表 JSON")
    ap.add_argument("--out", required=True, help="CSV 输出")
    ap.add_argument("--md", help="Markdown 输出")
    args = ap.parse_args()

    try:
        with open(args.reqs, "r", encoding="utf-8-sig") as f:
            reqs = json.load(f)
    except Exception as e:
        print(f"[ERROR] 读取需求失败: {e}", file=sys.stderr)
        return 2

    rows = [["需求ID", "模块", "需求", "测试点", "用例ID", "执行结果", "状态"]]
    for r in reqs:
        rows.append([r.get("id", ""), r.get("module", ""), r.get("title", ""),
                     "待补充", "待补充", "待执行", "未覆盖"])

    with open(args.out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerows(rows)
    print(f"[OK] 已生成追溯矩阵: {args.out}（{len(reqs)} 条需求）")

    if args.md:
        lines = ["# 需求可追溯矩阵\n",
                 "| 需求ID | 模块 | 需求 | 测试点 | 用例ID | 执行结果 | 状态 |",
                 "| --- | --- | --- | --- | --- | --- | --- |"]
        for r in rows[1:]:
            lines.append("| " + " | ".join(r) + " |")
        with open(args.md, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print(f"[OK] 已生成 Markdown: {args.md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
