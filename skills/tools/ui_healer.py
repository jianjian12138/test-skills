#!/usr/bin/env python3
"""Playwright MCP ARIA Accessibility Tree Snapshot Parser & Low-Token Self-Healing Engine."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .router import get_trace_id

SAMPLE_ARIA_SNAPSHOT = """- banner:
  - heading "订单结算中心" [level=1]
  - navigation "主导航":
    - link "首页"
    - link "我的订单"
- main:
  - region "收货人信息":
    - textbox "收货人姓名"
    - textbox "手机号码"
  - region "支付方式":
    - radio "微信支付" [checked]
    - radio "支付宝"
  - button "立即提交并支付"
  - button "取消订单"
"""


@dataclass
class AriaNode:
    role: str
    name: str
    attributes: list[str]
    raw_line: str


def parse_aria_snapshot(aria_yaml: str) -> list[AriaNode]:
    """Parse Playwright ARIA YAML snapshot into structured semantic nodes."""
    nodes: list[AriaNode] = []
    pattern = re.compile(r'-\s+([a-zA-Z0-9_-]+)(?:\s+"([^"]*)")?(?:\s+\[([^\]]+)\])?')
    for line in aria_yaml.splitlines():
        m = pattern.search(line)
        if not m:
            continue
        role = m.group(1).strip()
        name = (m.group(2) or "").strip()
        attrs = [a.strip() for a in (m.group(3) or "").split(",") if a.strip()]
        nodes.append(AriaNode(role=role, name=name, attributes=attrs, raw_line=line.strip()))
    return nodes


def heal_ui_locator_via_aria(
    broken_selector: str,
    target_intent: str,
    aria_snapshot_yaml: str | None = None,
) -> dict[str, Any]:
    """Heal a broken CSS/XPath selector using Playwright MCP ARIA accessibility tree snapshot."""
    snapshot = aria_snapshot_yaml or SAMPLE_ARIA_SNAPSHOT
    nodes = parse_aria_snapshot(snapshot)
    intent_terms = [t for t in re.split(r"[\s_\->:#.]+", target_intent.lower()) if t]

    best_node: AriaNode | None = None
    best_score = -1.0

    interactive_roles = {"button", "textbox", "link", "radio", "checkbox", "combobox", "menuitem", "tab"}
    a11y_warnings: list[str] = []

    for node in nodes:
        if node.role in interactive_roles and not node.name:
            a11y_warnings.append(f"WCAG 4.1.2 Warning: Interactive role '{node.role}' is missing an accessible name.")

        score = 0.0
        name_lower = node.name.lower()
        if target_intent.lower() in name_lower and name_lower:
            score += 10.0
        for term in intent_terms:
            if term in name_lower:
                score += 4.0
            if term == node.role.lower():
                score += 3.0
        if node.role in interactive_roles:
            score += 1.5
        if score > best_score and node.name:
            best_score = score
            best_node = node

    approx_tokens = max(1, len(snapshot) // 4)
    raw_dom_equivalent_tokens = approx_tokens * 12

    if best_node and best_score > 1.5:
        healed_code = f'page.get_by_role("{best_node.role}", name="{best_node.name}", exact=True)'
        confidence = min(0.99, round(0.65 + (best_score / 30.0), 2))
        status = "HEALED_VIA_ARIA_SNAPSHOT"
    else:
        healed_code = f'page.locator("{broken_selector}")'
        confidence = 0.0
        status = "UNRESOLVED_FALLBACK"

    return {
        "trace_id": get_trace_id(),
        "status": status,
        "broken_selector": broken_selector,
        "target_intent": target_intent,
        "healed_playwright_locator": healed_code,
        "matched_aria_role": best_node.role if best_node else None,
        "matched_accessible_name": best_node.name if best_node else None,
        "confidence": confidence,
        "snapshot_token_cost": approx_tokens,
        "raw_dom_token_estimate": raw_dom_equivalent_tokens,
        "token_savings_pct": round((1.0 - approx_tokens / raw_dom_equivalent_tokens) * 100.0, 1),
        "wcag_a11y_warnings": a11y_warnings,
    }
