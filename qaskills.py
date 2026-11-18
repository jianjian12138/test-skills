#!/usr/bin/env python3
"""Universal QA Skills (v12.1.0 — L6.0 Industrial Edition) Unified CLI."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from skills.tools.api_contract_fuzzer import generate_3d_bola_fuzz_matrix  # noqa: E402
from skills.tools.mcp_server import run_http_server, run_stdio_server  # noqa: E402
from skills.tools.red_blue_swarm import run_red_blue_adversarial_swarm  # noqa: E402
from skills.tools.router import ProgressiveSkillRouter, new_trace_id  # noqa: E402
from skills.tools.tdm_factory import generate_test_data_batch, sanitize_sensitive_data  # noqa: E402
from skills.tools.tia_engine import run_hybrid_tia  # noqa: E402
from skills.tools.ui_healer import heal_ui_locator_via_aria  # noqa: E402


def main() -> int:
    new_trace_id("cli")
    parser = argparse.ArgumentParser(
        prog="qaskills",
        description="Universal QA Skills v12.1.0 (L6.0 Autonomous Quality Engineering Mesh)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="列出全部 49 个细分 QA 技能")
    p_list.add_argument("--stage", default="", help="按生命周期阶段过滤")

    p_search = sub.add_parser("search", help="按关键词搜索 QA 技能")
    p_search.add_argument("keyword", help="搜索关键词")

    p_route = sub.add_parser("route", help="[L6.0 新增] L1/L2 渐进式技能路由 (收敛至 <= 5 个候选)")
    p_route.add_argument("query", help="测试需求或问题描述")
    p_route.add_argument("--stage", default="", help="阶段过滤")
    p_route.add_argument("--top-k", type=int, default=4)

    p_load = sub.add_parser("load", help="[L6.0 新增] 按需加载指定技能的完整 SKILL.md SOP")
    p_load.add_argument("skill_id", help="技能 ID，如 qa-ui-automation")

    p_data = sub.add_parser("data", help="生成中国大陆合规脱敏测试数据或跨表订单状态机数据")
    p_data.add_argument("--type", dest="data_type", choices=["id_card", "phone", "name", "order_chain"], default="id_card")
    p_data.add_argument("--count", type=int, default=3)

    p_san = sub.add_parser("sanitize", help="主动清洗文本中的大陆身份证、手机号与密钥")
    p_san.add_argument("text", help="待清洗文本")

    p_tia = sub.add_parser("tia", help="运行动静融合 TIA 精准测试分析 (AST + Coverage SQLite)")
    p_tia.add_argument("--diff", default="HEAD~1", help="Git Diff 目标版本")

    p_aria = sub.add_parser("aria-heal", help="[L6.0 新增] 基于 Playwright MCP ARIA 快照自愈失效选择器")
    p_aria.add_argument("--selector", default="#legacy-pay-btn", help="失效的原选择器")
    p_aria.add_argument("--intent", default="立即提交并支付", help="目标元素语义意图")

    p_bola = sub.add_parser("bola-fuzz", help="[L6.0 新增] 生成 3D BOLA/IDOR 有状态接口越权测试矩阵")
    p_bola.add_argument("--endpoint", default="/api/v1/orders/{order_id}", help="目标 REST 接口路径")

    p_swarm = sub.add_parser("swarm", help="运行 OWASP ASI:2026 & AST10 红蓝对抗自主进化博弈")
    p_swarm.add_argument("--rounds", type=int, default=6)

    sub.add_parser("eval", help="运行 3D 黄金数据集与 τ-bench pass^k (k=5) 自动化评测套件")

    p_tpl = sub.add_parser("templates", help="[v12.1 新增] 查看通用业务场景“骨·肉·尺”模板清单或模板详情")
    p_tpl.add_argument("--id", default="", help="指定模板 ID，如 SCEN-MASTER 或 SCEN-TPL-01")

    p_mcp = sub.add_parser("serve-mcp", help="启动双模 MCP Server (stdio 或 Streamable HTTP)")
    p_mcp.add_argument("--transport", choices=["stdio", "http"], default="stdio")
    p_mcp.add_argument("--host", default="127.0.0.1")
    p_mcp.add_argument("--port", type=int, default=8765)

    args = parser.parse_args()
    router = ProgressiveSkillRouter(REPO_ROOT)

    if args.cmd == "list":
        skills = router.list_all(stage=args.stage)
        print(f"=== Universal QA Skills (v12.1.0 L6.0) — 共 {len(skills)} 项原子技能 ===")
        for s in skills:
            print(f"[{s['index']:02d}] {s['id']:<24} ({s['tier']}/{s['stage']}) -> {s['title']}")
        return 0

    if args.cmd == "search":
        res = router.route(query=args.keyword, top_k=5)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "route":
        res = router.route(query=args.query, stage=args.stage, top_k=args.top_k)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "load":
        res = router.load_skill_sop(args.skill_id)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "data":
        res = generate_test_data_batch(data_type=args.data_type, count=args.count)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "sanitize":
        res = sanitize_sensitive_data(args.text)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "tia":
        res = run_hybrid_tia(REPO_ROOT, diff_target=args.diff)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "aria-heal":
        res = heal_ui_locator_via_aria(broken_selector=args.selector, target_intent=args.intent)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "bola-fuzz":
        res = generate_3d_bola_fuzz_matrix(resource_endpoint=args.endpoint)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "swarm":
        res = run_red_blue_adversarial_swarm(rounds=args.rounds)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "eval":
        eval_script = REPO_ROOT / "evals" / "run_evals.py"
        proc = subprocess.run([sys.executable, str(eval_script)], cwd=str(REPO_ROOT), check=False)
        return proc.returncode

    if args.cmd == "templates":
        res = router.list_scenario_templates(template_id=args.id)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "serve-mcp":
        if args.transport == "http":
            run_http_server(args.host, args.port)
        else:
            run_stdio_server()
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
