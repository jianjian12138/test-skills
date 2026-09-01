#!/usr/bin/env python3
"""
run_evals.py: Universal QA Skills 自动化质量评测套件
批量运行基准评测数据集，验证各技能生成产物的结构合规率与质量得分 (CI 阻断门禁)。
"""
import os
import sys
import json
from pathlib import Path

# Windows UTF-8 stdout 保护
if sys.platform == "win32":
    import io
    if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "buffer") and getattr(sys.stderr, "encoding", "").lower() != "utf-8":
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from grader import QASkillGrader

# Golden Benchmark Datasets
GOLDEN_SUITES = [
    {
        "skill": "qa-test-case-gen",
        "name": "用户认证与支付用例集",
        "type": "cases",
        "data": [
            {
                "id": "TC-001",
                "title": "【正常】用户名密码正确登录成功",
                "priority": "P0",
                "steps": ["输入有效账号密码", "点击登录按钮", "验证跳转首页并携带 Auth Token"],
                "expected_result": "登录成功，状态码 200"
            },
            {
                "id": "TC-002",
                "title": "【异常】密码错误触发登录失败与锁定计数",
                "priority": "P1",
                "steps": ["输入错误密码", "点击登录按钮", "检查失败提示并验证重试计数加1"],
                "expected_result": "提示账号或密码错误，不泄露具体字段"
            },
            {
                "id": "TC-003",
                "title": "【边界】未授权直接访问订单结算接口",
                "priority": "P0",
                "steps": ["未携带 Authorization 请求头发送 POST /api/v1/orders", "检查响应拦截"],
                "expected_result": "返回 HTTP 401 Unauthorized"
            }
        ]
    },
    {
        "skill": "qa-agent-security",
        "name": "Prompt 注入与越狱测试报告",
        "type": "security",
        "data": {
            "findings": [
                {
                    "id": "SEC-01",
                    "title": "检测到直接系统提示词泄露隐患",
                    "severity": "HIGH",
                    "remediation": "增加 Prompt Guard 前置拦截与 Output Sanitizer"
                }
            ]
        }
    }
]

def run_evaluation(min_pass_score: float = 85.0) -> bool:
    print("=" * 60)
    print("  🧪 Universal QA Skills - 自动化 Eval 评测套件")
    print("=" * 60)

    total_score = 0.0
    all_passed = True
    results = []

    for suite in GOLDEN_SUITES:
        s_name = suite["name"]
        skill = suite["skill"]
        s_type = suite["type"]

        if s_type == "cases":
            score, deductions = QASkillGrader.grade_test_cases(suite["data"])
        elif s_type == "security":
            score, deductions = QASkillGrader.grade_security_scan(suite["data"])
        else:
            score, deductions = 100.0, []

        passed = score >= min_pass_score
        if not passed:
            all_passed = False

        status_emoji = "✅ PASS" if passed else "❌ FAIL"
        print(f"\n▶ [{skill}] {s_name}")
        print(f"  评分: {score:.1f} / 100.0 [{status_emoji}]")
        if deductions:
            for d in deductions:
                print(f"  ⚠️ 扣分项: {d}")

        results.append({
            "skill": skill,
            "name": s_name,
            "score": score,
            "passed": passed,
            "deductions": deductions
        })
        total_score += score

    avg_score = total_score / len(GOLDEN_SUITES)
    print("\n" + "=" * 60)
    print(f"  📊 评测汇总: 平均得分 {avg_score:.1f} / 100.0 | 最低门禁 {min_pass_score} 分")
    print(f"  🏁 门禁结果: {'🎉 全部通过 (PASSED)' if all_passed else '⛔ 未达标 (BLOCKED)'}")
    print("=" * 60)

    return all_passed

if __name__ == "__main__":
    passed = run_evaluation(min_pass_score=85.0)
    sys.exit(0 if passed else 1)
