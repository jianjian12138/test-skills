#!/usr/bin/env python3
"""移动端测试五维质量 rubric：加权打分（满分 100，<70 必须补全）。

Usage:
    python scripts/quality_rubric.py --input scores.json --out rubric.md

scores.json（各维度 0~1，或 0~100 均可，脚本自动归一化）：
{
  "runnable": 1.0,        # 可运行性
  "locator": 0.9,         # 定位健壮性（P0 无裸 XPath）
  "maintainable": 0.8,    # 可维护性（Screen/Flow 分层）
  "stable": 0.7,          # 稳定性（无 sleep，失败自动截图）
  "coverage": 0.6         # 覆盖透明度（有 manifest，报告标风险）
}

权重：可运行性25 / 定位健壮性25 / 可维护性20 / 稳定性15 / 覆盖透明度15。
总分 < 70 → 标红「必须补全」，不强行当流水线硬门槛（与 Web 五维门一致）。
"""
import argparse
import json
import os
import sys
from datetime import datetime

DIMS = [
    ("runnable", "可运行性", 25),
    ("locator", "定位健壮性", 25),
    ("maintainable", "可维护性", 20),
    ("stable", "稳定性", 15),
    ("coverage", "覆盖透明度", 15),
]
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
def to_100(v):
    v = float(v)
    if v <= 1.0:
        return v * 100
    return min(v, 100.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--signals-dir", default="signals", help="质量信号输出目录（默认 ./signals）")
    args = ap.parse_args()

    with open(args.input, "r", encoding="utf-8-sig") as f:
        scores = json.load(f)

    total = 0.0
    details = []
    for key, label, weight in DIMS:
        raw = scores.get(key)
        if raw is None:
            print(f"[warn] 缺少维度 {key}，按 0 计", file=sys.stderr)
            val = 0.0
        else:
            val = to_100(raw)
        contrib = val * weight / 100.0
        total += contrib
        details.append((label, weight, val, contrib))

    lines = ["# 移动端测试质量 rubric\n",
             "| 维度 | 权重 | 得分(0~100) | 加权贡献 |",
             "| --- | --- | --- | --- |"]
    for label, w, val, contrib in details:
        lines.append(f"| {label} | {w} | {val:.1f} | {contrib:.2f} |")
    lines.append(f"\n**总分：{total:.1f} / 100**")
    if total < PASS_LINE:
        lines.append(f"❌ 总分 < {PASS_LINE}，**必须补全**对应维度后再交付（不强行当硬门槛，但禁止带病上线）。")
    else:
        lines.append(f"✅ 总分 ≥ {PASS_LINE}，质量门达标。")
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[OK] 质量 rubric: {args.out}  总分={total:.1f}  {'❌需补全' if total < PASS_LINE else '✅达标'}")
    # 质量信号契约：总分 < 及格线 → blocking 信号，门禁据此禁止带病上线
    if total < PASS_LINE:
        emit_signal("qa-mobile-autotest", [{
            "signal": "mobile_quality_gate", "severity": "high", "count": 1,
            "blocking": True, "detail_ref": args.out,
        }], args.signals_dir)
    return 0 if total >= PASS_LINE else 2


if __name__ == "__main__":
    sys.exit(main())
