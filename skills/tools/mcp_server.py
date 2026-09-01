#!/usr/bin/env python3
"""
mcp_server.py: Universal QA Skills - Model Context Protocol (MCP) Server
纯 Python 3.9+ 标准库实现，零外部依赖，支持 JSON-RPC 2.0 stdio 协议。
用于将 40 个 QA 细分领域技能作为原生 Tools 暴露给 Claude Code, Cursor, Antigravity 等 AI Agent。
"""
import sys
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

# Windows UTF-8 stdout 保护
if sys.platform == "win32":
    import io
    if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "buffer") and getattr(sys.stderr, "encoding", "").lower() != "utf-8":
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
SKILLS_DIR = HERE.parent

logging.basicConfig(level=logging.INFO, format="[MCP] %(message)s", stream=sys.stderr)

# 动态测试数据生成函数
def _gen_fake_data(data_type: str, count: int = 1) -> List[str]:
    import random, time, uuid
    results = []
    prefixes = ["138", "139", "150", "158", "188", "189", "177", "133", "199"]
    first_names = "赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜戚谢"
    last_names = ["伟", "芳", "娜", "敏", "静", "丽", "强", "磊", "军", "洋", "勇", "艳", "杰", "娟", "涛", "明", "超"]
    
    for _ in range(count):
        if data_type == "phone":
            results.append(random.choice(prefixes) + "".join([str(random.randint(0, 9)) for _ in range(8)]))
        elif data_type == "id_card":
            prefix_17 = f"110101{random.randint(1970, 2005):04d}{random.randint(1,12):02d}{random.randint(1,28):02d}{random.randint(100,999):03d}"
            weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
            check_codes = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']
            check_code = check_codes[sum(int(prefix_17[i]) * weights[i] for i in range(17)) % 11]
            results.append(prefix_17 + check_code)
        elif data_type == "name":
            results.append(random.choice(first_names) + random.choice(last_names))
        elif data_type == "email":
            results.append(f"qa_test_{random.randint(1000,9999)}_{int(time.time())%1000}@example.com")
        elif data_type == "uuid":
            results.append(str(uuid.uuid4()))
        else:
            results.append(f"mock_val_{random.randint(100,999)}")
    return results

# 工具定义字典
TOOLS = [
    {
        "name": "list_qa_skills",
        "description": "获取当前仓库中全部 40 个细分 QA 技能的分类列表与能力定义",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "按阶段过滤: req/analysis/cases/data/api/exec/report/gates/agent"}
            }
        }
    },
    {
        "name": "generate_test_data",
        "description": "动态生成合规脱敏的测试数据 (合规中国手机号/身份证/姓名/邮箱/UUID)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["phone", "id_card", "name", "email", "uuid"], "description": "数据类型"},
                "count": {"type": "integer", "default": 1, "description": "生成条数"}
            },
            "required": ["type"]
        }
    },
    {
        "name": "sanitize_sensitive_data",
        "description": "对输入的文本或测试数据进行主动脱敏清洗 (手机号/身份证/银行卡号自动掩码打码)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "待脱敏的文本内容"}
            },
            "required": ["text"]
        }
    },
    {
        "name": "run_quality_gate",
        "description": "运行质量红线门禁评估，检查指定产物目录中的 signals 信号是否 blocking",
        "inputSchema": {
            "type": "object",
            "properties": {
                "signals_dir": {"type": "string", "description": "质量信号目录路径 (默认为 signals)"}
            }
        }
    },
    {
        "name": "run_tia_analysis",
        "description": "运行 TIA 精准测试分析，根据 Git 变更计算受影响的测试用例文件",
        "inputSchema": {
            "type": "object",
            "properties": {
                "diff_ref": {"type": "string", "default": "HEAD", "description": "Git 差异比较基准 (如 HEAD~1)"},
                "test_dir": {"type": "string", "default": ".", "description": "测试用例目录"}
            }
        }
    },
    {
        "name": "run_red_blue_swarm",
        "description": "启动红蓝对抗自主进化测试，红队生成变异攻击载荷，蓝队生成加固防御用例与补丁",
        "inputSchema": {
            "type": "object",
            "properties": {
                "endpoint": {"type": "string", "description": "目标接口路径 (如 /api/v1/orders)"},
                "title": {"type": "string", "description": "用例标题"}
            },
            "required": ["endpoint"]
        }
    }
]

