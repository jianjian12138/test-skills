#!/usr/bin/env python3
"""qa-orchestrator: 独立路由 Agent 测试类技能（qa-agent-eval / qa-agent-security）。

不混入 8 阶段产品生命周期编排；通过 stages.json 的 ``agent_testing`` 维度声明接入
（S-02 设计权衡定稿：既可路由又不污染 8 阶段编排，保持"独立类目"语义）。

用法:
    python route_agent.py --task "评测 agent 成功率" [--json]
    python route_agent.py --task "红队攻击 asr" --auto

--json 输出统一结构化：{status, schema_version, skill, reason, alternates}
（与 route_next.py 的 --json 同构，供多 agent 出口标准化消费，R-26）。
"""
import argparse
import json
import os
import sys

import _stages

# 注意：_stages.load_stages() 仅返回 stages 列表；agent_testing 维度是 stages.json 的
# 顶层字段，需读整份文档（S-02）。
with open(_stages.STAGES_FILE, "r", encoding="utf-8") as _f:
    STAGES = json.load(_f)
SCHEMA_VERSION = "1.0"


def skills_root():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(os.path.dirname(here))


def agent_dimension():
    return STAGES.get("agent_testing", {}).get("skills", {})


def route(task):
    """依据任务描述关键词路由到合适的 Agent 测试技能。

    返回统一结构化 dict；status ∈ {ok, ambiguous, blocked}。
    """
    dim = agent_dimension()
    if not dim:
        return {"status": "blocked", "schema_version": SCHEMA_VERSION,
                "skill": None, "reason": "stages.json 未定义 agent_testing 维度",
                "alternates": []}
    text = (task or "").lower()
    scores = {}
    for skill, kws in dim.items():
        hit = [k for k in kws if k.lower() in text]
        if hit:
            scores[skill] = hit
    if len(scores) == 1:
        skill = list(scores)[0]
        return {"status": "ok", "schema_version": SCHEMA_VERSION, "skill": skill,
                "reason": "命中关键词: " + ", ".join(scores[skill]),
                "alternates": [s for s in dim if s != skill]}
    if len(scores) > 1:
        # 命中数多者优先；并列按维度声明顺序
        best = max(scores, key=lambda s: (len(scores[s]), list(dim).index(s)))
        return {"status": "ok", "schema_version": SCHEMA_VERSION, "skill": best,
                "reason": "多维度命中，选命中最多: " + ", ".join(scores[best]),
                "alternates": [s for s in dim if s != best]}
    return {"status": "ambiguous", "schema_version": SCHEMA_VERSION, "skill": None,
            "reason": "未命中任何 agent_testing 关键词", "alternates": list(dim)}


def main():
    ap = argparse.ArgumentParser(description="Agent 测试类技能路由（独立类目）")
    ap.add_argument("--task", required=True, help="任务描述（自然语言）")
    ap.add_argument("--auto", action="store_true", help="只打印技能名（供代理直接调用）")
    ap.add_argument("--json", action="store_true", help="结构化 JSON 输出")
    args = ap.parse_args()
    res = route(args.task)
    if args.auto:
        print(res["skill"] or "")
        return 0
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(f"[route_agent] status={res['status']} skill={res['skill']} reason={res['reason']}")
        print(f"  alternates={res['alternates']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
