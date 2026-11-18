#!/usr/bin/env python3
"""Universal QA Skills v12.1.0 — Zero-Dependency Dual-Mode MCP Server (stdio + Streamable HTTP)."""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

# Allow running both as module and standalone script
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from skills.tools.api_contract_fuzzer import generate_3d_bola_fuzz_matrix  # noqa: E402
from skills.tools.red_blue_swarm import run_red_blue_adversarial_swarm  # noqa: E402
from skills.tools.router import ProgressiveSkillRouter, get_trace_id, new_trace_id  # noqa: E402
from skills.tools.tdm_factory import generate_test_data_batch, sanitize_sensitive_data  # noqa: E402
from skills.tools.tia_engine import run_hybrid_tia  # noqa: E402
from skills.tools.ui_healer import heal_ui_locator_via_aria  # noqa: E402

ROUTER = ProgressiveSkillRouter(REPO_ROOT)

MCP_TOOLS_SCHEMA = [
    {
        "name": "route_qa_skills",
        "description": "[L1 Router] 将 49 个 QA 技能按查询意图与阶段收敛至 <= 5 个高相关候选，降低 80%+ 上下文 Token 消耗。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "测试任务或问题关键词"},
                "stage": {"type": "string", "description": "可选阶段过滤 (requirements/tdm_cases/api_testing/ui_mobile/performance/security/release_ops/quality_gates_agent)"},
                "top_k": {"type": "integer", "default": 4},
            },
            "required": ["query"],
        },
    },
    {
        "name": "load_skill_sop",
        "description": "[L2 Loader] 按需加载指定 QA 技能的完整 SKILL.md 规约与四维边界契约。",
        "inputSchema": {
            "type": "object",
            "properties": {"skill_id": {"type": "string", "description": "技能 ID，如 qa-ui-automation"}},
            "required": ["skill_id"],
        },
    },
    {
        "name": "list_qa_skills",
        "description": "检索全部 49 个细分领域 QA 技能清单。",
        "inputSchema": {
            "type": "object",
            "properties": {"stage": {"type": "string", "description": "可选阶段过滤"}},
        },
    },
    {
        "name": "generate_test_data",
        "description": "动态生成中国大陆合规身份证号(GB 11643-1999)、手机号、姓名或跨表关联订单状态机数据(order_chain)。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "data_type": {"type": "string", "enum": ["id_card", "phone", "name", "order_chain"], "default": "id_card"},
                "count": {"type": "integer", "default": 3},
            },
        },
    },
    {
        "name": "sanitize_sensitive_data",
        "description": "主动清洗与掩码脱敏输入文本中的大陆身份证、手机号与 API 密钥。",
        "inputSchema": {
            "type": "object",
            "properties": {"text": {"type": "string", "description": "待脱敏原始文本"}},
            "required": ["text"],
        },
    },
    {
        "name": "run_tia_analysis",
        "description": "运行动静融合 TIA 精准测试分析（Git Diff + Python AST + coverage.py SQLite 动态上下文）。",
        "inputSchema": {
            "type": "object",
            "properties": {"diff_target": {"type": "string", "default": "HEAD~1"}},
        },
    },
    {
        "name": "heal_ui_locator_aria",
        "description": "基于 Playwright MCP ARIA 无障碍树快照（200-400 Tokens）自愈失效的 UI 选择器。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "broken_selector": {"type": "string"},
                "target_intent": {"type": "string"},
                "aria_snapshot_yaml": {"type": "string"},
            },
            "required": ["broken_selector", "target_intent"],
        },
    },
    {
        "name": "run_quality_gate",
        "description": "执行上线质量红线门禁评估或生成 3D BOLA 接口越权测试矩阵。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "coverage_pct": {"type": "number", "default": 88.5},
                "pass_k_score": {"type": "number", "default": 86.0},
                "p0_bugs": {"type": "integer", "default": 0},
                "endpoint": {"type": "string", "default": "/api/v1/orders/{order_id}"},
            },
        },
    },
    {
        "name": "run_red_blue_swarm",
        "description": "运行对齐 OWASP Agentic Top 10 (ASI:2026) 与 AST10 的红蓝对抗自主进化飞轮。",
        "inputSchema": {
            "type": "object",
            "properties": {"rounds": {"type": "integer", "default": 6}},
        },
    },
    {
        "name": "list_scenario_templates",
        "description": "[骨·肉·尺场景模具] 获取与具体业务解耦的通用业务场景骨架模板清单或指定模板全文。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "template_id": {"type": "string", "description": "可选模板 ID，如 SCEN-MASTER 或 SCEN-TPL-01"}
            },
        },
    },
]


