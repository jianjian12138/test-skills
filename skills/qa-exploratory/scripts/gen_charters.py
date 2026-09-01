#!/usr/bin/env python3
"""Generate exploratory testing charters from features/risk input.

Usage:
    python scripts/gen_charters.py --input features.json --out charters.md
    python scripts/gen_charters.py --features "订单导出,优惠券核销" \
        --risks "大数据量超时;权限越界" --timebox 90 --out charters.md

For each feature, emit one or more charters (mission / area / tours / risks /
stop condition / timebox). Tours are selected deterministically from a built-in
library so output is reproducible.
"""
import argparse
import json
import sys


# Built-in tour library (name -> description). Picked by index for determinism.
TOURS = [
    ("Museum Tour", "逐页/逐接口走查，核对呈现与文案"),
    ("Guide Tour", "走官方推荐主流程（核心路径）"),
    ("Supermodel Tour", "走最复杂/最长的功能链"),
    ("Money Tour", "走关键转化路径（下单/支付）"),
    ("Extreme Tour", "边界值/最大长度/超大数据量"),
    ("Destroy Tour", "非法输入/断网/并发/越权"),
    ("Lazy Tour", "全默认、空提交、跳过校验"),
    ("Antisocial Tour", "多用户抢资源/并发修改"),
    ("Awake Tour", "长时间静置后状态/会话校验"),
]


