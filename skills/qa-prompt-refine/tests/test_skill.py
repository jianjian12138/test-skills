#!/usr/bin/env python3
"""Self-test for skill package: qa-prompt-refine."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_runner():
    path = ROOT / "scripts" / "skill_runner.py"
    spec = importlib.util.spec_from_file_location("qa_prompt_refine_runner", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestSkillPackage(unittest.TestCase):
    def test_skill_files_exist(self) -> None:
        self.assertTrue((ROOT / "SKILL.md").exists())
        self.assertTrue((ROOT / "references" / "domain_guide.md").exists())
        self.assertTrue((ROOT / "scripts" / "skill_runner.py").exists())

    def test_vague_prompt_is_flagged(self) -> None:
        runner = _load_runner()
        result = runner.build_skeleton("帮我尽量写点用例，差不多就行")
        self.assertEqual(result["status"], "NEEDS_REFINE")
        self.assertIn("尽量", result["diagnosis"]["vague_terms"])
        self.assertTrue(result["diagnosis"]["missing_dimensions"])

    def test_explicit_prompt_is_ready(self) -> None:
        runner = _load_runner()
        result = runner.build_skeleton(
            "当用户提供 PRD 时，接收需求文档，输出三列表格，必须包含不少于 3 条风险项"
        )
        self.assertEqual(result["status"], "READY")
        self.assertEqual(len(result["acceptance_criteria"]), 3)


if __name__ == "__main__":
    unittest.main()
