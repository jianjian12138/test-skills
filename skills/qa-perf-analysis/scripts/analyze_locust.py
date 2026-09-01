#!/usr/bin/env python3
"""Analyze Locust CSV output into a verdict markdown report.

Usage:
    python scripts/analyze_locust.py --stats results_stats.csv \
        --history results_history.csv --sla sla.json --out analysis.md

Robust to column-name variations across Locust versions.

修复 V6 评审发现的「缺 Aggregated 行时 p95=0 假绿」：当 stats CSV 缺少聚合行时，
p95/p99 置为 None，SLA 含 p95 判定则**判不达标（阻断）**，绝不以 p95=0 通过。
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
def _col(headers, *candidates):
    """Return index of first header matching any candidate (case-insensitive, substring)."""
    low = [h.lower() for h in headers]
    for cand in candidates:
        c = cand.lower()
        for i, h in enumerate(low):
            if c == h or c in h:
                return i
    return None


def _num(v):
    try:
        return float(str(v).replace(",", ""))
    except Exception:
        return 0.0


def parse_stats(path):
    """Return dict: aggregated totals + per-endpoint list.

    若 CSV 缺少 Aggregated/Total 聚合行，返回 agg 的 p95/p99 为 None（derived=True），
    由 verdict 据 SLA 要求判不达标，避免 p95=0 假绿。
    """
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
    if not rows:
        return None
    headers = rows[0]
    i_name = _col(headers, "name")
    i_req = _col(headers, "request count")
    i_fail = _col(headers, "failure count")
    i_avg = _col(headers, "average response time")
    i_med = _col(headers, "median response time")
    i_p95 = _col(headers, "95%")
    i_p99 = _col(headers, "99%")
    i_rps = _col(headers, "requests/s", "rps")
    i_err = _col(headers, "failures/s")

    endpoints = []
    agg = None
    for r in rows[1:]:
        if len(r) <= max(filter(None, [i_name, i_req, i_fail])):
            continue
        name = r[i_name] if i_name is not None else ""
        rec = {
            "name": name,
            "requests": _num(r[i_req]) if i_req is not None else 0,
            "failures": _num(r[i_fail]) if i_fail is not None else 0,
            "avg": _num(r[i_avg]) if i_avg is not None else 0,
            "median": _num(r[i_med]) if i_med is not None else 0,
            "p95": _num(r[i_p95]) if i_p95 is not None else 0,
            "p99": _num(r[i_p99]) if i_p99 is not None else 0,
            "rps": _num(r[i_rps]) if i_rps is not None else 0,
            "err_rate": (_num(r[i_fail]) / _num(r[i_req])) if (i_fail and i_req and _num(r[i_req]) > 0) else 0,
        }
        if name.strip().lower() in ("aggregated", "total", ""):
            agg = rec
        else:
            endpoints.append(rec)
    if agg is None:
        # 缺聚合行：无法获得全局 P95，置 None 交由 verdict 判定
        agg = {
            "name": "Aggregated(derived=missing)",
            "requests": sum(e["requests"] for e in endpoints),
            "failures": sum(e["failures"] for e in endpoints),
            "avg": None, "median": None, "p95": None, "p99": None,
            "rps": sum(e["rps"] for e in endpoints),
            "err_rate": 0,
            "derived": True,
        }
        tot = agg["requests"] or 1
        agg["err_rate"] = agg["failures"] / tot
    return {"agg": agg, "endpoints": endpoints}


def parse_history(path):
    """Return peak RPS, peak avg rt, and trend (first-half vs second-half avg rt)."""
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
    if not rows:
        return None
    headers = rows[0]
    i_rps = _col(headers, "total(rps)")
    i_rt = _col(headers, "total(avg", "total(average response time)")
    i_users = _col(headers, "user count")
    rps_vals, rt_vals, users = [], [], []
    for r in rows[1:]:
        if i_rps is not None and len(r) > i_rps:
            rps_vals.append(_num(r[i_rps]))
        if i_rt is not None and len(r) > i_rt:
            rt_vals.append(_num(r[i_rt]))
        if i_users is not None and len(r) > i_users:
            users.append(_num(r[i_users]))
    if not rt_vals:
        return None
    half = max(1, len(rt_vals) // 2)
    first = sum(rt_vals[:half]) / len(rt_vals[:half])
    second = sum(rt_vals[half:]) / len(rt_vals[half:])
    knee_idx = 0
    if rps_vals:
        knee_idx = max(range(len(rps_vals)), key=lambda i: rps_vals[i])
    knee_rps = rps_vals[knee_idx] if rps_vals else 0
    knee_users = users[knee_idx] if knee_idx < len(users) else 0
    declined = False
    if rps_vals and len(rps_vals) > knee_idx + 1:
        tail = rps_vals[knee_idx + 1:]
        declined = max(tail) < knee_rps * 0.9
    return {
        "peak_rps": max(rps_vals) if rps_vals else 0,
        "peak_rt": max(rt_vals),
        "first_half_rt": first,
        "second_half_rt": second,
        "rt_growth": (second - first) / first if first > 0 else 0,
        "max_users": max(users) if users else 0,
        "knee_rps": knee_rps,
        "knee_users": knee_users,
        "knee_declined": declined,
    }


def diagnose(agg, hist, endpoints):
    notes = []
    if agg and agg.get("err_rate", 0) > 0.01:
        notes.append("错误率 >1%，疑似服务端过载 / 依赖限流 / 连接池耗尽。")
    if agg and agg.get("rps", 0) > 0 and (agg.get("p95") or 0) > 1000:
        notes.append("P95 延迟偏高（>1s）但需结合 RPS 判断是否单请求过重（慢 SQL / 外部调用）。")
    if hist:
        if hist["rt_growth"] > 0.2:
            notes.append(f"响应时间随时间增长 {hist['rt_growth']*100:.0f}%，疑似内存泄漏 / 缓存失效 / 连接堆积。")
        if hist["peak_rps"] > 0 and agg and agg.get("rps", 0) < hist["peak_rps"] * 0.9:
            notes.append("RPS 出现回落，可能已越过系统拐点（饱和）。")
    if agg and (agg.get("p95") or 0) > 0 and (agg.get("p99") or 0) > (agg.get("p95") or 0) * 2:
        notes.append("P99 远大于 P95，存在明显长尾（GC / 锁竞争 / 慢依赖）。")
    if not notes:
        notes.append("未触发明显瓶颈 heuristics，性能表现平稳。")
    return notes


def verdict(agg, sla):
    if not sla or not agg:
        return True, "未提供 SLA，跳过判定。"
    msgs = []
    p95 = agg.get("p95")
    err = agg.get("err_rate", 0)
    tps = agg.get("rps", 0)
    ok = True
    if "p95_ms" in sla:
        if p95 is None:
            ok = False
            msgs.append("P95：无法获取聚合 P95（stats 缺 Aggregated 行）→ 判定不达标（阻断）")
        else:
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


def render(stats, hist, sla):
    agg = stats["agg"]
    lines = []
    lines.append("# 性能测试结果分析\n")
    lines.append("## 总览\n")
    if agg:
        lines.append(f"- 总请求数：{agg['requests']:.0f}")
        lines.append(f"- 失败数：{agg['failures']:.0f}（错误率 {agg['err_rate']*100:.2f}%）")
        lines.append(f"- 平均吞吐 RPS：{agg['rps']:.1f}")
        lines.append(f"- 平均响应时间：{(agg['avg'] or 0):.1f} ms")
        p95s = f"{agg['p95']:.1f}" if agg.get("p95") is not None else "N/A(缺Aggregated行)"
        p99s = f"{agg['p99']:.1f}" if agg.get("p99") is not None else "N/A"
        lines.append(f"- P95：{p95s} ms ｜ P99：{p99s} ms")
        if agg.get("derived"):
            lines.append("- ⚠️ 注意：stats CSV 缺少 Aggregated 聚合行，P95/P99 无法计算，SLA 含 P95 判定将判不达标。")
    if hist:
        lines.append(f"- 峰值 RPS：{hist['peak_rps']:.1f}")
        lines.append(f"- 峰值平均响应时间：{hist['peak_rt']:.1f} ms")
        lines.append(f"- 最大并发用户：{hist['max_users']:.0f}")
        lines.append(f"- 拐点(Knee)：RPS 峰值出现在约 {hist['knee_users']:.0f} 并发处 "
                     f"（RPS={hist['knee_rps']:.1f}）"
                     + ("，其后吞吐回落，已越过系统饱和点。" if hist.get("knee_declined") else "。"))
    lines.append("")

    lines.append("## 逐接口\n")
    lines.append("| 接口 | 请求数 | 失败数 | 错误率 | 平均(ms) | P95(ms) | P99(ms) | RPS |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for e in stats["endpoints"]:
        lines.append(f"| {e['name']} | {e['requests']:.0f} | {e['failures']:.0f} | "
                     f"{e['err_rate']*100:.2f}% | {e['avg']:.1f} | {e['p95']:.1f} | {e['p99']:.1f} | {e['rps']:.1f} |")
    lines.append("")

    lines.append("## 瓶颈诊断\n")
    for n in diagnose(agg, hist, stats["endpoints"]):
        lines.append(f"- {n}")
    lines.append("")

    lines.append("## SLA 判定\n")
    _, verdict_text = verdict(agg, sla)
    lines.append(verdict_text)
    lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats", required=True)
    ap.add_argument("--history")
    ap.add_argument("--sla")
    ap.add_argument("--out", required=True)
    ap.add_argument("--signals-dir", default="signals", help="质量信号输出目录（默认 ./signals）")
    args = ap.parse_args()

    stats = parse_stats(args.stats)
    if stats is None:
        print(f"[ERROR] 无法解析 stats: {args.stats}", file=sys.stderr)
        return 2
    hist = None
    if args.history:
        try:
            hist = parse_history(args.history)
        except Exception as e:
            print(f"[WARN] 解析 history 失败: {e}", file=sys.stderr)
    sla = None
    if args.sla:
        try:
            with open(args.sla, "r", encoding="utf-8") as f:
                sla = json.load(f)
        except Exception as e:
            print(f"[WARN] 读取 SLA 失败: {e}", file=sys.stderr)

    md = render(stats, hist, sla)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(md)
    # 质量信号契约：SLA 不达标（含缺 Aggregated 行导致 P95 缺失）→ blocking 信号
    ok, _ = verdict(stats["agg"], sla)
    print(f"[OK] 已生成分析: {args.out}")
    if sla and not ok:
        emit_signal("qa-perf-analysis", [{
            "signal": "perf_sla_violation", "severity": "high", "count": 1,
            "blocking": True, "detail_ref": args.out,
        }], args.signals_dir)
        print(f"[GATE] SLA 不达标 → 阻断（blocking 信号已写）")
        return 1
    print(f"[GATE] SLA 达标（或无 SLA 跳过判定），未发阻断信号")
    return 0


if __name__ == "__main__":
    sys.exit(main())