def handle_mcp_request(req: dict[str, Any]) -> dict[str, Any]:
    """Process a single JSON-RPC 2.0 MCP request and return a JSON-RPC 2.0 response."""
    new_trace_id("mcp")
    req_id = req.get("id")
    method = req.get("method", "")
    params = req.get("params") or {}

    if method == "initialize":
        result = {
            "protocolVersion": "2025-11-25",
            "serverInfo": {
                "name": "universal-qa-skills-l6",
                "version": "12.1.0",
                "transports": ["stdio", "streamable-http"],
            },
            "capabilities": {"tools": {"listChanged": False}},
        }
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": MCP_TOOLS_SCHEMA}}

    if method == "tools/call":
        name = params.get("name", "")
        args = params.get("arguments") or {}
        try:
            payload = dispatch_tool_call(name, args)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False, indent=2)}],
                    "isError": False,
                },
            }
        except Exception as exc:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps({"error": str(exc), "trace_id": get_trace_id()}, ensure_ascii=False)}],
                    "isError": True,
                },
            }

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Method '{method}' not supported."},
    }


def dispatch_tool_call(name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Dispatch MCP tool invocation to underlying L6.0 engine."""
    if name == "route_qa_skills":
        return ROUTER.route(
            query=str(args.get("query", "")),
            stage=str(args.get("stage", "")),
            top_k=int(args.get("top_k", 4)),
        )
    if name == "load_skill_sop":
        return ROUTER.load_skill_sop(str(args.get("skill_id", "")))
    if name == "list_qa_skills":
        skills = ROUTER.list_all(stage=str(args.get("stage", "")))
        return {"trace_id": get_trace_id(), "total": len(skills), "skills": skills}
    if name == "generate_test_data":
        return generate_test_data_batch(
            data_type=str(args.get("data_type", "id_card")),
            count=int(args.get("count", 3)),
        )
    if name == "sanitize_sensitive_data":
        return sanitize_sensitive_data(str(args.get("text", "")))
    if name == "run_tia_analysis":
        return run_hybrid_tia(REPO_ROOT, diff_target=str(args.get("diff_target", "HEAD~1")))
    if name == "heal_ui_locator_aria":
        return heal_ui_locator_via_aria(
            broken_selector=str(args.get("broken_selector", "#submit-btn")),
            target_intent=str(args.get("target_intent", "立即提交并支付")),
            aria_snapshot_yaml=args.get("aria_snapshot_yaml"),
        )
    if name == "run_quality_gate":
        cov = float(args.get("coverage_pct", 88.5))
        pk = float(args.get("pass_k_score", 86.0))
        p0 = int(args.get("p0_bugs", 0))
        passed = cov >= 80.0 and pk >= 80.0 and p0 == 0
        bola = generate_3d_bola_fuzz_matrix(str(args.get("endpoint", "/api/v1/orders/{order_id}")))
        return {
            "trace_id": get_trace_id(),
            "gate_passed": passed,
            "metrics": {"coverage_pct": cov, "tau_bench_pass_5_pct": pk, "p0_bugs": p0},
            "bola_preview_vectors": bola["total_vectors"],
        }
    if name == "list_scenario_templates":
        return ROUTER.list_scenario_templates(str(args.get("template_id", "")))
    if name == "run_red_blue_swarm":
        return run_red_blue_adversarial_swarm(rounds=int(args.get("rounds", 6)))
    raise ValueError(f"Unknown MCP tool: {name}")


class StreamableHTTPMCPHandler(BaseHTTPRequestHandler):
    """MCP 2025-11-25 / 2026 Streamable HTTP single-endpoint transport handler."""

    sessions: dict[str, str] = {}

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        return

    def do_GET(self) -> None:  # noqa: N802
        if self.path.startswith("/mcp"):
            body = json.dumps({
                "service": "universal-qa-skills-l6",
                "version": "12.1.0",
                "transport": "streamable-http",
                "status": "ready",
                "tools_count": len(MCP_TOOLS_SCHEMA),
            }).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_error(404)

    def do_POST(self) -> None:  # noqa: N802
        if not self.path.startswith("/mcp"):
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        session_id = self.headers.get("Mcp-Session-Id") or f"mcp-sess-{uuid.uuid4().hex[:10]}"
        payload = json.loads(raw)
        if isinstance(payload, list):
            resp_obj = [handle_mcp_request(item) for item in payload]
        else:
            resp_obj = handle_mcp_request(payload)

        body = json.dumps(resp_obj, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Mcp-Session-Id", session_id)
        self.send_header("X-Trace-Id", get_trace_id())
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_stdio_server() -> None:
    """Run MCP server over standard input/output (stdio)."""
    for line in sys.stdin:
        line_str = line.strip()
        if not line_str:
            continue
        req = json.loads(line_str)
        resp = handle_mcp_request(req)
        sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
        sys.stdout.flush()


def run_http_server(host: str = "127.0.0.1", port: int = 8765) -> None:
    """Run MCP server over Streamable HTTP transport."""
    server = HTTPServer((host, port), StreamableHTTPMCPHandler)
    print(f"[MCP Streamable HTTP] Listening on http://{host}:{port}/mcp")
    server.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description="Universal QA Skills v12.1.0 MCP Server")
    parser.add_argument("--transport", choices=["stdio", "http"], default="stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if args.transport == "http":
        run_http_server(args.host, args.port)
    else:
        run_stdio_server()


if __name__ == "__main__":
    main()
