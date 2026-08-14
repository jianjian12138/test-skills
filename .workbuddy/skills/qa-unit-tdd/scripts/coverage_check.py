#!/usr/bin/env python3
"""覆盖率真提升校验（W10 / Cover-Agent 思路：Coverage Parser）。

本包 `qa-unit-tdd` / `qa-mutation` 旧逻辑只「生成测试 / 聚合分数」，无法回答
「覆盖率是否真的提升了」。本模块实现 Coverage Parser 的最小闭环：
- 读「改前 / 改后」覆盖率报告（标量百分比 或 {文件: 百分比} 字典）
- 判断覆盖率是否**真实提升**（delta >= min_delta），而非仅生成了测试

诚实边界：本模块**不运行测试、不调用 pytest-cov**——它消费覆盖率工具（pytest-cov/
coverage.py）已产出的报告，做「真提升」判定。真实覆盖率采集须接 coverage.py。

用法:
    coverage_check.py --before before.json --after after.json [--min-delta 0.0] [--json]
before/after.json: {"overall": 73.2} 或 {"files": {"a.py": 80, "b.py": 60}}
"""
import argparse
import json
import sys


def _to_scalar(cov):
    """覆盖率报告 → 标量百分比。支持 {"overall": x} / {"files": {...}} / 标量。"""
    if isinstance(cov, (int, float)):
        return float(cov)
    if isinstance(cov, dict):
        if "overall" in cov:
            return float(cov["overall"])
        if "files" in cov and isinstance(cov["files"], dict):
            vals = [v for v in cov["files"].values() if isinstance(v, (int, float))]
            return (sum(vals) / len(vals)) if vals else 0.0
        # 直接是 {文件: 百分比}
        vals = [v for v in cov.values() if isinstance(v, (int, float))]
        return (sum(vals) / len(vals)) if vals else 0.0
    raise ValueError("无法解析覆盖率报告: %r" % cov)


def coverage_real_increase(before, after, min_delta=0.0):
    """判定覆盖率是否真实提升。

    返回 (improved: bool, detail: dict)。
    - improved=True  表示 after 相对 before 提升了至少 min_delta（覆盖真提升）。
    - improved=False 表示未提升（生成了测试但覆盖没涨 → 须阻断/告警，不得记绿）。
    """
    b = _to_scalar(before)
    a = _to_scalar(after)
    delta = round(a - b, 4)
    improved = delta >= min_delta
    return improved, {
        "before": round(b, 4), "after": round(a, 4),
        "delta": delta, "min_delta": min_delta, "improved": improved,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", required=True, help="改前覆盖率报告 JSON")
    ap.add_argument("--after", required=True, help="改后覆盖率报告 JSON")
    ap.add_argument("--min-delta", type=float, default=0.0,
                    help="最小提升阈值(百分点)；低于此视为未真实提升（默认 0，即只要涨就算）")
    ap.add_argument("--json", action="store_true", help="JSON 输出")
    args = ap.parse_args()
    before = json.load(open(args.before, encoding="utf-8"))
    after = json.load(open(args.after, encoding="utf-8"))
    improved, detail = coverage_real_increase(before, after, args.min_delta)
    if args.json:
        print(json.dumps(detail, ensure_ascii=False, indent=2))
    else:
        print("覆盖率真提升校验: %s" % ("✅ 真提升" if improved else "❌ 未真实提升（仅生成测试≠覆盖涨）"))
        print("  before=%s after=%s delta=%s (min_delta=%s)"
              % (detail["before"], detail["after"], detail["delta"], detail["min_delta"]))
    # 未真实提升 → exit 1（fail-closed：不得把"生成测试"记成"覆盖提升"）
    return 0 if improved else 1


if __name__ == "__main__":
    sys.exit(main())
