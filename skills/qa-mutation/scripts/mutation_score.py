#!/usr/bin/env python3
"""变异测试分数计算：killed / (total - equivalent)，低于阈值发阻断信号。

零外部依赖（仅标准库）。契合 skills 系统的 signals 契约：
低于阈值时写 signals/qa-mutation.json 的 mutation_score_low（blocking=true）。
"""
import argparse
from datetime import datetime
import json
import os
import sys


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
def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def normalize_status(m):
    """将变异体归一为 killed / survived / timeout / equivalent。"""
    if "status" in m and m["status"]:
        return str(m["status"]).lower()
    if "killed" in m:  # 兼容旧式布尔
        return "killed" if m["killed"] else "survived"
    return "survived"


def main():
    ap = argparse.ArgumentParser(description="变异测试分数计算")
    ap.add_argument("--mutants", required=True, help="变异体清单 JSON")
    ap.add_argument("--out", default="mutation_report.md", help="报告输出路径")
    ap.add_argument("--signals-dir", default="signals", help="信号输出目录（接门禁）；缺省即写 signals/ 确保任何调用都落信号")
    ap.add_argument("--threshold", type=float, default=0.8, help="变异分数达标线，低于则阻断")
    ap.add_argument("--fail-on", action="store_true", help="未达标时 sys.exit(1)")
    args = ap.parse_args()

    mutants = load_json(args.mutants)
    if not isinstance(mutants, list):
        # 兼容 {mutants:[...]} 包装
        mutants = mutants.get("mutants", [])

    total = len(mutants)
    counts = {}
    for m in mutants:
        st = normalize_status(m)
        counts[st] = counts.get(st, 0) + 1

    killed = counts.get("killed", 0) + counts.get("timeout", 0)  # 超时按已杀死计
    equivalent = counts.get("equivalent", 0)
    no_coverage = counts.get("no_coverage", 0)  # R-08：无覆盖变异体不计入分母
    denom = total - equivalent - no_coverage
    EQUIV_CAP = 0.5  # equivalent 占比上限，超过触发人工复核

    signals = []
    if denom <= 0:
        # R-08：无有效可杀变异体（空清单 / 全等价 / 全无覆盖）→ 不得刷满 1.0，判阻断
        score = 0.0
        passed = False
        signals.append({
            "signal": "mutation_no_coverage", "severity": "critical", "count": total,
            "blocking": True, "detail_ref": os.path.basename(args.out),
            "score": 0.0, "threshold": args.threshold,
            "reason": "有效分母<=0（空清单/全等价/全无覆盖），不可宣称达标",
        })
    else:
        score = killed / denom
        passed = score >= args.threshold
        if not passed:
            signals.append({
                "signal": "mutation_score_low", "severity": "high",
                "count": denom - killed, "blocking": True,
                "detail_ref": os.path.basename(args.out),
                "score": round(score, 4), "threshold": args.threshold,
            })
    # equivalent 占比上限 → 人工复核（不阻断，标记需人工确认）
    if total > 0 and equivalent / total > EQUIV_CAP:
        signals.append({
            "signal": "mutation_equiv_review", "severity": "medium", "count": equivalent,
            "blocking": False, "detail_ref": os.path.basename(args.out),
            "reason": f"等价变异占比 {equivalent / total:.0%} 超过 {EQUIV_CAP:.0%} 上限，需人工复核等价判定",
        })

    lines = [
        "# 变异测试分数报告",
        "",
        f"**结论：{'✅ 达标' if passed else '⛔ 未达标（低于阈值 ' + str(args.threshold) + '）'}**",
        "",
        f"- 变异体总数：{total}",
        f"- 已杀死(killed+timeout)：{killed}",
        f"- 存活(survived)：{counts.get('survived', 0)}",
        f"- 等价变异(equivalent，不计入分母)：{equivalent}",
        f"- 无覆盖变异(no_coverage，不计入分母)：{no_coverage}",
        f"- 有效分母：{denom}",
        f"- **变异分数：{score:.4f}**  （达标线 {args.threshold}）",
        "",
        "## 状态分布",
        "",
        "| 状态 | 数量 |",
        "| --- | --- |",
    ]
    for st in ("killed", "survived", "timeout", "equivalent"):
        if counts.get(st):
            lines.append(f"| {st} | {counts[st]} |")
    lines.append("")

    # 列出存活变异体（重点整改对象）
    survivors = [m for m in mutants if normalize_status(m) == "survived"]
    if survivors:
        lines += ["## 存活变异体（测试未察觉，优先补断言）", ""]
        lines += ["| ID | 文件 | 行 | 算子 |", "| --- | --- | --- | --- |"]
        for m in survivors:
            lines.append(f"| {m.get('id','')} | {m.get('file','')} | {m.get('line','')} | {m.get('operator','')} |")
        lines.append("")

    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    if signals and args.signals_dir:
        # P1-3 加固：--signals-dir 未提供时不强制写信号（避免 signals_dir=None 时 makedirs 崩溃）；
        # 真实管线（qa-orchestrator / 发布门禁）始终显式传 --signals-dir。
        emit_signal("qa-mutation", signals, args.signals_dir)

    print(f"[RESULT] score={score:.4f} threshold={args.threshold} passed={passed} "
          f"killed={killed} survived={counts.get('survived',0)} equivalent={equivalent} "
          f"no_coverage={no_coverage} denom={denom}")
    if args.fail_on and not passed:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
