#!/usr/bin/env python3
"""Self-test for skill package: qa-code-review."""

from __future__ import annotations

import unittest
from pathlib import Path


class TestSkillPackage(unittest.TestCase):
    def test_skill_files_exist(self) -> None:
        root = Path(__file__).resolve().parents[1]
        self.assertTrue((root / "SKILL.md").exists())
        self.assertTrue((root / "references" / "domain_guide.md").exists())
        self.assertTrue((root / "scripts" / "skill_runner.py").exists())


if __name__ == "__main__":
    unittest.main()