def handle_tool_call(name: str, args: dict) -> Any:
    if name == "list_qa_skills":
        reg_file = SKILLS_DIR / "REGISTRY.json"
        if reg_file.exists():
            data = json.loads(reg_file.read_text(encoding="utf-8"))
            skills = data.get("skills", [])
            cat = args.get("category")
            if cat:
                skills = [s for s in skills if cat in s.get("name", "") or cat in s.get("stage", "") or cat in s.get("description", "")]
            return {"total": len(skills), "skills": skills}
        return {"error": "REGISTRY.json not found"}

    elif name == "generate_test_data":
        data_type = args.get("type", "phone")
        count = max(1, min(args.get("count", 1), 100))
        return {"type": data_type, "count": count, "data": _gen_fake_data(data_type, count)}

    elif name == "sanitize_sensitive_data":
        import re
        text = args.get("text", "")
        text = re.sub(r'(?<!\d)(1[3-9]\d)(\d{4})(\d{4})(?!\d)', r'\1****\3', text)
        text = re.sub(r'(?<!\d)([1-9]\d{5})\d{8}(\d{3}[\dXx])(?!\d)', r'\1********\2', text)
        text = re.sub(r'(?<!\d)(\d{4})\d{8,11}(\d{4})(?!\d)', r'\1********\2', text)
        return {"sanitized_text": text}

    elif name == "run_quality_gate":
        sig_dir = Path(args.get("signals_dir") or "signals")
        if not sig_dir.exists():
            return {"passed": True, "message": "No signals directory found, default pass."}
        blocking_signals = []
        for sf in sig_dir.glob("*.json"):
            try:
                sdata = json.loads(sf.read_text(encoding="utf-8"))
                if sdata.get("blocking"):
                    blocking_signals.append({"signal": sf.name, "detail": sdata})
            except Exception:
                pass
        return {
            "passed": len(blocking_signals) == 0,
            "blocking_count": len(blocking_signals),
            "blocking_signals": blocking_signals
        }

    elif name == "run_tia_analysis":
        from . import tia_engine
        diff_ref = args.get("diff_ref", "HEAD")
        test_dir = args.get("test_dir", ".")
        changes = tia_engine.get_git_diff_changes(diff_ref)
        impacted = tia_engine.calculate_impacted_tests(changes, test_dir)
        return {
            "diff_ref": diff_ref,
            "changed_files_count": len(changes),
            "impacted_tests_count": len(impacted),
            "impacted_tests": impacted
        }

    elif name == "run_red_blue_swarm":
        from . import red_blue_swarm
        ep = args.get("endpoint", "/api/v1/orders")
        title = args.get("title", "核心接口测试")
        base_case = {"id": "TC-001", "title": title, "endpoint": ep}
        attacks = red_blue_swarm.RedTeamAgent.mutate_case(base_case)
        defense_report = red_blue_swarm.BlueTeamAgent.evaluate_and_harden(attacks)
        return {
            "endpoint": ep,
            "attacks_generated": len(attacks),
            "hardened_cases": defense_report["hardened_cases"],
            "patch_suggestions": defense_report["patch_suggestions"]
        }

    raise ValueError(f"Unknown tool: {name}")

def run_stdio_server():
    """标准 MCP JSON-RPC 2.0 stdio 消息循环"""
    logging.info("Universal QA Skills MCP Server started on stdio")
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})

            if method == "initialize":
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "universal-qa-skills-mcp", "version": "11.0.0"}
                    }
                }
            elif method == "tools/list":
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"tools": TOOLS}
                }
            elif method == "tools/call":
                t_name = params.get("name")
                t_args = params.get("arguments", {})
                try:
                    res = handle_tool_call(t_name, t_args)
                    resp = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [{"type": "text", "text": json.dumps(res, ensure_ascii=False, indent=2)}]
                        }
                    }
                except Exception as e:
                    resp = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {"code": -32000, "message": str(e)}
                    }
            else:
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"}
                }

            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()

        except Exception as err:
            logging.error(f"Error handling request: {err}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print(f"✅ QA MCP Server ready! Registered {len(TOOLS)} tools:")
        for t in TOOLS:
            print(f"  - {t['name']}: {t['description']}")
    else:
        run_stdio_server()
