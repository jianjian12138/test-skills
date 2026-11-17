#!/usr/bin/env python3
"""Comprehensive Zero-Token Unit & Integration Test Suite for test-skills v12.0.0 (L6.0)."""

from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from evals.run_evals import compute_pass_at_k, compute_tau_pass_hat_k, run_evaluation_suite
from skills.tools.api_contract_fuzzer import (
    detect_openapi_breaking_changes,
    generate_3d_bola_fuzz_matrix,
    resolve_openapi_refs,
)
from skills.tools.mcp_server import handle_mcp_request
from skills.tools.red_blue_swarm import run_red_blue_adversarial_swarm
from skills.tools.router import ProgressiveSkillRouter
from skills.tools.shadow_qa import diff_shadow_traffic
from skills.tools.tdm_factory import (
    generate_id_card,
    generate_order_state_chain,
    sanitize_sensitive_data,
    verify_id_card_checksum,
)
from skills.tools.tia_engine import run_hybrid_tia
from skills.tools.ui_healer import heal_ui_locator_via_aria

REPO_ROOT = Path(__file__).resolve().parents[1]


class TestUniversalQASkillsV12(unittest.TestCase):
    def test_01_registry_and_progressive_router(self) -> None:
        router = ProgressiveSkillRouter(REPO_ROOT)
        all_skills = router.list_all()
        self.assertEqual(len(all_skills), 40)

        routed = router.route("Playwright ARIA 无障碍树选择器自愈", top_k=4)
        self.assertLessEqual(routed["candidate_count"], 4)
        top_ids = [c["id"] for c in routed["candidates"]]
        self.assertIn("qa-ui-automation", top_ids)
        self.assertGreater(routed["telemetry"]["token_reduction_pct"], 85.0)

        sop = router.load_skill_sop("qa-ui-automation")
        self.assertEqual(sop["status"], "ok")
        self.assertIn("4-Panel Boundary Blueprint", sop["sop_markdown"])

    def test_02_tdm_id_checksum_and_order_chain(self) -> None:
        for seed in range(10, 25):
            cid = generate_id_card(seed=seed)
            self.assertEqual(len(cid), 18)
            self.assertTrue(verify_id_card_checksum(cid))

        chain = generate_order_state_chain(count=3, seed=99)
        self.assertTrue(chain["referential_integrity_verified"])
        self.assertEqual(len(chain["tables"]["users"]), 3)
        self.assertEqual(len(chain["tables"]["orders"]), 3)
        for inv in chain["tables"]["inventory_ledger"]:
            self.assertTrue(inv["invariant_ok"])

    def test_03_pii_and_secret_sanitizer(self) -> None:
        sample_id = generate_id_card(seed=1)
        raw = f"客户身份证 {sample_id}，手机号 13987654321，密钥 sk-abcdefgh1234567890"
        res = sanitize_sensitive_data(raw)
        self.assertEqual(res["redaction_count"], 3)
        self.assertNotIn(sample_id, res["sanitized_text"])
        self.assertNotIn("13987654321", res["sanitized_text"])
        self.assertIn("[REDACTED_SECRET:", res["sanitized_text"])

    def test_04_hybrid_tia_with_sqlite_coverage_db(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cov_db = Path(tmpdir) / ".coverage"
            db_handle = sqlite3.connect(str(cov_db))
            db_handle.execute("CREATE TABLE file (id INTEGER PRIMARY KEY, path TEXT)")
            db_handle.execute("CREATE TABLE context (id INTEGER PRIMARY KEY, context TEXT)")
            db_handle.execute("CREATE TABLE line_map (file_id INTEGER, context_id INTEGER, lines TEXT)")
            db_handle.execute("INSERT INTO file VALUES (1, 'skills/tools/router.py')")
            db_handle.execute("INSERT INTO context VALUES (1, 'tests/test_v12_suite.py::test_dynamic_router_hit')")
            db_handle.execute("INSERT INTO line_map VALUES (1, 1, '55,58,59,60')")
            db_handle.commit()
            db_handle.close()

            fake_diff = (
                "--- a/skills/tools/router.py\n"
                "+++ b/skills/tools/router.py\n"
                "@@ -58,0 +58,2 @@\n"
                "+    # dynamic line change\n"
            )
            tia_res = run_hybrid_tia(REPO_ROOT, raw_diff_override=fake_diff, cov_db_path=cov_db)
            self.assertEqual(tia_res["engine_mode"], "HYBRID_AST_PLUS_COVERAGE_SQLITE")
            self.assertIn("tests/test_v12_suite.py::test_dynamic_router_hit", tia_res["dynamic_coverage_tests"])

    def test_05_playwright_aria_snapshot_healer(self) -> None:
        res = heal_ui_locator_via_aria("#old-submit", "立即提交并支付")
        self.assertEqual(res["status"], "HEALED_VIA_ARIA_SNAPSHOT")
        self.assertEqual(res["matched_aria_role"], "button")
        self.assertIn('page.get_by_role("button", name="立即提交并支付", exact=True)', res["healed_playwright_locator"])
        self.assertLess(res["snapshot_token_cost"], 400)

    def test_06_openapi_ref_and_3d_bola_matrix(self) -> None:
        spec = {
            "paths": {"/orders": {"post": {"requestBody": {"content": {"application/json": {"schema": {"$ref": "#/components/schemas/OrderReq"}}}}}}},
            "components": {"schemas": {"OrderReq": {"type": "object", "required": ["sku_id"]}}},
        }
        resolved = resolve_openapi_refs(spec)
        req_list = resolved["paths"]["/orders"]["post"]["requestBody"]["content"]["application/json"]["schema"]["required"]
        self.assertEqual(req_list, ["sku_id"])

        new_spec = {
            "paths": {"/orders": {"post": {"requestBody": {"content": {"application/json": {"schema": {"type": "object", "required": ["sku_id", "tenant_token"]}}}}}}}
        }
        diff = detect_openapi_breaking_changes(spec, new_spec)
        self.assertFalse(diff["compatible"])
        self.assertEqual(diff["breaking_changes"][0]["type"], "NEW_REQUIRED_REQUEST_FIELD")

        bola = generate_3d_bola_fuzz_matrix("/api/v1/orders/{id}")
        self.assertEqual(bola["total_vectors"], 36)

    def test_07_shadow_qa_and_red_blue_swarm(self) -> None:
        base = {"status": 200, "timestamp": 100, "data": {"items": [1, 2]}}
        shad = {"status": 200, "timestamp": 999, "data": {"items": [1, 2]}}
        parity = diff_shadow_traffic(base, shad)
        self.assertTrue(parity["parity_passed"])

        swarm = run_red_blue_adversarial_swarm(rounds=6)
        self.assertEqual(swarm["total_rounds"], 6)
        self.assertEqual(swarm["escape_rate_after_heal_pct"], 0.0)

    def test_08_mcp_jsonrpc_protocol_handler(self) -> None:
        init_resp = handle_mcp_request({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        self.assertEqual(init_resp["result"]["serverInfo"]["version"], "12.0.0")

        list_resp = handle_mcp_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        self.assertEqual(len(list_resp["result"]["tools"]), 9)

        call_resp = handle_mcp_request({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "route_qa_skills", "arguments": {"query": "OWASP Agentic 安全红队", "top_k": 3}},
        })
        self.assertFalse(call_resp["result"]["isError"])

    def test_09_tau_bench_pass_hat_k_math_and_suite(self) -> None:
        # At p = 0.85 and k = 5: Pass@5 = 99.99%, pass^5 = 44.37%
        self.assertGreater(compute_pass_at_k(0.85, 5), 99.9)
        self.assertAlmostEqual(compute_tau_pass_hat_k(0.85, 5), 44.37, places=2)

        eval_summary = run_evaluation_suite(k=5)
        self.assertTrue(eval_summary["gate_passed"])
        self.assertGreaterEqual(eval_summary["avg_tau_pass_hat_k_pct"], 85.0)


if __name__ == "__main__":
    unittest.main()
