#!/usr/bin/env python3
"""Generate a standardized bug report (Markdown) + tracker payload JSON.

Usage:
    python scripts/gen_bug.py --bug bug.json --out bug_report.md --tracker tapd
"""
import argparse
import json
import sys

SEV_CN = {"S1": "致命", "S2": "严重", "S3": "一般", "S4": "轻微"}
PRI_CN = {"P0": "立即修复", "P1": "本迭代", "P2": "排期", "P3": "backlog"}


def render_md(b: dict) -> str:
    lines = []
    lines.append(f"# 缺陷报告：{b.get('title', '未命名缺陷')}\n")
    lines.append("## 基本信息\n")
    lines.append(f"- 模块：{b.get('module', '-')}")
    lines.append(f"- 类型：{b.get('type', '-')}")
    sev = b.get("severity", "-")
    lines.append(f"- 严重级：{sev}（{SEV_CN.get(sev, '')}）")
    pri = b.get("priority", "-")
    lines.append(f"- 优先级：{pri}（{PRI_CN.get(pri, '')}）")
    lines.append(f"- 环境：{b.get('env', '-')}")
    lines.append(f"- 版本：{b.get('version', '-')}")
    lines.append(f"- 报告人：{b.get('reporter', '-')} ｜ 指派给：{b.get('assignee', '-')}")
    lines.append("")
    lines.append("## 复现步骤\n")
    for i, s in enumerate(b.get("steps", []), 1):
        lines.append(f"{i}. {s}")
    if not b.get("steps"):
        lines.append("（未提供）")
    lines.append("")
    lines.append("## 期望结果\n")
    lines.append(b.get("expected", "-"))
    lines.append("")
    lines.append("## 实际结果\n")
    lines.append(b.get("actual", "-"))
    lines.append("")
    if b.get("impact"):
        lines.append("## 业务影响\n")
        lines.append(b["impact"])
        lines.append("")
    ev = b.get("evidence")
    if ev:
        evs = ev if isinstance(ev, list) else [ev]
        lines.append("## 证据\n")
        for e in evs:
            lines.append(f"- {e}")
        lines.append("")
    return "\n".join(lines)


def to_payload(b: dict, tracker: str) -> dict:
    title = b.get("title", "")
    desc = "【复现步骤】\n" + "\n".join(f"{i}. {s}" for i, s in enumerate(b.get("steps", []), 1))
    desc += "\n\n【期望】" + b.get("expected", "")
    desc += "\n【实际】" + b.get("actual", "")
    if b.get("evidence"):
        evs = b.get("evidence") if isinstance(b.get("evidence"), list) else [b.get("evidence")]
        desc += "\n【证据】" + "; ".join(evs)

    if tracker == "tapd":
        return {
            "title": title,
            "module": b.get("module", ""),
            "severity": {"S1": "1", "S2": "2", "S3": "3", "S4": "4"}.get(b.get("severity"), "3"),
            "priority": b.get("priority", ""),
            "description": desc,
            "assigned": b.get("assignee", ""),
            "env": b.get("env", ""),
        }
    if tracker == "zentao":
        # 禅道 severity 数字越大越轻，反转
        sev_map = {"S1": "1", "S2": "2", "S3": "3", "S4": "4"}
        pri_map = {"P0": "1", "P1": "2", "P2": "3", "P3": "4"}
        return {
            "title": title,
            "module": b.get("module", ""),
            "severity": sev_map.get(b.get("severity"), "3"),
            "pri": pri_map.get(b.get("priority"), "3"),
            "steps": desc,
            "type": "bug",
            "assignedTo": b.get("assignee", ""),
        }
    if tracker == "jira":
        return {
            "fields": {
                "project": {"key": b.get("project_key", "PROJ")},
                "summary": title,
                "issuetype": {"name": "Bug"},
                "priority": {"name": b.get("priority", "P2")},
                "description": desc,
                "assignee": {"accountId": b.get("assignee_account", "")},
            }
        }
    return {"title": title, "description": desc}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bug", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tracker", default="tapd", choices=["tapd", "zentao", "jira"])
    ap.add_argument("--payload-out", default=None)
    args = ap.parse_args()
    try:
        with open(args.bug, "r", encoding="utf-8") as f:
            b = json.load(f)
    except Exception as e:
        print(f"[ERROR] 读取 bug 失败: {e}", file=sys.stderr)
        return 2

    md = render_md(b)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(md)

    payload = to_payload(b, args.tracker)
    pout = args.payload_out or (args.out.rsplit(".", 1)[0] + f"_{args.tracker}.json")
    with open(pout, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"[OK] 缺陷报告: {args.out} ｜ {args.tracker} 载荷: {pout}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
