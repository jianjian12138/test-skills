#!/usr/bin/env python3
"""OpenAPI 3.0/3.1 Recursive $ref Resolver, Breaking Change Detector & Stateful 3D BOLA Fuzzer."""

from __future__ import annotations

import copy
from typing import Any

from .router import get_trace_id


def resolve_openapi_refs(spec: dict[str, Any], max_depth: int = 8) -> dict[str, Any]:
    """Recursively resolve local JSON Pointer $ref (#/components/schemas/...) with cycle protection."""
    root = copy.deepcopy(spec)

    def _lookup_pointer(ptr: str) -> Any:
        if not ptr.startswith("#/"):
            return {}
        parts = ptr[2:].split("/")
        cur: Any = root
        for p in parts:
            p_unescaped = p.replace("~1", "/").replace("~0", "~")
            if isinstance(cur, dict) and p_unescaped in cur:
                cur = cur[p_unescaped]
            else:
                return {}
        return copy.deepcopy(cur)

    def _walk(node: Any, depth: int, seen: set[str]) -> Any:
        if depth > max_depth:
            return node
        if isinstance(node, dict):
            if "$ref" in node and isinstance(node["$ref"], str):
                ref_str = node["$ref"]
                if ref_str in seen:
                    return {"_circular_ref": ref_str}
                target = _lookup_pointer(ref_str)
                return _walk(target, depth + 1, seen | {ref_str})
            return {k: _walk(v, depth + 1, seen) for k, v in node.items()}
        if isinstance(node, list):
            return [_walk(item, depth + 1, seen) for item in node]
        return node

    return _walk(root, 0, set())


def detect_openapi_breaking_changes(old_spec: dict[str, Any], new_spec: dict[str, Any]) -> dict[str, Any]:
    """Compare two OpenAPI specs (after $ref resolution) and report breaking changes."""
    old_resolved = resolve_openapi_refs(old_spec)
    new_resolved = resolve_openapi_refs(new_spec)

    breaking_changes: list[dict[str, str]] = []
    old_paths = old_resolved.get("paths", {})
    new_paths = new_resolved.get("paths", {})

    for path_key, old_methods in old_paths.items():
        if path_key not in new_paths:
            breaking_changes.append({
                "severity": "CRITICAL",
                "type": "ENDPOINT_REMOVED",
                "location": path_key,
                "detail": f"Endpoint '{path_key}' was removed in candidate OpenAPI spec.",
            })
            continue
        new_methods = new_paths[path_key]
        for method, old_op in old_methods.items():
            if method not in new_methods:
                breaking_changes.append({
                    "severity": "HIGH",
                    "type": "HTTP_METHOD_REMOVED",
                    "location": f"{method.upper()} {path_key}",
                    "detail": f"Method '{method.upper()}' removed from '{path_key}'.",
                })
                continue
            new_op = new_methods[method]
            # Check newly added required requestBody properties
            old_req_props = (
                old_op.get("requestBody", {})
                .get("content", {})
                .get("application/json", {})
                .get("schema", {})
                .get("required", [])
            )
            new_req_props = (
                new_op.get("requestBody", {})
                .get("content", {})
                .get("application/json", {})
                .get("schema", {})
                .get("required", [])
            )
            added_req = set(new_req_props) - set(old_req_props)
            for req_field in sorted(added_req):
                breaking_changes.append({
                    "severity": "HIGH",
                    "type": "NEW_REQUIRED_REQUEST_FIELD",
                    "location": f"{method.upper()} {path_key}",
                    "detail": f"New required request field '{req_field}' breaks existing clients.",
                })

    return {
        "trace_id": get_trace_id(),
        "compatible": len(breaking_changes) == 0,
        "breaking_change_count": len(breaking_changes),
        "breaking_changes": breaking_changes,
    }


def generate_3d_bola_fuzz_matrix(resource_endpoint: str = "/api/v1/orders/{order_id}") -> dict[str, Any]:
    """Generate a 3D BOLA/IDOR stateful property-based test matrix (Tenant × Role × Resource State)."""
    actors = [
        ("Tenant_A_Owner", "TENANT_A", "OWNER", True),
        ("Tenant_B_Horizontal_Attacker", "TENANT_B", "OWNER", False),
        ("Tenant_A_Readonly_Auditor", "TENANT_A", "AUDITOR_RO", False),
        ("Anonymous_Unauthenticated", "NONE", "ANONYMOUS", False),
    ]
    operations = ["GET", "PATCH", "DELETE"]
    states = ["CREATED", "PAID", "ARCHIVED"]

    matrix: list[dict[str, Any]] = []
    for actor_name, tenant, role, is_owner in actors:
        for method in operations:
            for state in states:
                if role == "ANONYMOUS":
                    expected_status = [401]
                elif not is_owner and not (tenant == "TENANT_A" and role == "AUDITOR_RO" and method == "GET"):
                    expected_status = [403, 404]
                elif state == "ARCHIVED" and method in ("PATCH", "DELETE"):
                    expected_status = [409, 422]
                else:
                    expected_status = [200, 204]

                matrix.append({
                    "case_id": f"BOLA-{actor_name[:8].upper()}-{method}-{state}",
                    "actor": actor_name,
                    "tenant": tenant,
                    "role": role,
                    "http_method": method,
                    "endpoint": resource_endpoint,
                    "resource_state": state,
                    "expected_http_status": expected_status,
                    "security_invariant": "MUST_NOT_RETURN_2XX" if expected_status in ([401], [403, 404]) else "STATE_TRANSITION_VALID",
                })

    return {
        "trace_id": get_trace_id(),
        "endpoint": resource_endpoint,
        "dimensions": "4 Actors × 3 HTTP Verbs × 3 Lifecycle States = 36 Stateful BOLA Vectors",
        "total_vectors": len(matrix),
        "vectors": matrix,
    }
