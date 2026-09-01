#!/usr/bin/env python3
"""Generate a bug verification + regression plan (Markdown) from a fixed-bug JSON.

Usage:
    python scripts/gen_verify_plan.py --bug bug_fixed.json --out verify_plan.md
"""
import argparse
import json
import sys

RISK_DEPTH = {
    "high": "受影响模块全量 + 相邻模块冒烟",
    "medium": "受影响模块核心路径 + 接口回归",
    "low": "受影响模块冒烟",
}


def render(data: dict) -> str:
    lines = []
    lines.append(f"# 缺陷验证与回归计划：{data.get('title', data.get('bug_id', '-'))}\n")
    lines.append("## 基本信息\n")
    lines.append(f"- 缺陷ID：{data.get('bug_id', '-')}")
    lines.append(f"- 修复版本：{data.get('fix_version', '-')}")
    lines.append(f"- 风险：{data.get('risk', '-')}")
    lines.append(f"- 回归深度：{RISK_DEPTH.get(data.get('risk', 'medium'), '受影响模块核心路径')}")
    lines.append("")

    lines.append("## 一、验证清单（重跑原复现步骤）\n")
    lines.append("| # | 复现步骤 | 验收标准 | 结果 |")
    lines.append("| --- | --- | --- | --- |")
    steps = data.get("steps", [])
    acc = data.get("acceptance", [])
    for i, s in enumerate(steps, 1):
        a = acc[i - 1] if i - 1 < len(acc) else ""
        lines.append(f"| {i} | {s} | {a} | ☐ |")
    if not steps:
        lines.append("| - | （无步骤） | - | - |")
    lines.append("")

    lines.append("## 二、回归范围\n")
    aff = data.get("affected_modules", [])
    lines.append(f"**直接受影响模块**：{', '.join(aff) if aff else '-'}")
    lines.append(f"**相邻模块推导**：与 `{data.get('module','-')}` 有调用/数据关系的模块，需冒烟。")
    rel = data.get("related_cases", [])
    if rel:
        lines.append("\n**已知关联用例（必回归）**：")
        for c in rel:
            lines.append(f"- {c}")
    lines.append("")

    lines.append("## 三、准入结论模板\n")
    lines.append("```")
    lines.append("验证：☐ 全过 / ☐ 仍有问题")
    lines.append("回归：☐ 无新增失败 / ☐ 引入 N 个新问题")
    lines.append("结论：☐ 可关闭  /  ☐ 打回重改")
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bug", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    try:
        with open(args.bug, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[ERROR] 读取 bug 失败: {e}", file=sys.stderr)
        return 2
    md = render(data)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"[OK] 已生成验证计划: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
