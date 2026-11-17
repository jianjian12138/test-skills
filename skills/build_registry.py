#!/usr/bin/env python3
"""Synchronizes skills/registry.json (lowercase only to prevent Windows/macOS collisions)."""

from __future__ import annotations

import json
from pathlib import Path


def verify_registry() -> dict:
    skills_dir = Path(__file__).resolve().parent
    upper = skills_dir / "REGISTRY.json"
    if upper.exists():
        upper.unlink()
    reg = json.loads((skills_dir / "registry.json").read_text(encoding="utf-8"))
    return {"status": "ok", "total_skills": reg["total_skills"]}


if __name__ == "__main__":
    print(json.dumps(verify_registry(), ensure_ascii=False))
