#!/usr/bin/env python3
"""Cross-Platform Portability & Case-Collision Validator for Universal QA Skills."""

from __future__ import annotations

import json
from pathlib import Path


def validate_repo_portability(repo_root: Path | None = None) -> dict:
    root = repo_root or Path(__file__).resolve().parents[2]
    collisions: list[str] = []

    for dirpath, dirnames, filenames in root.walk() if hasattr(root, "walk") else []:
        pass

    # Compatible walk across Python 3.10+
    import os
    for cur_root, dirs, files in os.walk(root):
        if "__pycache__" in cur_root or ".git" in cur_root:
            continue
        seen_lower: dict[str, str] = {}
        for item in [*dirs, *files]:
            low = item.lower()
            if low in seen_lower and seen_lower[low] != item:
                collisions.append(f"{cur_root}: {seen_lower[low]} vs {item}")
            seen_lower[low] = item

    reg_file = root / "skills" / "registry.json"
    reg_data = json.loads(reg_file.read_text(encoding="utf-8"))
    missing_sops = [
        s["id"]
        for s in reg_data.get("skills", [])
        if not (root / s.get("sop_path", "")).exists()
    ]

    return {
        "case_insensitive_safe": len(collisions) == 0,
        "case_collisions": collisions,
        "registered_skills_count": len(reg_data.get("skills", [])),
        "missing_sop_files": missing_sops,
        "portability_passed": len(collisions) == 0 and len(missing_sops) == 0,
    }


if __name__ == "__main__":
    res = validate_repo_portability()
    print(json.dumps(res, ensure_ascii=False, indent=2))
    raise SystemExit(0 if res["portability_passed"] else 1)
