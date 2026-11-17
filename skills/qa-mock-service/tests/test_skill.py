#!/usr/bin/env python3
"""Self-test for skill package: qa-mock-service."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_runner():
    path = ROOT / "scripts" / "skill_runner.py"
    spec = importlib.util.spec_from_file_location("qa_mock_service_runner", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestSkillPackage(unittest.TestCase):
    def test_skill_files_exist(self) -> None:
        self.assertTrue((ROOT / "SKILL.md").exists())
        self.assertTrue((ROOT / "references" / "domain_guide.md").exists())
        self.assertTrue((ROOT / "scripts" / "skill_runner.py").exists())

    def test_mock_generation_from_schema(self) -> None:
        runner = _load_runner()
        result = runner.generate_mock_spec({
            "endpoints": [{
                "method": "POST", "url": "127.0.0.1:9000/orders",
                "response_schema": {
                    "type": "object",
                    "properties": {"order_id": {"type": "string", "example": "MOCK-001"},
                                   "status": {"type": "string", "enum": ["CREATED"]}},
                    "required": ["order_id", "status"],
                },
            }],
            "state_sequence": ["CREATED", "PAID"],
        })
        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["mocks"][0]["sample_response"]["status"], "CREATED")
        self.assertTrue(result["rollback_hint"])

    def test_production_url_is_blocked(self) -> None:
        runner = _load_runner()
        result = runner.generate_mock_spec({
            "endpoints": [{"method": "GET", "url": "https://api.example.com/pay"}],
        })
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(any("生产地址" in issue for issue in result["issues"]))


if __name__ == "__main__":
    unittest.main()
