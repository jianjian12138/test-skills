#!/usr/bin/env python3
"""Scans all SKILL.md files to verify zero broken local relative markdown links."""

from __future__ import annotations

import json
import re
from pathlib import Path


def scan_deadlinks(repo_root: Path | None = None) -> dict:
    root = repo_root or Path(__file__).resolve().parents[1]
    deadlinks: list[str] = []
    link_re = re.compile(r"\[[^\]]+\]\(([^)]+)\)")

    for md_file in sorted((root / "skills").rglob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        for match in link_re.finditer(text):
            target = match.group(1).strip()
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            target_path = (md_file.parent / target).resolve()
            if not target_path.exists():
                deadlinks.append(f"{md_file.relative_to(root)} -> {target}")

    return {"deadlink_count": len(deadlinks), "deadlinks": deadlinks, "passed": len(deadlinks) == 0}


if __name__ == "__main__":
    res = scan_deadlinks()
    print(json.dumps(res, ensure_ascii=False, indent=2))
    raise SystemExit(0 if res["passed"] else 1)
