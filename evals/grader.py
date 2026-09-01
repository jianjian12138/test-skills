#!/usr/bin/env python3
"""
grader.py: QA Skills 自动化打分与质量评估器 (Deterministic & Rule-based Grader)
对测试需求拆解、测试用例集、安全分析、API 契约等输出进行多维度量化评分 (0-100分)。
"""
import json
import re
from typing import Dict, Any, List, Tuple

class QASkillGrader:
    @staticmethod
    def grade_test_cases(cases: List[Dict[str, Any]]) -> Tuple[float, List[str]]:
        """评测测试用例集质量"""
        if not cases or not isinstance(cases, list):
            return 0.0, ["用例集为空或非列表格式"]

        score = 100.0
        deductions = []

        # 1. 结构完整性 (40分)
        required_fields = ["id", "title", "priority", "steps", "expected_result"]
        missing_fields_cnt = 0
        for i, c in enumerate(cases):
            for f in required_fields:
                if f not in c or not c[f]:
                    missing_fields_cnt += 1
        if missing_fields_cnt > 0:
            pen = min(30.0, missing_fields_cnt * 3.0)
            score -= pen
            deductions.append(f"缺少必填字段 ({missing_fields_cnt}处，扣{pen:.1f}分)")

        # 2. 优先级分布合理性 (20分)
        p0_cnt = sum(1 for c in cases if c.get("priority") == "P0")
        if p0_cnt == 0:
            score -= 10.0
            deductions.append("缺少 P0 核心阻塞用例 (扣10分)")
        elif p0_cnt == len(cases):
            score -= 10.0
            deductions.append("全部用例均为 P0，优先级划分缺乏梯度 (扣10分)")

        # 3. 边界与逆向测试覆盖 (20分)
        negative_keywords = ["异常", "错误", "缺少", "越权", "超时", "空", "非法", "失败", "边界", "超出"]
        neg_cases = sum(1 for c in cases if any(k in c.get("title", "") or k in str(c.get("steps", "")) for k in negative_keywords))
        if neg_cases == 0:
            score -= 15.0
            deductions.append("缺少异常分支与边界值测试用例 (扣15分)")

        # 4. 步骤可操作性 (20分)
        vague_steps = 0
        for c in cases:
            steps = c.get("steps") or []
            if isinstance(steps, list) and len(steps) < 2:
                vague_steps += 1
        if vague_steps > 0:
            pen = min(15.0, vague_steps * 2.0)
            score -= pen
            deductions.append(f"存在过于简略的测试步骤 ({vague_steps}条，扣{pen:.1f}分)")

        final_score = max(0.0, min(100.0, score))
        return final_score, deductions

    @staticmethod
    def grade_security_scan(report: Dict[str, Any]) -> Tuple[float, List[str]]:
        """评测安全扫描报告质量"""
        score = 100.0
        deductions = []
        if not report or not isinstance(report, dict):
            return 0.0, ["报告为空"]

        findings = report.get("findings", [])
        if not findings:
            return 90.0, ["未发现漏洞 (正常扫描)"]

        for f in findings:
            if not f.get("severity") or not f.get("remediation"):
                score -= 10.0
                deductions.append("漏洞条目缺少严重级别或修复建议")
                break

        return max(0.0, score), deductions