def load_input(args):
    if args.input:
        try:
            with open(args.input, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
        except Exception as e:
            print(f"[ERROR] 读取输入失败: {e}", file=sys.stderr)
            return None
        features = data.get("features", [])
        timebox = int(data.get("session_timebox_min", args.timebox))
        return features, timebox
    # simple mode
    feats = [s.strip() for s in (args.features or "").split(",") if s.strip()]
    risks = [s.strip() for s in (args.risks or "").split(";") if s.strip()]
    features = [{"name": f, "risks": risks} for f in feats]
    return features, args.timebox


def gen_charter(idx, feat, timebox):
    name = feat.get("name", f"功能{idx}")
    risks = feat.get("risks", []) or []
    # pick tours deterministically: base set + one extra per risk
    picks = [TOURS[0], TOURS[4], TOURS[5]]  # Museum + Extreme + Destroy baseline
    for i, _ in enumerate(risks):
        picks.append(TOURS[(i + 1) % len(TOURS)])
    # dedupe preserve order
    seen, tours = set(), []
    for t in picks:
        if t[0] not in seen:
            seen.add(t[0])
            tours.append(t)
    tour_lines = "\n".join(f"    - {n}：{d}" for n, d in tours)
    risk_lines = "\n".join(f"    - {r}" for r in risks) if risks else "    - （无显性风险，按 Tour 自由探索）"
    stop = f"覆盖 {max(1, len(tours))} 个 Tour 或 时间盒 {timebox}min 到"
    return f"""### C-{idx:02d} {name}

- **目标**：验证「{name}」在典型与异常场景下的行为正确性、稳定性与安全性
- **区域**：{name} 相关页面 / 接口 / 依赖
- **方法（Tour）**：
{tour_lines}
- **风险点**：
{risk_lines}
- **停止条件**：{stop}
- **时间盒**：{timebox} min
"""


def gen_session_sheet(idx, feat, timebox):
    """SBTM 会话工作单：会话中由测试员填写，保证探索性「可复查、可收口」。"""
    name = feat.get("name", f"功能{idx}")
    return f"""#### 会话工作单 C-{idx:02d} · {name}

| 字段 | 内容 |
|---|---|
| 章程 | C-{idx:02d} {name} |
| 测试员 | （填写） |
| 时长 | {timebox} min |
| 覆盖区域 | （填写：页面/接口/依赖） |
| 风险关注 | {', '.join(feat.get('risks', []) or ['—']) } |
| 发现 | （填写：现象/复现步骤/截图） |
| 是否转缺陷 | ☐ 是（见 debrief 自动生成 bug） ☐ 否 |
"""


def gen_debrief(sessions):
    """根据会话结果生成 debrief + 缺陷清单（章程→缺陷接口，直接喂 qa-bug-report）。

    sessions: [{"charter":"C-01 登录","findings":[{"title":"...","severity":"S2","repro":"..."}]}]
    返回 (debrief_md, bugs_json_list)。
    """
    bugs = []
    n = 0
    lines = ["# 探索性测试 Debrief（会话复盘）\n"]
    for s in sessions:
        n += 1
        ch = s.get("charter", f"S-{n}")
        finds = s.get("findings", []) or []
        lines.append(f"## {ch}\n")
        if not finds:
            lines.append("- 无新发现，覆盖符合预期。\n")
            continue
        for f in finds:
            bid = f"EXP-{n}-{len(bugs)+1:02d}"
            bugs.append({
                "id": bid,
                "title": f.get("title", "探索性发现"),
                "severity": f.get("severity", "S3"),
                "status": "open",
                "source": "exploratory",
                "charter": ch,
                "repro": f.get("repro", ""),
            })
            lines.append(f"- [{bid}] **{f.get('severity','S3')}** {f.get('title','')}"
                         + (f" — 复现：{f.get('repro','')}" if f.get('repro') else ""))
        lines.append("")
    lines.append(f"\n**合计：{len(bugs)} 个缺陷已生成（可直送 qa-bug-report）。**")
    return "\n".join(lines), bugs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", help="JSON: {features:[{name,risks}], session_timebox_min}")
    ap.add_argument("--features", help="逗号分隔功能名（简单模式）")
    ap.add_argument("--risks", help="分号分隔风险点（简单模式）")
    ap.add_argument("--timebox", type=int, default=90, help="单轮时间盒（分钟）")
    ap.add_argument("--out", required=False, help="章程输出（debrief 模式可省略，用 --debrief-out）")
    ap.add_argument("--session-sheet", action="store_true",
                    help="在每个章程后追加 SBTM 会话工作单")
    ap.add_argument("--debrief", help="会话结果 JSON（含 findings），生成 debrief")
    ap.add_argument("--debrief-out", help="debrief Markdown 输出")
    ap.add_argument("--bugs-out", help="debrief 产出的缺陷 JSON（喂 qa-bug-report）")
    args = ap.parse_args()

    # debrief 模式（独立于章程生成）
    if args.debrief:
        with open(args.debrief, "r", encoding="utf-8-sig") as f:
            sessions = json.load(f)
        md, bugs = gen_debrief(sessions)
        out = args.debrief_out or args.out
        with open(out, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"[OK] 已生成 debrief: {out}（{len(bugs)} 个缺陷）")
        if args.bugs_out:
            with open(args.bugs_out, "w", encoding="utf-8") as f:
                json.dump(bugs, f, ensure_ascii=False, indent=2)
            print(f"[OK] 已生成缺陷清单: {args.bugs_out}（可送 qa-bug-report）")
        return 0

    loaded = load_input(args)
    if loaded is None:
        return 2
    if not args.out:
        print("[ERROR] 未指定 --out（章程输出路径）", file=sys.stderr)
        return 2
    features, timebox = loaded
    if not features:
        print("[ERROR] 没有功能输入", file=sys.stderr)
        return 2

    lines = ["# 探索性测试章程（Exploratory Charters）\n"]
    lines.append(f"- 时间盒：{timebox} min/轮 ｜ 章程数：{len(features)}\n")
    for i, feat in enumerate(features, 1):
        lines.append(gen_charter(i, feat, timebox))
        if args.session_sheet:
            lines.append(gen_session_sheet(i, feat, timebox))
        lines.append("")
    md = "\n".join(lines)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"[OK] 已生成章程: {args.out} ({len(features)} 个)"
          + (" + 会话工作单" if args.session_sheet else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
