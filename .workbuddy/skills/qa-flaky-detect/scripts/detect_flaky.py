#!/usr/bin/env python3
"""不稳定测试（flaky）检测：多轮重跑结果中识别时过时不过的用例。

零外部依赖（仅标准库）。契合 skills 系统的 signals 契约：
flaky 率超阈值时写 signals/qa-flaky-detect.json 的 flaky_detected（blocking=true）。
"""
import argparse
from datetime import datetime
import json
import math
import os
import sys
from collections import defaultdict


def wilson_ci(k, n, z=1.96):
    """Wilson 置信区间下界（R-09：小样本下避免 flaky 率被稀释误判可控）。"""
    if n <= 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2.0 * n)) / denom
    spread = z * math.sqrt(p * (1 - p) / n + z * z / (4.0 * n * n)) / denom
    return (max(0.0, center - spread), min(1.0, center + spread))


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


def collect(data):
    """归一为多轮重跑：返回 {test: [pass_bool, ...]}。"""
    per_test = defaultdict(list)
    if isinstance(data, dict):
        if "runs" in data and isinstance(data["runs"], list):
            for run in data["runs"]:
                res = run.get("results", {})
                for name, ok in res.items():
                    per_test[name].append(bool(ok))
            return per_test
        if "results" in data and isinstance(data["results"], list):
            for r in data["results"]:
                name = r.get("test") or r.get("name")
                ok = r.get("passed", r.get("pass", r.get("status") == "pass"))
                if name is not None:
                    per_test[name].append(bool(ok))
            return per_test
    # 退化：单轮结果
    if isinstance(data, dict):
        for name, ok in data.items():
            per_test[name].append(bool(ok))
    return per_test


def main():
    ap = argparse.ArgumentParser(description="不稳定测试（flaky）检测")
    ap.add_argument("--runs", required=True, help="多轮重跑结果 JSON")
    ap.add_argument("--out", default="flaky_report.md", help="报告输出路径")
    ap.add_argument("--signals-dir", default="signals", help="信号输出目录（接门禁）；缺省即写 signals/ 确保任何调用都落信号")
    ap.add_argument("--threshold", type=float, default=0.05, help="flaky 率达标线，超过则阻断")
    ap.add_argument("--min-runs", type=int, default=5, help="判定 flaky 所需最少轮数（R-09：默认 5，低于则视为样本不足）")
    ap.add_argument("--fail-on", action="store_true", help="超阈值时 sys.exit(1)")
    args = ap.parse_args()

    data = load_json(args.runs)
    per_test = collect(data)
    total = len(per_test)

    flaky, stable_fail, stable_pass = [], [], []
    sample_short = []
    for name, outcomes in per_test.items():
        n = len(outcomes)
        fails = sum(1 for o in outcomes if not o)
        if n < args.min_runs:
            sample_short.append(name)
            continue
        if fails == 0:
            stable_pass.append(name)
        elif fails == n:
            stable_fail.append(name)  # 稳定失败，需修 bug
        else:
            flaky.append((name, n, fails))

    # R-09 修复：分母改为「可判定用例数」（剔除样本不足者），避免 flaky 被稀释到阈值下。
    judgeable = total - len(sample_short)
    flaky_rate = (len(flaky) / judgeable) if judgeable else 0.0
    flaky_rate_lo = wilson_ci(len(flaky), judgeable)[0] if judgeable else 0.0
    # 判定以 Wilson 下界为准：小样本下若下界仍超阈值，必阻断；避免「宣称可控」误判。
    blocking = (flaky_rate > args.threshold) or (flaky_rate_lo > args.threshold)

    lines = [
        "# 不稳定测试（flaky）检测报告",
        "",
        f"**结论：{'⛔ 发现 flaky（率 ' + f'{flaky_rate:.2%} 超阈值 {args.threshold:.0%}）' if blocking else '✅ flaky 率可控' if flaky_rate else '✅ 无 flaky'}**",
        "",
        f"- 用例总数：{total}",
        f"- 可判定用例数（剔除样本不足）：{judgeable}",
        f"- flaky 用例数：{len(flaky)}（flaky 率 {flaky_rate:.2%}，Wilson 95% 下界 {flaky_rate_lo:.2%}）",
        f"- 稳定失败（需修 bug）：{len(stable_fail)}",
        f"- 稳定通过：{len(stable_pass)}",
    ]
    if sample_short:
        lines.append(f"- ⚠️ 样本不足（<{args.min_runs} 轮）未判定：{len(sample_short)} 个：{', '.join(sample_short)}")
    lines.append("")

    if flaky:
        lines += ["## flaky 用例（时过时不过，建议隔离 + 定位根因）", "",
                  "| 用例 | 轮数 | 失败轮 |", "| --- | --- | --- |"]
        for name, n, fails in sorted(flaky, key=lambda x: -x[2] / x[1]):
            lines.append(f"| {name} | {n} | {fails} |")
        lines.append("")
        lines.append("**重跑建议**：对 flaky 用例单独隔离并重跑 ≥5 轮以定位根因（并发时序、"
                     "异步等待、测试间状态耦合、环境差异等）。")
        lines.append("")

    if stable_fail:
        lines += ["## 稳定失败（100% 失败，非 flaky，应修代码/断言）", "",
                  "| 用例 |", "| --- |"]
        for name in stable_fail:
            lines.append(f"| {name} |")
        lines.append("")

    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    if flaky:
        emit_signal(
            "qa-flaky-detect",
            [{
                "signal": "flaky_detected",
                "severity": "high" if blocking else "warn",
                "count": len(flaky),
                "blocking": blocking,
                "detail_ref": os.path.basename(args.out),
                "flaky_rate": round(flaky_rate, 4),
                "threshold": args.threshold,
            }],
            args.signals_dir,
        )

    print(f"[RESULT] flaky_rate={flaky_rate:.2%} threshold={args.threshold} "
          f"flaky={len(flaky)} stable_fail={len(stable_fail)} blocking={blocking}")
    if args.fail_on and blocking:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
