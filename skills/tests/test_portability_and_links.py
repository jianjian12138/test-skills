#!/usr/bin/env python3
"""Verifies zero deadlinks and zero case collisions across the skills directory."""

from __future__ import annotations

import unittest
from skills._diag_deadlink import scan_deadlinks
from skills.tools.validate_portability import validate_repo_portability


class TestSkillsIntegrity(unittest.TestCase):
    def test_zero_deadlinks(self) -> None:
        res = scan_deadlinks()
        self.assertTrue(res["passed"], f"Deadlinks found: {res['deadlinks']}")

    def test_zero_case_collisions(self) -> None:
        res = validate_repo_portability()
        self.assertTrue(res["portability_passed"], f"Portability issues: {res}")


if __name__ == "__main__":
    unittest.main()
