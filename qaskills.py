#!/usr/bin/env python3
"""
qaskills.py: Universal QA Skills 统一命令行交互与管理工具 (All-in-One CLI)
纯 Python 3.9+ 标准库，支持检索 40 个 QA 细分领域技能、运行质量门禁、启动 MCP Server 与执行 Eval 评测。

子命令:
  list        - 列出全部 40 个细分测试技能与依赖要求
  search      - 根据关键词搜索相关技能 (如 api, ui, perf, security, flaky)
  mcp         - 启动 QA MCP JSON-RPC 服务 (供 Cursor/Claude Code/Antigravity 接入)
  eval        - 运行技能输出质量自动化评测套件
  data        - 动态测试数据工厂 (生成合规手机号/身份证/姓名/时间戳)
  gate        - 检查指定目录的 signals 质量门禁阻断信号
"""
import os
import sys
import json
import argparse
from pathlib import Path

# Windows UTF-8 stdout 保护
if sys.platform == "win32":
    import io
    if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "buffer") and getattr(sys.stderr, "encoding", "").lower() != "utf-8":
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent
SKILLS_DIR = ROOT / "skills"

def cmd_list(args):
    reg_file = SKILLS_DIR / "REGISTRY.json"
    if not reg_file.exists():
        print("❌ 未找到 REGISTRY.json")
        return
    data = json.loads(reg_file.read_text(encoding="utf-8"))
    skills = data.get("skills", [])
    print(f"📦 Universal QA Skills 注册中心 (共 {len(skills)} 个技能):\n")
    print(f"{'技能名称':<25} | {'依赖要求':<18} | {'一句话能力描述'}")
    print("-" * 80)
    for s in sorted(skills, key=lambda x: x.get("name", "")):
        name = s.get("name", "")
        deps = s.get("runtime_dependencies") or "零依赖"
        desc = (s.get("description") or "").replace("\n", " ")[:40]
        print(f"{name:<25} | {str(deps):<18} | {desc}...")

def cmd_search(args):
    kw = args.keyword.lower()
    reg_file = SKILLS_DIR / "REGISTRY.json"
    data = json.loads(reg_file.read_text(encoding="utf-8"))
    skills = data.get("skills", [])
    matched = [s for s in skills if kw in s.get("name", "").lower() or kw in s.get("description", "").lower()]
    print(f"🔍 搜索 '{kw}' 匹配到 {len(matched)} 个 QA 技能:\n")
    for s in matched:
        name = s.get("name", "")
        print(f"▶ {name}")
        print(f"  描述: {s.get('description')}")
        print(f"  依赖: {s.get('runtime_dependencies') or '零依赖'}\n")

def cmd_data(args):
    from skills.tools.mcp_server import _gen_fake_data
    dtype = args.type or "phone"
    cnt = args.count
    res = _gen_fake_data(dtype, cnt)
    print(f"🎲 生成 {cnt} 条 [{dtype}] 测试数据:")
    for item in res:
        print(f"  {item}")

def cmd_eval(args):
    eval_script = ROOT / "evals" / "run_evals.py"
    if eval_script.exists():
        import subprocess
        res = subprocess.run([sys.executable, str(eval_script)], cwd=str(ROOT))
        sys.exit(res.returncode)

def cmd_mcp(args):
    mcp_script = SKILLS_DIR / "tools" / "mcp_server.py"
    if mcp_script.exists():
        import subprocess
        subprocess.run([sys.executable, str(mcp_script)] + sys.argv[2:])

def main():
    parser = argparse.ArgumentParser(description="Universal QA Skills 全能 CLI 工具")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    p_list = subparsers.add_parser("list", help="列出全部 40 个技能")
    p_search = subparsers.add_parser("search", help="搜索测试技能")
    p_search.add_argument("keyword", help="搜索关键词 (如 api, ui, security, gate)")

    p_data = subparsers.add_parser("data", help="动态生成测试数据")
    p_data.add_argument("--type", "-t", choices=["phone", "id_card", "name", "email", "uuid"], default="phone", help="数据类型")
    p_data.add_argument("--count", "-c", type=int, default=3, help="生成数量")

    p_eval = subparsers.add_parser("eval", help="运行自动化 Eval 评测套件")
    p_mcp = subparsers.add_parser("mcp", help="启动 QA MCP Server")

    p_tia = subparsers.add_parser("tia", help="精准测试分析 (Git Diff 受影响用例计算)")
    p_tia.add_argument("--diff", default="HEAD", help="Git 比较基准")
    p_tia.add_argument("--test-dir", default=".", help="测试目录")

    p_swarm = subparsers.add_parser("swarm", help="红蓝对抗自主进化测试")
    p_swarm.add_argument("--cases", "-c", help="基准用例 JSON")

    args = parser.parse_args()

    if args.command == "list":
        cmd_list(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "data":
        cmd_data(args)
    elif args.command == "eval":
        cmd_eval(args)
    elif args.command == "mcp":
        cmd_mcp(args)
    elif args.command == "tia":
        from skills.tools import tia_engine
        changes = tia_engine.get_git_diff_changes(args.diff)
        impacted = tia_engine.calculate_impacted_tests(changes, args.test_dir)
        print(f"🎯 精准测试分析 (TIA): 命中 {len(impacted)} 个关联用例:")
        for t in impacted:
            print(f"  ⚡ {t}")
    elif args.command == "swarm":
        from skills.tools import red_blue_swarm
        base_cases = [{"id": "TC-001", "title": "核心接口测试", "endpoint": "/api/v1/orders"}]
        if args.cases and Path(args.cases).exists():
            base_cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))
        attacks = []
        for c in base_cases:
            attacks.extend(red_blue_swarm.RedTeamAgent.mutate_case(c))
        res = red_blue_swarm.BlueTeamAgent.evaluate_and_harden(attacks)
        print(f"🏆 红蓝博弈完成: 产生 {len(attacks)} 个变异攻击载荷，生成 {len(res['hardened_cases'])} 条自愈加固防御用例")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
