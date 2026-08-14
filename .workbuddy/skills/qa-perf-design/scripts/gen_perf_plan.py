#!/usr/bin/env python3
"""Gen perf plan markdown from a scenario JSON.

Usage:
    python scripts/gen_perf_plan.py --scenarios scenarios.json --out plan.md

Input schema matches references/scenario-template.md.
"""
import argparse
import json
import sys


TYPE_DESC = {
    "load": "负载（验证日常/峰值容量下达标）",
    "stress": "压力（逐步加压找拐点/极限）",
    "endurance": "疲劳（长时间运行找泄漏/退化）",
    "spike": "尖峰（突发流量韧性）",
}


def _fmt(v, default="-"):
    return default if v is None else str(v)


def render(data: dict) -> str:
    target = data.get("target", "未命名目标")
    base_url = data.get("base_url", "-")
    scenarios = data.get("scenarios", [])
    lines = []
    lines.append(f"# 性能测试方案：{target}\n")
    lines.append(f"- 被测基准地址：`{base_url}`")
    lines.append(f"- 场景数量：{len(scenarios)}\n")

    lines.append("## 场景矩阵\n")
    lines.append("| 场景 | 类型 | 并发 | 爬坡/s | 时长(s) | 思考时间(s) | 目标TPS | SLA-P95(ms) | SLA-错误率 |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for s in scenarios:
        t = s.get("type", "-")
        lines.append(
            "| {name} | {type} | {users} | {spawn} | {dur} | {think} | {tps} | {p95} | {err} |".format(
                name=s.get("name", "-"),
                type=t,
                users=_fmt(s.get("users")),
                spawn=_fmt(s.get("spawn_rate")),
                dur=_fmt(s.get("duration")),
                think=_fmt(s.get("think_time")),
                tps=_fmt(s.get("target_tps")),
                p95=_fmt(s.get("sla_p95_ms")),
                err=_fmt(s.get("sla_error_rate")),
            )
        )
    lines.append("")

    lines.append("## 场景说明与判定口径\n")
    for s in scenarios:
        t = s.get("type", "-")
        lines.append(f"### {s.get('name', '-')}（{TYPE_DESC.get(t, t)}）")
        lines.append(f"- 并发用户：{_fmt(s.get('users'))}")
        lines.append(f"- 爬坡速度：{_fmt(s.get('spawn_rate'))} 用户/秒")
        lines.append(f"- 持续时长：{_fmt(s.get('duration'))} 秒")
        lines.append(f"- 思考时间：{_fmt(s.get('think_time'))} 秒")
        lines.append(f"- 目标 TPS：{_fmt(s.get('target_tps'))}")
        lines.append(f"- SLA：P95 ≤ {_fmt(s.get('sla_p95_ms'))} ms，错误率 ≤ {_fmt(s.get('sla_error_rate'))}")
        verdict = _verdict_hint(s)
        lines.append(f"- 判定：{verdict}\n")

    # 并发估算速算
    lines.append("## 并发估算速算（起点参考）\n")
    for s in scenarios:
        users = s.get("users")
        think = s.get("think_time")
        if users is not None and think is not None:
            # 单个用户在 think_time 内约完成 1 次事务，吞吐≈users/(think+resp)
            # 这里给出并发下界提示
            tps_lower = users / (float(think) + 0.5)
            lines.append(f"- `{s.get('name')}`：{users} 并发 ≈ 至少 {tps_lower:.0f} TPS（按 P95≈0.5s 估算下界）")
    lines.append("")
    return "\n".join(lines)


def _verdict_hint(s: dict) -> str:
    t = s.get("type")
    if t == "load":
        return "实际 TPS ≥ 目标 且 P95/SLA 达标 → 通过"
    if t == "stress":
        return "记录拐点（TPS 下降/错误率突增的并发点）作为容量上限"
    if t == "endurance":
        return "时长内无退化、资源无持续上涨 → 通过"
    if t == "spike":
        return "峰值后回落至基线、错误率回落 → 韧性达标"
    return "按场景类型判定"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenarios", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    try:
        with open(args.scenarios, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[ERROR] 读取场景文件失败: {e}", file=sys.stderr)
        return 2

    md = render(data)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"[OK] 已生成方案: {args.out}（{len(data.get('scenarios', []))} 个场景）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
