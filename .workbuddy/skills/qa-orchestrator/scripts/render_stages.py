#!/usr/bin/env python3
"""由 stages.json 渲染生命周期路由表 Markdown（单一事实源，避免文档层漂移）。

Usage:
    python scripts/render_stages.py [--stages stages.json] [--out stages_table.md]

输出的表格可直接粘贴进 qa-orchestrator/SKILL.md 的「生命周期路由表」一节。
cross_cutting 中的技能单独列出为「横切关注点」。
"""
import argparse
import json
import sys


def render(stages_doc):
    stages = stages_doc.get("stages", [])
    cross = stages_doc.get("cross_cutting", [])
    lines = ["## 生命周期路由表（由 stages.json 自动渲染，单一事实源）", "",
             "| 阶段目录 | 对应技能 | 关键产出 |", "| --- | --- | --- |"]
    for st in stages:
        combined = list(st.get("skills", []))
        for a in st.get("alternates", []):
            if a not in combined:
                combined.append(a)
        skill_cell = " · ".join(combined)
        arts = " / ".join(st.get("artifacts", []))
        lines.append(f"| `{st['dir']}/` | {skill_cell} | {arts} |")
    if cross:
        lines.append("")
        lines.append("### 横切关注点（贯穿全程，不属单一阶段）")
        lines.append("")
        lines.append("| 技能 | 角色 |")
        lines.append("| --- | --- |")
        role = {
            "qa-risk-based": "基于风险的测试（RBT），前置量化风险并反推用例密度",
            "qa-test-strategy": "测试策略制定",
            "qa-ci": "CI 集成与门禁接线",
        }
        for c in cross:
            lines.append(f"| `{c}` | {role.get(c, '横切活动')} |")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stages", default="stages.json")
    ap.add_argument("--out")
    args = ap.parse_args()
    try:
        with open(args.stages, "r", encoding="utf-8") as f:
            doc = json.load(f)
    except Exception as e:
        print(f"[ERROR] 读取 {args.stages} 失败: {e}", file=sys.stderr)
        return 2
    md = render(doc)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"[OK] 已渲染路由表: {args.out}")
    else:
        print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
