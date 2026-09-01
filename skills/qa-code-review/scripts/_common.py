#!/usr/bin/env python3
"""Vendored common helpers for this skill.

Self-contained copy so the skill can be distributed as a single directory
and used by any agent that runs its scripts. Mirrors the shared contract:
- emit_signal writes signals/<skill>.json only when signals is non-empty
- load_json / save_json / read_text use UTF-8
"""
import json
import os
from datetime import datetime


# A-04 入口校验：vendored 副本须在导入期确认自身为受治理副本（与 signal-schema
# 一致的 schema_version），防止被静默改坏导致信号契约漂移；单例共享由
# check_drift 规则 9（字节一致）强制。
SCHEMA_VERSION = "1.0"


def _self_check():
    if SCHEMA_VERSION != "1.0":
        raise RuntimeError("vendored _common.py schema_version 漂移（应为 1.0）")


_self_check()


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(obj, path, indent=2):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent)


def read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def emit_signal(skill, signals, signals_dir="signals"):
    """Write signals/<skill>.json per the quality-signal contract.

    No file is written when signals is empty (clean run).
    """
    if not signals:
        return
    os.makedirs(signals_dir, exist_ok=True)
    doc = {
        "source": skill,
        "generated_at": datetime.now().isoformat(),
        "schema_version": "1.0",
        "signals": signals,
    }
    with open(os.path.join(signals_dir, f"{skill}.json"), "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
def wilson_ci(p, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    phat = p / n
    denom = 1 + z * z / n
    center = (phat + z * z / (2 * n)) / denom
    margin = (z * ((phat * (1 - phat) + z * z / (4 * n)) / n) ** 0.5) / denom
    return (max(0.0, center - margin), min(1.0, center + margin))


def two_prop_z(p1, n1, p2, n2):
    if n1 == 0 or n2 == 0:
        return 0.0
    p_pool = (p1 + p2) / (n1 + n2)
    se = (p_pool * (1 - p_pool) * (1 / n1 + 1 / n2)) ** 0.5
    if se == 0:
        return 0.0
    return (p1 / n1 - p2 / n2) / se
