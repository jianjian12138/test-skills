#!/usr/bin/env python3
"""Self-test for skill package: qa-incident-retro."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_runner():
    path = ROOT / "scripts" / "skill_runner.py"
    spec = importlib.util.spec_from_file_location("qa_incident_retro_runner", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestSkillPackage(unittest.TestCase):
    def test_skill_files_exist(self) -> None:
        self.assertTrue((ROOT / "SKILL.md").exists())
        self.assertTrue((ROOT / "references" / "domain_guide.md").exists())
        self.assertTrue((ROOT / "scripts" / "skill_runner.py").exists())

    def test_complete_retro_is_ready(self) -> None:
        runner = _load_runner()
        result = runner.build_retro_report({
            "timeline": [{"time": "10:00", "event": "告警", "evidence": "trace-1"}],
            "root_causes": {"direct": "连接池耗尽", "why_chain": "峰值未评估", "systemic": "缺容量门禁"},
            "action_items": [{
                "item": "补容量压测", "owner": "张三",
                "due_date": "2026-12-01", "acceptance": "覆盖 3 倍峰值且 P99 < 500ms",
            }],
        })
        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["action_items"][0]["owner"], "张三")

    def test_action_item_without_owner_is_blocked(self) -> None:
        runner = _load_runner()
        result = runner.build_retro_report({
            "timeline": [],
            "root_causes": {},
            "action_items": [{"item": "优化", "owner": "待定", "due_date": "x", "acceptance": ""}],
        })
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(any("责任人" in issue for issue in result["issues"]))


if __name__ == "__main__":
    unittest.main()
