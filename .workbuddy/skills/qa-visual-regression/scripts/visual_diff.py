#!/usr/bin/env python3
"""视觉回归：对比基线快照与当前快照（DOM 结构 + 关键视觉属性），识别布局/结构/样式回归。
零外部依赖（仅标准库）。契合 signals 契约：存在布局级(high)回归时写 blocking 信号。

说明：本技能做「结构/属性快照」级 diff；像素级回归需接 Playwright screenshot + pixelmatch 等专业工具（见能力边界）。
"""
import argparse
from datetime import datetime
import json
import os
import sys

BLOCKING_SEVERITIES = {"critical", "high"}


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


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
LAYOUT_PROPS = {
    "display", "position", "top", "left", "right", "bottom", "width", "height",
    "flex_direction", "flex_wrap", "justify_content", "align_items", "grid_template",
    "visibility", "overflow", "float", "transform", "z_index", "margin", "padding",
}
TEXT_PROPS = {"text", "content", "value", "placeholder", "alt", "aria_label", "title"}


def classify(prop):
    if prop in LAYOUT_PROPS:
        return "high"
    # 文本/样式变化统一 medium，避免文案微调误伤
    return "medium"


def diff(base, cur, threshold):
    b_els = {e["id"]: e for e in base.get("elements", [])}
    c_els = {e["id"]: e for e in cur.get("elements", [])}
    findings = []
    checked = 0
    for eid in b_els:
        if eid not in c_els:
            findings.append({"rule": "VR-MISSING", "severity": "high", "id": eid,
                             "detail": "元素在回归版本中缺失", "change": "removed"})
            checked += 1
    for eid in c_els:
        if eid not in b_els:
            findings.append({"rule": "VR-ADDED", "severity": "high", "id": eid,
                             "detail": "回归版本新增元素（可能挤压布局）", "change": "added"})
            checked += 1
    for eid in b_els:
        if eid not in c_els:
            continue
        bp = b_els[eid].get("props", {})
        cp = c_els[eid].get("props", {})
        checked += 1
        for k in (set(bp) | set(cp)):
            bv, cv = bp.get(k), cp.get(k)
            if bv != cv:
                sev = classify(k)
                findings.append({"rule": "VR-PROP", "severity": sev, "id": eid, "prop": k,
                                 "detail": f"{k}: {bv} → {cv}", "change": "modified"})
    high = [f for f in findings if f["severity"] == "high"]
    n_high = len(high)
    blocked = n_high > threshold
    score = max(0.0, 1.0 - len(findings) / max(1, checked))
    return findings, n_high, blocked, score


def main():
    ap = argparse.ArgumentParser(description="视觉回归：快照 diff")
    ap.add_argument("--baseline", required=True, help="基线快照 JSON")
    ap.add_argument("--current", required=True, help="当前快照 JSON")
    ap.add_argument("--out", default="visual_report.md", help="报告输出路径")
    ap.add_argument("--signals-dir", default=None, help="信号输出目录（接门禁）")
    ap.add_argument("--threshold", type=int, default=0, help="允许的高危(high)回归数，超过则阻断")
    ap.add_argument("--fail-on", action="store_true", help="存在布局级回归时 sys.exit(1)")
    args = ap.parse_args()

    base = load_json(args.baseline)
    cur = load_json(args.current)
    findings, n_high, blocked, score = diff(base, cur, args.threshold)

    lines = [
        "# 视觉回归报告",
        "",
        f"**结论：{'⛔ 存在布局级回归，阻断' if blocked else '✅ 无布局级回归'}**",
        "",
        f"- 基线元素数：{len(base.get('elements', []))}",
        f"- 当前元素数：{len(cur.get('elements', []))}",
        f"- 回归项：{len(findings)}（高危 {n_high}）",
        f"- 回归趋势分：{score:.3f}",
        "",
        "⚠️ 能力边界：本技能为「结构/属性快照级」diff，**非像素级回归**。像素级回归需接 "
        "Playwright screenshot + pixelmatch（如 jest-image-snapshot）等专业工具。本结果仅证明 "
        "DOM 结构与关键视觉属性未退化，不保证逐像素一致；如需像素级门禁请在 CI 接入上述工具。",
        "",
        "## 回归明细",
        "",
        "| 元素 | 规则 | 级别 | 说明 |",
        "| --- | --- | --- | --- |",
    ]
    for f in findings:
        lines.append(f"| {f['id']} | {f['rule']} | {f['severity']} | {f['detail']} |")
    lines.append("")

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    if blocked:
        emit_signal("qa-visual-regression", [{
            "signal": "visual_regression",
            "severity": "high",
            "count": n_high,
            "blocking": True,
            "detail_ref": os.path.basename(args.out),
            "rules": sorted({f["rule"] for f in findings}),
        }], args.signals_dir)

    print(f"[RESULT] findings={len(findings)} high={n_high} blocked={blocked} score={score:.3f}")
    if args.fail_on and blocked:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
