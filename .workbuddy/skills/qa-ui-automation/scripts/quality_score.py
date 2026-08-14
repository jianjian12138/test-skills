#!/usr/bin/env python3
"""Web UI 自动化五维质量评分 + 失败分桶（学 playwright-e2e-builder 方法论）。

Usage:
    python scripts/quality_score.py --input ui_inventory.json --out ui_score.md

ui_inventory.json（各维度事实来源，由 Screen Model / 路由 / 接口清单汇总）：
{
  "screens":   [{"name":"登录","has_case":true,"locator_health":0.9}],
  "behaviors": [{"name":"筛选","covered":true}, {"name":"创建","covered":false}],
  "endpoints": [{"name":"/api/login","touched":true}],
  "journeys":  [{"name":"下单","has_spec":true}],
  "failures":  [{"type":"targeting","case":"登录"}, {"type":"timing","case":"下单"}]
}

五维（均归一到 0~100，权重可按需调整）：
  screen   页面是否有关联 case
  behavior  渲染/筛选/创建/校验等行为是否覆盖
  endpoint  接口依赖是否被 case 或 mock 触及
  journey   跨页流程是否有场景 spec
  locator   定位健康度（能否支撑长期维护）
composite（文章①哲学）：composite < 阈值(默认70) 不强行当流水线硬门槛，但强制「按 gaps 补测」。
失败分桶 triage：targeting / timing / session，先按桶修再重跑。
"""
import argparse
import json
import os
import sys
from datetime import datetime

WEIGHTS = {"screen": 0.2, "behavior": 0.25, "endpoint": 0.2, "journey": 0.2, "locator": 0.15}
PASS_LINE = 70


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
def dim_screen(screens):
    if not screens:
        return 0.0
    return 100.0 * sum(1 for s in screens if s.get("has_case")) / len(screens)


def dim_behavior(behaviors):
    if not behaviors:
        return 0.0
    return 100.0 * sum(1 for b in behaviors if b.get("covered")) / len(behaviors)


def dim_endpoint(endpoints):
    if not endpoints:
        return 0.0
    return 100.0 * sum(1 for e in endpoints if e.get("touched")) / len(endpoints)


def dim_journey(journeys):
    if not journeys:
        return 0.0
    return 100.0 * sum(1 for j in journeys if j.get("has_spec")) / len(journeys)


def dim_locator(screens):
    if not screens:
        return 0.0
    vals = [float(s.get("locator_health", 0)) for s in screens]
    return 100.0 * sum(min(v, 1.0) for v in vals) / len(vals)


def triage(failures):
    buckets = {"targeting": 0, "timing": 0, "session": 0, "other": 0}
    for f in failures or []:
        t = f.get("type", "other")
        buckets[t if t in buckets else "other"] += 1
    return buckets


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--pass-line", type=float, default=PASS_LINE)
    ap.add_argument("--signals-dir", default="signals", help="质量信号输出目录（默认 ./signals）")
    args = ap.parse_args()

    with open(args.input, "r", encoding="utf-8-sig") as f:
        inv = json.load(f)

    dims = {
        "screen": dim_screen(inv.get("screens", [])),
        "behavior": dim_behavior(inv.get("behaviors", [])),
        "endpoint": dim_endpoint(inv.get("endpoints", [])),
        "journey": dim_journey(inv.get("journeys", [])),
        "locator": dim_locator(inv.get("screens", [])),
    }
    composite = sum(dims[k] * WEIGHTS[k] for k in dims)
    buckets = triage(inv.get("failures", []))

    lines = ["# Web UI 自动化质量评分（五维 scorecard）\n",
             "| 维度 | 权重 | 得分(0~100) | 加权 |",
             "| --- | --- | --- | --- |"]
    for k in dims:
        lines.append(f"| {k} | {WEIGHTS[k]:.2f} | {dims[k]:.1f} | {dims[k]*WEIGHTS[k]:.2f} |")
    lines.append(f"\n**综合分 composite：{composite:.1f}**（阈值 {args.pass_line}）")
    if composite < args.pass_line:
        lines.append(f"⚠️ composite < {args.pass_line}：**不强行当硬门槛，但必须按 gaps 补测后重评**。")
    else:
        lines.append("✅ 综合分达标。")

    if buckets:
        lines.append("\n## 失败分桶（triage，先按桶修再重跑）\n")
        for b, c in buckets.items():
            if c:
                hint = {
                    "targeting": "优先改定位与 Screen Model",
                    "timing": "查等待与异步",
                    "session": "查登录态/权限夹具",
                }.get(b, "人工研判")
                lines.append(f"- {b}: {c} 例 → {hint}")
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    # 质量信号契约：综合分 < 及格线 → blocking 信号，门禁据此按 gaps 补测后重评
    if composite < args.pass_line:
        emit_signal("qa-ui-automation", [{
            "signal": "ui_quality_gate", "severity": "high", "count": 1,
            "blocking": True, "detail_ref": args.out,
        }], args.signals_dir)
    print(f"[OK] UI 五维评分: {args.out}  composite={composite:.1f}"
          f"  {'⚠️需补测' if composite < args.pass_line else '✅达标'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
