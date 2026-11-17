#!/usr/bin/env python3
"""Local executable helper for qa-mock-service: 由 schema 生成 Mock 响应与状态序列（零依赖）。"""

from __future__ import annotations

import json
import re
import sys

PRODUCTION_HOST_RE = re.compile(r"https?://(?!127\.0\.0\.1|localhost)(?:\w+\.)*\w+", re.I)
SECRET_KEY_HINTS = ("password", "token", "secret", "api_key", "apikey", "authorization")


def sample_from_schema(schema: dict, depth: int = 0) -> object:
    """按 JSON Schema 片段生成合成样例值。"""
    if depth > 6:
        return None
    if "enum" in schema and schema["enum"]:
        return schema["enum"][0]
    t = schema.get("type", "string")
    if isinstance(t, list):
        t = t[0]
    if t == "object":
        props = schema.get("properties", {})
        required = set(schema.get("required", []))
        return {
            k: sample_from_schema(v, depth + 1)
            for k, v in props.items()
            if k in required or depth == 0
        }
    if t == "array":
        return [sample_from_schema(schema.get("items", {"type": "string"}), depth + 1)]
    if t in ("integer", "number"):
        return schema.get("example", schema.get("minimum", 0))
    if t == "boolean":
        return True
    return schema.get("example", "mock_string")


def generate_mock_spec(payload: dict | None = None) -> dict:
    data = payload or {}
    endpoints = data.get("endpoints", [])
    sequence = data.get("state_sequence", [])
    faults = data.get("fault_injection", [])

    issues: list[str] = []
    mocks = []
    for ep in endpoints:
        if not isinstance(ep, dict):
            issues.append("endpoint 必须是对象")
            continue
        url = str(ep.get("url", ""))
        if PRODUCTION_HOST_RE.search(url):
            issues.append(f"检测到非本地生产地址: {url}")
        schema = ep.get("response_schema") or {}
        body = sample_from_schema(schema) if schema else {"_note": "仅结构占位，需补充 response_schema"}
        mocks.append({
            "method": str(ep.get("method", "GET")).upper(),
            "url": url or "127.0.0.1",
            "sample_response": body,
            "schema_defined": bool(schema),
        })

    for item in faults:
        text = json.dumps(item, ensure_ascii=False).lower()
        if any(hint in text for hint in SECRET_KEY_HINTS):
            issues.append("故障注入配置疑似包含真实密钥字段，已拒绝")

    return {
        "skill_id": "qa-mock-service",
        "title": "下游依赖未就绪时的 Mock 服务与联调阻塞解除",
        "stage": "tdm_cases",
        "tier": "L2",
        "mcp_tool_binding": "generate_test_data",
        "status": "BLOCKED" if issues else "READY",
        "mocks": mocks,
        "state_sequence": sequence,
        "fault_injection": faults,
        "rollback_hint": "下游就绪后关闭 Mock 并运行真实集成回归，禁止以 Mock 结果作为上线依据",
        "issues": issues,
    }


if __name__ == "__main__":
    raw = sys.stdin.read() if len(sys.argv) < 2 else sys.argv[1]
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        payload = {"raw": raw}
    print(json.dumps(generate_mock_spec(payload), ensure_ascii=False, indent=2))
