#!/usr/bin/env python3
"""Generate a compatibility test matrix (CSV + Markdown) from dimension config.

Usage:
    python scripts/gen_matrix.py --config matrix.json --out matrix.md --csv matrix.csv

Config JSON:
{
  "web": {"os": [...], "browsers": [...]},
  "mobile": {"devices": [...], "os": [...]},
  "must_pairs": ["Chrome|Windows 11", "Safari|iOS 17"],
  "cloud_browsers": ["微信内置", "UC", "360"],
  "resolutions": ["1920x1080", "375x812"],
  "invalid_pairs": ["Safari|Windows 11"]   # 可选：显式排除的 Web 组合
}

修复 P0-D「兼容性矩阵笛卡尔积」：内置浏览器×OS 合法性规则（如 Safari 仅 macOS/iOS），
生成时过滤非法组合并告警，杜绝 Safari@Windows 这类不存在的组合被误判为应测。
Priority: must (in must_pairs or mainstream), should (other mainstream), optional (long tail).
need_cloud: mobile device / cloud_browsers / mobile OS.
"""
import argparse
import csv
import json
import sys


def is_invalid(os_name, browser, extra_invalid=None):
    """返回 (是否非法, 原因)。Safari 仅 macOS/iOS；其余跨平台。"""
    if browser == "Safari" and not any(k in os_name for k in ("macOS", "Mac", "iOS", "mac")):
        return True, "Safari 仅支持 macOS/iOS"
    if extra_invalid:
        key = f"{browser}|{os_name}"
        if key in extra_invalid:
            return True, "配置显式排除(invalid_pairs)"
    return False, ""


def priority_for(os_name, browser, must_pairs):
    key = f"{browser}|{os_name}"
    if key in must_pairs:
        return "must"
    if browser in ("Chrome", "Safari", "Edge") and os_name in ("Windows 11", "Windows 10", "macOS 14", "macOS 13", "iOS 17", "iOS 16"):
        return "should"
    return "optional"


def need_cloud(os_name, browser, device, cloud_browsers):
    if device:
        return True
    if browser in cloud_browsers:
        return True
    if any(k in os_name for k in ("Android", "iOS")):
        return True
    return False


def build_web(cfg, rows, warnings):
    web = cfg.get("web", {})
    oses = web.get("os", [])
    browsers = web.get("browsers", [])
    must = set(cfg.get("must_pairs", []))
    cb = cfg.get("cloud_browsers", [])
    extra_invalid = set(cfg.get("invalid_pairs", []))
    for o in oses:
        for b in browsers:
            bad, reason = is_invalid(o, b, extra_invalid)
            if bad:
                warnings.append(f"{b} @ {o} → 已过滤（{reason}）")
                continue
            rows.append({
                "type": "web",
                "comb": f"{b} @ {o}",
                "os": o,
                "browser": b,
                "device": "",
                "priority": priority_for(o, b, must),
                "need_cloud": need_cloud(o, b, "", cb),
            })


def build_mobile(cfg, rows):
    mob = cfg.get("mobile", [])
    cb = cfg.get("cloud_browsers", [])
    if isinstance(mob, dict):
        mob = [{"device": d, "os": o} for d in mob.get("devices", [])
               for o in mob.get("os", [])]
    for pair in mob:
        d = pair.get("device", "")
        o = pair.get("os", "")
        rows.append({
            "type": "mobile",
            "comb": f"{d} @ {o}",
            "os": o,
            "browser": "",
            "device": d,
            "priority": "must" if (d and o) else "should",
            "need_cloud": need_cloud(o, "", d, cb),
        })


def render_md(rows, cfg, warnings):
    lines = ["# 兼容性测试矩阵（Compatibility Matrix）\n"]
    if warnings:
        lines.append("## ⚠️ 已过滤的非法组合（不参与排期）\n")
        for w in warnings:
            lines.append(f"- {w}")
        lines.append("")
    for title, t in [("Web 矩阵", "web"), ("移动矩阵", "mobile")]:
        sub = [r for r in rows if r["type"] == t]
        if not sub:
            continue
        lines.append(f"## {title}\n")
        lines.append("| 组合 | 优先级 | 需云端 | OS | 浏览器 | 设备 |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for r in sub:
            lines.append(f"| {r['comb']} | {r['priority']} | "
                         f"{'是' if r['need_cloud'] else '否'} | {r['os']} | "
                         f"{r['browser']} | {r['device']} |")
        lines.append("")
    res = cfg.get("resolutions", [])
    if res:
        lines.append("## 分辨率视口\n")
        lines.append("、".join(res) + "\n")
    must_n = sum(1 for r in rows if r["priority"] == "must")
    cloud_n = sum(1 for r in rows if r["need_cloud"])
    lines.append("## 统计\n")
    lines.append(f"- 总组合：{len(rows)}（已过滤 {len(warnings)} 个非法组合）｜ 必测(must)：{must_n} ｜ 需云端：{cloud_n}\n")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True, help="Markdown 输出")
    ap.add_argument("--csv", help="CSV 输出（可选）")
    args = ap.parse_args()

    try:
        with open(args.config, "r", encoding="utf-8-sig") as f:
            cfg = json.load(f)
    except Exception as e:
        print(f"[ERROR] 读取配置失败: {e}", file=sys.stderr)
        return 2

    rows = []
    warnings = []
    build_web(cfg, rows, warnings)
    build_mobile(cfg, rows)
    if not rows:
        print("[ERROR] 配置未产生任何组合（可能全部被合法性规则过滤）", file=sys.stderr)
        if warnings:
            for w in warnings:
                print(f"  - {w}", file=sys.stderr)
        return 2

    md = render_md(rows, cfg, warnings)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"[OK] 已生成矩阵: {args.out} ({len(rows)} 组合, {len(warnings)} 个非法组合已过滤)")
    for w in warnings:
        print(f"  [过滤] {w}")

    if args.csv:
        with open(args.csv, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["type", "comb", "os", "browser", "device",
                                              "priority", "need_cloud"])
            w.writeheader()
            for r in rows:
                w.writerow(r)
        print(f"[OK] 已生成 CSV: {args.csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
