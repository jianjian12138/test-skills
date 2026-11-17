#!/usr/bin/env python3
"""Local executable helper for qa-prompt-refine: 模糊指令诊断与结构化改写骨架。"""

from __future__ import annotations

import json
import re
import sys

VAGUE_TERMS = [
    "尽量", "适当", "差不多", "大致", "视情况", "合理",
    "尽快", "可能的话", "等等", "相关",
]

REQUIRED_DIMENSIONS = {
    "trigger": ("当", "触发条件", "一旦", "如果", "when"),
    "input": ("输入", "接收", "给定", "提供", "input"),
    "output": ("输出", "格式", "表格", "JSON", "output"),
    "acceptance": ("验收", "不少于", "必须", "判定", "条", "acceptance"),
}


def diagnose(raw_prompt: str) -> dict:
    """返回模糊词命中和缺失维度。"""
    hits = [term for term in VAGUE_TERMS if term in raw_prompt]
    missing = [
        key for key, markers in REQUIRED_DIMENSIONS.items()
        if not any(marker in raw_prompt for marker in markers)
    ]
    return {"vague_terms": hits, "missing_dimensions": missing}


def build_skeleton(raw_prompt: str, diagnosis: dict | None = None) -> dict:
    diag = diagnosis or diagnose(raw_prompt)
    skeleton = {
        "trigger": "当用户提供 <被测对象/文档> 时",
        "input": "输入契约：<字段/来源/约束>，缺失时先输出澄清清单",
        "output": "输出规约：<结构化 JSON 或固定列数的 Markdown 表格>",
        "acceptance": "验收标准：给出 3–5 条可判定检查项（数量/格式/阈值）",
    }
    acceptance = [
        "产出结构在三次重复输入下保持一致",
        "所有关键字段有明确来源，未使用猜测默认值",
        "验收项均可二值判定（是/否），不含模糊词",
    ]
    status = "READY" if not diag["vague_terms"] and not diag["missing_dimensions"] else "NEEDS_REFINE"
    return {
        "skill_id": "qa-prompt-refine",
        "title": "模糊测试指令打磨为有输入、有约束、有验收标准的可执行 Prompt",
        "stage": "requirements",
        "tier": "L1",
        "mcp_tool_binding": "route_qa_skills",
        "status": status,
        "diagnosis": diag,
        "rewrite_skeleton": skeleton,
        "acceptance_criteria": acceptance,
    }


if __name__ == "__main__":
    raw = sys.stdin.read() if len(sys.argv) < 2 else sys.argv[1]
    try:
        payload = json.loads(raw)
        text = payload.get("raw_prompt", "") if isinstance(payload, dict) else str(payload)
    except json.JSONDecodeError:
        text = raw
    print(json.dumps(build_skeleton(text), ensure_ascii=False, indent=2))
