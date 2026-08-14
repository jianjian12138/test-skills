#!/usr/bin/env python3
"""Generate an execution progress matrix (Markdown) from cases+results JSON.

Usage:
    python scripts/gen_matrix.py --cases cases.json --out matrix.md
"""
import argparse
import json
import sys
from collections import defaultdict

STATUS_ORDER = ["passed", "failed", "blocked", "notrun"]
STATUS_CN = {"passed": "通过", "failed": "失败", "blocked": "阻塞", "notrun": "未执行"}

ROUTE = {
    ("api", "failed"): "qa-bug-report（功能缺陷）",
    ("ui", "failed"): "qa-bug-report（功能缺陷）",
    ("perf", "failed"): "qa-perf-analysis（先归因）",
    ("security", "failed"): "qa-security-report（安全缺陷）",
    ("blocked", None): "跟进依赖/环境",
}


def render(data: dict) -> str:
    change = data.get("change", "-")
    cases = data.get("cases", [])
    lines = []
    lines.append(f"# 测试执行进度矩阵：{change}\n")

    total = len(cases)
    by_status = defaultdict(int)
    for c in cases:
        by_status[c.get("status", "notrun")] += 1
    executed = total - by_status["notrun"]
    passed = by_status["passed"]
    rate = (passed / executed * 100) if executed else 0

    lines.append("## 总览\n")
    lines.append(f"- 用例总数：**{total}**")
    lines.append(f"- 已执行：{executed} ｜ 未执行：{by_status['notrun']}")
    lines.append(f"- 通过率（已执行）：**{rate:.1f}%**")
    for s in STATUS_ORDER:
        lines.append(f"- {STATUS_CN[s]}：{by_status[s]}")
    lines.append("")

    # 模块 x 类型 交叉
    cross = defaultdict(lambda: defaultdict(int))
    for c in cases:
        cross[c.get("module", "-")][c.get("type", "-")] += 1
    types = sorted({c.get("type", "-") for c in cases})
    lines.append("## 模块 × 类型 分布\n")
    head = "| 模块 | " + " | ".join(types) + " | 合计 |"
    sep = "| --- | " + " | ".join(["---"] * len(types)) + " | --- |"
    lines.append(head)
    lines.append(sep)
    for m in sorted(cross):
        row = [str(cross[m].get(t, 0)) for t in types]
        tot = sum(int(x) for x in row)
        lines.append(f"| {m} | " + " | ".join(row) + f" | {tot} |")
    lines.append("")

    # 失败/阻塞路由
    lines.append("## 失败 / 阻塞 路由建议\n")
    routed = False
    for c in cases:
        st = c.get("status")
        tp = c.get("type")
        if st == "failed":
            target = ROUTE.get((tp, "failed"), "qa-bug-report")
            lines.append(f"- ❌ [{tp}] {c.get('module')}/{c.get('name')} → {target}")
            routed = True
        elif st == "blocked":
            lines.append(f"- ⛔ [{tp}] {c.get('module')}/{c.get('name')} → 跟进依赖/环境")
            routed = True
    if not routed:
        lines.append("- 无失败/阻塞项。")
    lines.append("")

    # 明细
    lines.append("## 逐用例明细\n")
    lines.append("| 模块 | 类型 | 用例 | 优先级 | 状态 | 负责人 | 备注 |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for c in cases:
        lines.append(f"| {c.get('module','-')} | {c.get('type','-')} | {c.get('name','-')} | "
                     f"{c.get('priority','-')} | {STATUS_CN.get(c.get('status','notrun'), c.get('status','-'))} | "
                     f"{c.get('owner','-')} | {c.get('result','')} |")
    lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    try:
        with open(args.cases, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[ERROR] 读取 cases 失败: {e}", file=sys.stderr)
        return 2
    md = render(data)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"[OK] 已生成执行矩阵: {args.out}（{len(data.get('cases', []))} 用例）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
