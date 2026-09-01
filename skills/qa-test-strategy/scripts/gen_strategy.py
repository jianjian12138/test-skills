#!/usr/bin/env python3
"""Generate a test strategy / plan (Markdown) from a strategy JSON.

Usage:
    python scripts/gen_strategy.py --strategy strategy.json --out test_strategy.md
"""
import argparse
import json
import sys

TYPE_POINTS = {
    "ui": "关键路径自动化 + 兼容性矩阵（浏览器/分辨率）",
    "api": "单接口 + 多接口串联 + 异常/边界 + 数据双校验",
    "perf": "负载/压力/疲劳/尖峰，定 SLA 再看拐点",
    "security": "OWASP 核查 + DAST/SAST/依赖/密钥扫描",
}


def render(d: dict) -> str:
    lines = []
    lines.append(f"# 测试策略 / 计划：{d.get('project', '-')} {d.get('version', '')}\n")

    lines.append("## 1. 概述\n")
    lines.append(f"- 项目：{d.get('project', '-')}")
    lines.append(f"- 版本：{d.get('version', '-')}")
    lines.append(f"- 测试范围：{d.get('scope', '-')}")
    lines.append(f"- 计划周期：{d.get('schedule', '-')}")
    lines.append("")

    lines.append("## 2. 测试目标\n")
    for o in d.get("objectives", []):
        lines.append(f"- {o}")
    if not d.get("objectives"):
        lines.append("- （待定）")
    lines.append("")

    lines.append("## 3. 测试类型与策略\n")
    for t in d.get("types", []):
        lines.append(f"- **{t.upper()}**：{TYPE_POINTS.get(t, '按类型设计')}")
    lines.append("")

    lines.append("## 4. 准入 / 准出准则\n")
    lines.append("**准入（Entry）**：")
    for e in d.get("entry", []):
        lines.append(f"- {e}")
    lines.append("\n**准出（Exit）**：")
    for e in d.get("exit", []):
        lines.append(f"- {e}")
    lines.append("")

    lines.append("## 5. 风险与应对\n")
    for r in d.get("risks", []):
        lines.append(f"- ⚠️ {r}")
    if not d.get("risks"):
        lines.append("- 暂无")
    lines.append("")

    lines.append("## 6. 衔接\n")
    lines.append("- 策略落地后进入 `qa-req-spec` 需求结构化 → `qa-test-analysis` 测试点 → 各专项技能执行。")
    lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strategy", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    try:
        with open(args.strategy, "r", encoding="utf-8") as f:
            d = json.load(f)
    except Exception as e:
        print(f"[ERROR] 读取 strategy 失败: {e}", file=sys.stderr)
        return 2
    md = render(d)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"[OK] 已生成测试策略: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
