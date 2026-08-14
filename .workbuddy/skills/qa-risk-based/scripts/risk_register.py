#!/usr/bin/env python3
"""基于风险的测试（RBT）量化：Risk = Impact × Probability，反推测试密度。

Usage:
    python scripts/risk_register.py --risks risks.json --out risk_register.md --csv risk_register.csv

risks.json: [{"id":"R1","area":"支付","impact":5,"probability":4,"note":"..."}, ...]
impact / probability 取 1~5。risk_score = impact * probability (1~25)。
"""
import argparse
import csv
import json
import os
import sys
from datetime import datetime


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
# R-15：显式风险矩阵分带（Impact×Probability ∈ 1..25）
RISK_BANDS = [
    (20, "Critical", "风险分 ≥ 20（影响×概率双高，须最高测试密度）"),
    (12, "High",     "12 ≤ 风险分 < 20"),
    (6,  "Medium",   "6 ≤ 风险分 < 12"),
    (0,  "Low",      "风险分 < 6"),
]


def level_of(score):
    for threshold, lvl, _ in RISK_BANDS:
        if score >= threshold:
            return lvl
    return "Low"


def density_of(level):
    return {
        "Critical": "穷尽用例 + 全量回归 + 兼容性全测 + 探索性重点",
        "High": "重点用例 + 回归 + 兼容性优先组合",
        "Medium": "正常用例覆盖",
        "Low": "冒烟即可",
    }[level]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--risks", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--csv", help="CSV 输出")
    ap.add_argument("--signals-dir", default="signals", help="质量信号输出目录（默认 ./signals）")
    ap.add_argument("--risk-appetite", type=int, default=20,
                    help="组织风险偏好阈值(1~25)；风险分高于此值记为『偏好突破』(⚠️)。默认 20")
    args = ap.parse_args()

    with open(args.risks, "r", encoding="utf-8-sig") as f:
        risks = json.load(f)

    rows = []
    for r in risks:
        impact = int(r.get("impact", 1))
        prob = int(r.get("probability", 1))
        score = impact * prob
        lvl = level_of(score)
        breach = score > args.risk_appetite
        rows.append({
            "id": r.get("id", ""),
            "area": r.get("area", ""),
            "impact": impact,
            "probability": prob,
            "risk_score": score,
            "level": lvl,
            "appetite_breach": breach,
            "appetite_mark": "⚠️" if breach else "",
            "density": density_of(lvl),
            "note": r.get("note", ""),
        })
    rows.sort(key=lambda x: x["risk_score"], reverse=True)

    lines = ["# 风险登记册（Risk Register / RBT）\n",
             "| 风险ID | 区域 | 影响 | 概率 | 风险分 | 定级 | 偏好突破 | 测试密度建议 | 说明 |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        lines.append(f"| {r['id']} | {r['area']} | {r['impact']} | {r['probability']} | "
                     f"{r['risk_score']} | {r['level']} | {r['appetite_mark']} | {r['density']} | {r['note']} |")
    lines.append(f"\n**统计**：Critical={sum(1 for r in rows if r['level']=='Critical')} "
                 f"High={sum(1 for r in rows if r['level']=='High')} "
                 f"Medium={sum(1 for r in rows if r['level']=='Medium')} "
                 f"Low={sum(1 for r in rows if r['level']=='Low')}")
    # R-15：输出显式风险矩阵分带，便于审计与对齐
    lines.append("\n**风险矩阵分带（Impact×Probability）**：")
    lines.append("| 定级 | 阈值 | 说明 |")
    lines.append("| --- | --- | --- |")
    for threshold, lvl, desc in RISK_BANDS:
        lines.append(f"| {lvl} | ≥ {threshold} | {desc} |")
    n_breach = sum(1 for r in rows if r["appetite_breach"])
    lines.append(f"\n**风险偏好(RA)**：阈值 = {args.risk_appetite}"
                 f"（风险分高于此值标记 ⚠️ 偏好突破）；本次突破项 = {n_breach}")
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[OK] 风险登记册: {args.out}（{len(rows)} 项，偏好突破 {n_breach} 项）")

    if args.csv:
        with open(args.csv, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["id", "area", "impact", "probability",
                                              "risk_score", "level", "appetite_breach",
                                              "density", "note"])
            w.writeheader()
            for r in rows:
                w.writerow(r)
        print(f"[OK] 已生成 CSV: {args.csv}")

    # 质量信号契约：高风险项存在时写入非阻断信号，供门禁聚合可见
    n_crit = sum(1 for r in rows if r["level"] == "Critical")
    n_high = sum(1 for r in rows if r["level"] == "High")
    signals = []
    if n_crit or n_high:
        signals.append({
            "signal": "high_risk_present", "severity": "high",
            "count": n_crit + n_high, "blocking": False,
            "detail_ref": args.out,
        })
    # R-15：偏好突破信号（暴露风险偏好，非阻断、供可见）
    if n_breach:
        signals.append({
            "signal": "risk_appetite_breach", "severity": "high",
            "count": n_breach, "blocking": False,
            "risk_appetite": args.risk_appetite,
            "detail_ref": args.out,
        })
    if signals:
        emit_signal("qa-risk-based", signals, args.signals_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
