#!/usr/bin/env python3
"""qa-api-runner: Agent 暴露接口 → 传统 QA 回归信号桥接（G-03）。

当被测 Agent 暴露了 HTTP 接口（即它同时是一个「有确定接口的业务系统」），本桥接把
该接口的回归结果转译为 `qa-api-runner` 风格的回归信号文档（signals/qa-api-runner-bridge.json），
使其能被 `qa-release-check` 门禁直接聚合——与接口/UI/性能/安全信号走同一阻断协议，
不再让「Agent 接口回归」游离在传统 QA 门禁之外。

桥接语义（与 ADR-002 / signal-schema 一致）：
  - regression_detected=True  → signal `agent_api_regression`，blocking=True（high）——禁止发布；
  - regression_detected=False → 非阻断信息信号（仍留痕，便于趋势追踪）。

用法:
    python bridge_agent_regression.py --spec agent_iface.json --regression true \
        --out signals/qa-api-runner-bridge.json
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone

SOURCE = "qa-api-runner-bridge"


def build_signal(spec, regression_detected, source=SOURCE):
    endpoints = []
    if isinstance(spec, dict):
        endpoints = spec.get("endpoints") or spec.get("paths") or []
    if isinstance(endpoints, dict):
        endpoints = list(endpoints.keys())
    blocking = bool(regression_detected)
    sig = {
        "signal": "agent_api_regression",
        "severity": "high" if blocking else "info",
        "count": 1,
        "blocking": blocking,
        "detail": ("Agent 暴露接口回归检出（%d 个端点）" % len(endpoints))
                  if blocking else ("Agent 暴露接口回归通过（%d 个端点）" % len(endpoints)),
        "endpoints": endpoints,
    }
    doc = {
        "source": source,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "signals": [sig],
    }
    return doc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True, help="Agent 暴露接口规格 JSON（含 endpoints/paths）")
    ap.add_argument("--regression", required=True, choices=["true", "false"],
                    help="是否检出回归（true→blocking）")
    ap.add_argument("--out", required=True, help="信号文档输出路径（signals/*.json）")
    ap.add_argument("--source", default=SOURCE, help="信号 source 名（默认 qa-api-runner-bridge）")
    args = ap.parse_args()

    try:
        with open(args.spec, "r", encoding="utf-8") as f:
            spec = json.load(f)
    except Exception as e:
        print(f"[ERROR] 读取 {args.spec} 失败: {e}", file=sys.stderr)
        return 2

    regression = args.regression == "true"
    doc = build_signal(spec, regression, source=args.source)
    out_dir = os.path.dirname(args.out)
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    flag = "🚫 阻断" if doc["signals"][0]["blocking"] else "· 信息"
    print(f"[OK] 已生成桥接信号: {args.out} （{flag}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
