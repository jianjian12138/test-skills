#!/usr/bin/env python3
"""Unified Quality Gate Runner (L6.0 compatibility module)."""

from __future__ import annotations

import json
from .mcp_server import dispatch_tool_call


def evaluate_release_gates(coverage_pct: float = 90.0, pass_k_score: float = 92.0, p0_bugs: int = 0) -> dict:
    return dispatch_tool_call(
        "run_quality_gate",
        {"coverage_pct": coverage_pct, "pass_k_score": pass_k_score, "p0_bugs": p0_bugs},
    )


if __name__ == "__main__":
    print(json.dumps(evaluate_release_gates(), ensure_ascii=False, indent=2))
