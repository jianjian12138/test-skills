#!/usr/bin/env python3
"""Local executable helper for qa-incident-retro: 复盘报告骨架与改进项门禁校验。"""

from __future__ import annotations

import json
import sys

VAGUE_OWNERS = {"", "待定", "TBD", "todo", "none", "相关团队", "大家"}


def build_retro_report(payload: dict | None = None) -> dict:
    """校验事故复盘四要素，返回 READY/BLOCKED 与结构化骨架。"""
    data = payload or {}
    timeline = data.get("timeline", [])
    causes = data.get("root_causes", {})
    actions = data.get("action_items", [])

    issues: list[str] = []
    if not timeline:
        issues.append("时间线为空，至少需提供告警/发现/止血/恢复四个时刻")

    for key in ("direct", "why_chain", "systemic"):
        if not causes.get(key):
            issues.append(f"根因分析缺少 {key}（直接原因 / 5 Why 链路 / 系统性根因）")

    if not actions:
        issues.append("改进项为空，复盘必须包含至少一条可跟踪改进项")

    normalized_actions = []
    for idx, item in enumerate(actions, 1):
        if not isinstance(item, dict):
            issues.append(f"改进项 #{idx} 不是对象")
            continue
        owner = str(item.get("owner", "")).strip()
        due = str(item.get("due_date", "")).strip()
        acceptance = str(item.get("acceptance", "")).strip()
        if owner.lower() in VAGUE_OWNERS:
            issues.append(f"改进项 #{idx} 缺少明确责任人")
        if len(due) != 10 or due[4:5] != "-" or due[7:8] != "-":
            issues.append(f"改进项 #{idx} 截止日期需为 YYYY-MM-DD")
        if len(acceptance) < 8:
            issues.append(f"改进项 #{idx} 缺少可判定的验收标准")
        normalized_actions.append(
            {
                "index": idx,
                "item": str(item.get("item", "")),
                "owner": owner,
                "due_date": due,
                "acceptance": acceptance,
                "status": item.get("status", "OPEN"),
            }
        )

    return {
        "skill_id": "qa-incident-retro",
        "title": "生产事故时间线复盘与改进项闭环跟踪",
        "stage": "release_ops",
        "tier": "L1",
        "mcp_tool_binding": "route_qa_skills",
        "status": "READY" if not issues else "BLOCKED",
        "timeline_count": len(timeline),
        "action_items": normalized_actions,
        "issues": issues,
    }


if __name__ == "__main__":
    raw = sys.stdin.read() if len(sys.argv) < 2 else sys.argv[1]
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        payload = {"raw": raw}
    print(json.dumps(build_retro_report(payload), ensure_ascii=False, indent=2))
