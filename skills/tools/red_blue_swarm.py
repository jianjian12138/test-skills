#!/usr/bin/env python3
"""
red_blue_swarm.py: 红蓝对抗自主进化测试引擎 (Self-Evolving Red-Blue Swarm)
红队 Agent 实施参数变异、越权嗅探与混沌异常注入；
蓝队 Agent 实施防御断言检验、缺陷自动提炼与防御用例自愈生成。

零外部依赖，纯 Python 3.9+ 标准库实现。
"""
import os
import sys
import json
import random
import copy
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple

if sys.platform == "win32":
    import io
    if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "buffer") and getattr(sys.stderr, "encoding", "").lower() != "utf-8":
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

class RedTeamAgent:
    """红队攻击智能体：生成变异、越权与混沌攻击 Payload"""
    ATTACK_PAYLOADS = {
        "sql_injection": ["' OR '1'='1", "1; DROP TABLE users--", "' UNION SELECT null, null--"],
        "xss": ["<script>alert(1)</script>", "<img src=x onerror=alert(1)>"],
        "overflow": ["A" * 10000, "99999999999999999999999999"],
        "auth_bypass": ["Bearer null", "Basic YWRtaW46YWRtaW4=", "Bearer invalid_expired_jwt"],
        "type_flip": [None, True, {}, []]
    }

    @classmethod
    def mutate_case(cls, original_case: dict) -> List[dict]:
        mutated_cases = []
        c_title = original_case.get("title", "未命名用例")
        endpoint = original_case.get("endpoint", "/api/v1/resource")
        method = original_case.get("method", "POST")

        # 1. SQL 注入变异
        for p in cls.ATTACK_PAYLOADS["sql_injection"][:1]:
            mc = copy.deepcopy(original_case)
            mc["id"] = f"RED-SQL-{random.randint(100,999)}"
            mc["title"] = f"【红队SQL注入对抗】{c_title}"
            mc["attack_vector"] = "SQL_INJECTION"
            mc["test_data"] = {"payload": p, "desc": "SQL注入探测载荷"}
            mc["expected_result"] = "严格参数化校验，拒绝非法输入 (返回 HTTP 400/422，禁止报错 500)"
            mutated_cases.append(mc)

        # 2. XSS 跨站脚本变异
        for p in cls.ATTACK_PAYLOADS["xss"][:1]:
            mc = copy.deepcopy(original_case)
            mc["id"] = f"RED-XSS-{random.randint(100,999)}"
            mc["title"] = f"【红队XSS注入对抗】{c_title}"
            mc["attack_vector"] = "XSS"
            mc["test_data"] = {"payload": p}
            mc["expected_result"] = "输入自动 HTML 转义或过滤，杜绝反射型跨站脚本"
            mutated_cases.append(mc)

        # 3. 鉴权越权嗅探
        mc = copy.deepcopy(original_case)
        mc["id"] = f"RED-BOLA-{random.randint(100,999)}"
        mc["title"] = f"【红队越权访问对抗】{c_title}"
        mc["attack_vector"] = "BOLA_AUTH_BYPASS"
        mc["test_data"] = {"headers": {"Authorization": "Bearer invalid_expired_jwt"}}
        mc["expected_result"] = "返回 HTTP 401/403 明确拒绝未授权调用"
        mutated_cases.append(mc)

        return mutated_cases

class BlueTeamAgent:
    """蓝队防御智能体：评估防御有效性并自主生成防御断言与修复补丁"""
    @staticmethod
    def evaluate_and_harden(attack_cases: List[dict]) -> Dict[str, Any]:
        hardened_cases = []
        patch_suggestions = []

        for ac in attack_cases:
            vector = ac.get("attack_vector", "GENERIC")
            hc = copy.deepcopy(ac)
            hc["id"] = f"BLUE-DEF-{ac.get('id', '001')}"
            hc["defense_assertions"] = [
                "断言 HTTP 状态码不等于 500 (杜绝未捕获系统异常)",
                "断言响应头包含 X-Content-Type-Options: nosniff",
                "断言敏感堆栈信息不外泄"
            ]

            if vector == "SQL_INJECTION":
                patch_suggestions.append({
                    "target": ac.get("endpoint"),
                    "vuln": "SQL注入风险",
                    "suggestion": "强制采用 ORM 参数化查询或预编译语句，严禁字符串拼接 SQL"
                })
            elif vector == "BOLA_AUTH_BYPASS":
                patch_suggestions.append({
                    "target": ac.get("endpoint"),
                    "vuln": "越权与未授权访问",
                    "suggestion": "在 API 网关与路由层增加统一 @assert_project_access 装饰器进行对象级鉴权"
                })

            hardened_cases.append(hc)

        return {
            "total_attacks": len(attack_cases),
            "hardened_cases": hardened_cases,
            "patch_suggestions": patch_suggestions
        }

def main():
    parser = argparse.ArgumentParser(description="Red-Blue Swarm - 红蓝对抗自主进化测试引擎")
    parser.add_argument("--cases", "-c", help="基准测试用例 JSON 文件路径")
    parser.add_argument("--output", "-o", help="输出红蓝博弈进化报告 JSON")
    args = parser.parse_args()

    # 样例输入
    base_cases = [
        {"id": "TC-001", "title": "创建订单接口", "endpoint": "/api/v1/orders", "method": "POST"}
    ]
    if args.cases and Path(args.cases).exists():
        base_cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))

    print("=" * 60)
    print("  ⚔️ Red-Blue QA Swarm - 红蓝对抗自主进化测试")
    print("=" * 60)

    print(f"\n🔴 红队 Agent 启动: 正在对 {len(base_cases)} 条基准用例实施变异与攻击注入...")
    all_attacks = []
    for c in base_cases:
        attacks = RedTeamAgent.mutate_case(c)
        all_attacks.extend(attacks)
        for a in attacks:
            print(f"  ⚡ [{a['id']}] {a['title']} (载荷类型: {a['attack_vector']})")

    print(f"\n🔵 蓝队 Agent 启动: 正在分析 {len(all_attacks)} 处攻击向量并加固防御断言...")
    result = BlueTeamAgent.evaluate_and_harden(all_attacks)
    for p in result["patch_suggestions"]:
        print(f"  🛡️ [补丁建议] {p['target']}: {p['suggestion']}")

    print("\n" + "=" * 60)
    print(f"  🏆 博弈完成: 生成 {len(all_attacks)} 个红队对抗变异体 | 沉淀 {len(result['hardened_cases'])} 条防御加固用例")
    print("=" * 60)

    if args.output:
        Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"📁 进化报告已保存至: {args.output}")

if __name__ == "__main__":
    main()
