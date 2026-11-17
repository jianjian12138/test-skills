#!/usr/bin/env python3
"""Shadow QA: Traffic Mirroring Baseline Normalization & Zero-Code Payload Diff Engine."""

from __future__ import annotations

from typing import Any

from .router import get_trace_id

VOLATILE_KEYS = {"timestamp", "request_id", "trace_id", "nonce", "server_time", "date", "etag"}


def scrub_volatile_fields(payload: Any) -> Any:
    """Recursively normalize dynamic timestamps, nonces, and trace IDs before snapshot comparison."""
    if isinstance(payload, dict):
        return {
            k: ("<NORMALIZED_VOLATILE>" if k.lower() in VOLATILE_KEYS else scrub_volatile_fields(v))
            for k, v in sorted(payload.items())
        }
    if isinstance(payload, list):
        return [scrub_volatile_fields(x) for x in payload]
    return payload


def diff_shadow_traffic(baseline_resp: dict[str, Any], shadow_resp: dict[str, Any]) -> dict[str, Any]:
    """Compare scrubbed production baseline response against staging shadow response."""
    clean_base = scrub_volatile_fields(baseline_resp)
    clean_shadow = scrub_volatile_fields(shadow_resp)
    drifts: list[dict[str, Any]] = []

    def _compare(path: str, a: Any, b: Any) -> None:
        if type(a) is not type(b):
            drifts.append({
                "path": path,
                "drift_type": "TYPE_MISMATCH",
                "baseline_type": type(a).__name__,
                "shadow_type": type(b).__name__,
            })
            return
        if isinstance(a, dict):
            for k in sorted(set(a.keys()) | set(b.keys())):
                sub = f"{path}.{k}"
                if k not in b:
                    drifts.append({"path": sub, "drift_type": "MISSING_KEY_IN_SHADOW", "baseline_val": a[k]})
                elif k not in a:
                    drifts.append({"path": sub, "drift_type": "EXTRA_KEY_IN_SHADOW", "shadow_val": b[k]})
                else:
                    _compare(sub, a[k], b[k])
        elif isinstance(a, list):
            if len(a) != len(b):
                drifts.append({"path": path, "drift_type": "ARRAY_LENGTH_DRIFT", "baseline_len": len(a), "shadow_len": len(b)})
            for idx, (item_a, item_b) in enumerate(zip(a, b)):
                _compare(f"{path}[{idx}]", item_a, item_b)
        elif a != b:
            drifts.append({"path": path, "drift_type": "VALUE_DRIFT", "baseline_val": a, "shadow_val": b})

    _compare("$", clean_base, clean_shadow)
    return {
        "trace_id": get_trace_id(),
        "parity_passed": len(drifts) == 0,
        "drift_count": len(drifts),
        "drifts": drifts,
    }
