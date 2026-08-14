#!/usr/bin/env python3
"""Capacity planning helper: derive target concurrency / TPS and knee hint.

Usage:
    python scripts/calc_capacity.py --peak-qps 1000 --avg-rt 0.5 --headroom 1.5 --out cap.md

Formulas:
    目标并发 ≈ 峰值QPS × 平均响应时间(秒) × 余量
    所需吞吐(TPS) = 峰值QPS
    拐点提示：在目标并发之上继续加压找系统饱和点
"""
import argparse
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--peak-qps", type=float, required=True, help="峰值 QPS")
    ap.add_argument("--avg-rt", type=float, required=True, help="平均响应时间(秒)")
    ap.add_argument("--headroom", type=float, default=1.5, help="并发余量系数")
    ap.add_argument("--duration-h", type=float, default=1.0, help="峰值持续小时数(用于总量)")
    ap.add_argument("--out", help="输出 Markdown")
    args = ap.parse_args()

    concurrency = args.peak_qps * args.avg_rt * args.headroom
    tps = args.peak_qps
    total = args.peak_qps * args.duration_h * 3600
    lines = ["# 容量规划估算\n",
             f"- 峰值 QPS：{args.peak_qps:.0f}",
             f"- 平均响应时间：{args.avg_rt:.2f}s",
             f"- 并发余量系数：{args.headroom}",
             f"- **目标并发 ≈ {concurrency:.0f}**（刚好打满吞吐的下界 × 余量）",
             f"- **所需吞吐 TPS ≥ {tps:.0f}**",
             f"- 峰值持续 {args.duration_h}h 总请求量 ≈ {total:,.0f}",
             "",
             "## 拐点 / 饱和识别",
             f"- 在 ~{concurrency:.0f} 并发基础上逐步加压，观察 RPS 是否不再增长即为拐点。",
             "- 拐点后增加并发只增延迟不增吞吐 → 已到系统饱和点。",
             "- 配合资源监控（CPU/内存/连接）定位瓶颈维度。"]
    md = "\n".join(lines) + "\n"
    print(md.strip())
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"[OK] 已写出: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
