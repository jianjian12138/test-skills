#!/usr/bin/env python3
"""Analyze JMeter result CSV (from `jmeter -l result.csv`) into a verdict markdown.

Usage:
    python scripts/analyze_jmeter.py --csv result.csv --sla sla.json --out analysis.md

Mirrors qa-perf-analysis output structure (per-endpoint + aggregate + bottleneck +
SLA) so Locust and JMeter results are comparable.

Robust to column-name variations; computes percentiles from `elapsed`,
throughput from `timeStamp` span when available.
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
def _col(headers, *cands):
    low = [h.lower() for h in headers]
    for c in cands:
        c = c.lower()
        for i, h in enumerate(low):
            if c == h or c in h:
                return i
    return None


def _num(v):
    try:
        return float(str(v).replace(",", ""))
    except Exception:
        return 0.0


def pct(sorted_vals, p):
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    k = (len(sorted_vals) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def parse(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        return None
    headers = rows[0]
    i_label = _col(headers, "label")
    i_elapsed = _col(headers, "elapsed")
    i_success = _col(headers, "success")
    i_ts = _col(headers, "timestamp", "timeStamp")
    if i_elapsed is None or i_label is None:
        return None

    by_label = {}
    total = []
    ts_list = []
    fail = 0
    for r in rows[1:]:
        if len(r) <= max(i_elapsed, i_label):
            continue
        label = r[i_label]
        el = _num(r[i_elapsed])
        ok = True
        if i_success is not None and len(r) > i_success:
            ok = str(r[i_success]).strip().lower() in ("true", "1", "y", "yes")
        by_label.setdefault(label, []).append((el, ok))
        total.append((el, ok))
        if not ok:
            fail += 1
        if i_ts is not None and len(r) > i_ts:
            ts_list.append(_num(r[i_ts]))

    def agg(vals, name):
        if not vals:
            return None
        els = sorted(v for v, _ in vals)
        n = len(els)
        fails = sum(1 for _, o in vals if not o)
        return {
            "name": name,
            "requests": n,
            "failures": fails,
            "err_rate": fails / n,
            "avg": sum(els) / n,
            "p50": pct(els, 50),
            "p90": pct(els, 90),
            "p95": pct(els, 95),
            "p99": pct(els, 99),
        }

    endpoints = [agg(v, label) for label, v in by_label.items()]
    agg_all = agg(total, "Aggregated")
    if agg_all:
        agg_all["name"] = "Aggregated"
    # throughput
    tps = 0.0
    if len(ts_list) >= 2:
        span = (max(ts_list) - min(ts_list)) / 1000.0
        tps = len(ts_list) / span if span > 0 else 0
        agg_all["rps"] = tps
    else:
        agg_all["rps"] = 0
    return {"agg": agg_all, "endpoints": endpoints, "tps": tps}


def diagnose(agg, endpoints):
    notes = []
    if agg and agg.get("err_rate", 0) > 0.01:
        notes.append("错误率 >1%，疑似服务端过载 / 依赖限流 / 连接池耗尽。")
    if agg and agg.get("rps", 0) > 0 and agg.get("p95", 0) > 1000:
        notes.append("P95 延迟偏高（>1s）且吞吐受限，疑似单请求过重（慢 SQL / 外部调用）。")
    if agg and agg.get("p95", 0) > 0 and agg.get("p99", 0) > agg["p95"] * 2:
        notes.append("P99 远大于 P95，存在明显长尾（GC / 锁竞争 / 慢依赖）。")
    # per-endpoint hotspots
    worst = sorted(endpoints, key=lambda e: e["p95"] if e else 0, reverse=True)[:3]
    for e in worst:
        if e and e["p95"] > 1000:
            notes.append(f"接口 {e['name']} P95={e['p95']:.0f}ms 偏高，优先排查。")
    if not notes:
        notes.append("未触发明显瓶颈 heuristics，性能表现平稳。")
    return notes


def verdict(agg, sla):
    if not sla or not agg:
        return True, "未提供 SLA，跳过判定。"
    msgs = []
    ok = True
    p95 = agg.get("p95", 0)
    err = agg.get("err_rate", 0)
    tps = agg.get("rps", 0)
    if "p95_ms" in sla:
        passed = p95 <= sla["p95_ms"]
        ok = ok and passed
        msgs.append(f"P95 {p95:.0f}ms ≤ {sla['p95_ms']}ms: {'通过' if passed else '不通过'}")
    if "error_rate" in sla:
        passed = err <= sla["error_rate"]
        ok = ok and passed
        msgs.append(f"错误率 {err*100:.2f}% ≤ {sla['error_rate']*100:.2f}%: {'通过' if passed else '不通过'}")
    if "min_tps" in sla:
        passed = tps >= sla["min_tps"]
        ok = ok and passed
        msgs.append(f"TPS {tps:.0f} ≥ {sla['min_tps']}: {'通过' if passed else '不通过'}")
    return ok, ("整体 SLA：" + ("✅ 达标" if ok else "❌ 不达标") + "\n- " + "\n- ".join(msgs))


def render(stats, sla):
    agg = stats["agg"]
    lines = ["# JMeter 性能测试结果分析\n", "## 总览\n"]
    if agg:
        lines.append(f"- 总请求数：{agg['requests']:.0f}")
        lines.append(f"- 失败数：{agg['failures']:.0f}（错误率 {agg['err_rate']*100:.2f}%）")
        lines.append(f"- 平均吞吐 TPS：{agg.get('rps', 0):.1f}")
        lines.append(f"- 平均响应时间：{agg['avg']:.1f} ms")
        lines.append(f"- P95：{agg['p95']:.1f} ms ｜ P99：{agg['p99']:.1f} ms")
    lines.append("")
    lines.append("## 逐接口\n")
    lines.append("| 接口 | 请求数 | 失败数 | 错误率 | 平均(ms) | P95(ms) | P99(ms) |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for e in stats["endpoints"]:
        if not e:
            continue
        lines.append(f"| {e['name']} | {e['requests']:.0f} | {e['failures']:.0f} | "
                     f"{e['err_rate']*100:.2f}% | {e['avg']:.1f} | {e['p95']:.1f} | {e['p99']:.1f} |")
    lines.append("")
    lines.append("## 瓶颈诊断\n")
    for n in diagnose(agg, stats["endpoints"]):
        lines.append(f"- {n}")
    lines.append("")
    lines.append("## SLA 判定\n")
    _, verdict_text = verdict(agg, sla)
    lines.append(verdict_text)
    lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="JMeter result CSV (from -l).")
    ap.add_argument("--sla")
    ap.add_argument("--out", required=True)
    ap.add_argument("--signals-dir", default="signals", help="质量信号输出目录（默认 ./signals）")
    ap.add_argument("--fail-on", dest="fail_on", action="store_true", default=True,
                    help="SLA 不达标时以退出码 1 失败（默认开，对齐 locust 行为，CI 真阻断）")
    ap.add_argument("--no-fail-on", dest="fail_on", action="store_false",
                    help="关闭 SLA 不达标退出码失败（仅产出报告与信号，不阻断 CI）")
    args = ap.parse_args()

    stats = parse(args.csv)
    if stats is None:
        print(f"[ERROR] 无法解析 CSV: {args.csv}", file=sys.stderr)
        return 2
    sla = None
    if args.sla:
        try:
            with open(args.sla, "r", encoding="utf-8") as f:
                sla = json.load(f)
        except Exception as e:
            print(f"[WARN] 读取 SLA 失败: {e}", file=sys.stderr)
    md = render(stats, sla)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(md)
    # 质量信号契约：SLA 不达标 → blocking 信号
    ok, _ = verdict(stats["agg"], sla)
    if sla and not ok:
        emit_signal("qa-perf-jmeter", [{
            "signal": "perf_sla_violation", "severity": "high", "count": 1,
            "blocking": True, "detail_ref": args.out,
        }], args.signals_dir)
    print(f"[OK] 已生成分析: {args.out}")
    # RK-05：SLA 不达标须真实失败（与 locust 一致），否则独立 CI 步骤仅看 rc 会假绿。
    if args.fail_on and sla and not ok:
        print("[GATE] SLA 不达标 → 阻断（blocking 信号已写）", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
