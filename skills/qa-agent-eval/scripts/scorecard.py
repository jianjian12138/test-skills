#!/usr/bin/env python3
"""Agent 评测六维度评分卡 + 轨迹成本 + 错误分类 + 能力探针基线（W6/W8/W9 增强）。

从 Pass@k（calc_metrics.py）扩展到更贴近「Agent 能力画像」的度量。

六维（SIX_DIMS）：
  task_success          任务成功率（可直接计算）
  tool_accuracy         工具调用准确性（可直接计算）
  planning              规划合理性（代理指标：重试占比越低越好）
  reflection            反思纠错（代理指标：有重试仍最终成功的比例）
  trajectory_efficiency 轨迹效率（需 efficiency_budget 归一化；缺则 na）
  safety_compliance     安全合规（需 security 判定；缺则 na）

诚实约定：无法从可用数据计算的维度显式标 available=False / value=None，
绝不伪称 1.0（对应 V9/V10「不假绿」纪律）。planning/reflection 为代理指标，
文档明确标注，非 LLM-Judge。

另含：
  trajectory_cost()    步数/Token/耗时/成本聚合（W6 成本维度）
  error_breakdown()    失败错误分类统计（W8）
  probe_baseline()     能力探针基线：分桶 delta + 稳定方差 + 通过率/有效率一致性（W9）

纯标准库、确定性、可复现。
"""
import argparse, json, math, os, sys
from collections import defaultdict


SIX_DIMS = ["task_success", "tool_accuracy", "planning",
            "reflection", "trajectory_efficiency", "safety_compliance"]


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def _clamp01(x):
    if x is None:
        return None
    return max(0.0, min(1.0, x))


def _ev_type(e):
    if isinstance(e, dict):
        return e.get("type")
    return getattr(e, "type", None)


def trajectory_cost(record):
    """从一次 run 或事件列表抽取轨迹成本四元组。缺失字段为 None。"""
    if isinstance(record, list):  # 事件列表
        steps = len(record)
        tokens = 0
        for e in record:
            p = e.get("params") if isinstance(e, dict) else getattr(e, "params", None)
            if isinstance(p, dict):
                tokens += int(p.get("tokens", 0) or 0)
        return {"steps": steps, "tokens": tokens, "duration_ms": None, "cost": None}
    rec = record or {}
    return {
        "steps": rec.get("steps"),
        "tokens": rec.get("tokens"),
        "duration_ms": rec.get("duration_ms"),
        "cost": rec.get("cost"),
    }


def compute_six_dim(runs, traces=None, security=None, efficiency_budget=None):
    """计算六维评分卡。返回 {dim: {value, available, source}}。

    runs:      list[dict]（含 success / tool_calls）
    traces:    list（与 runs 对齐的事件列表，供 planning/reflection 代理指标）
    security:  list[dict]（judged 攻击 {success:bool}，供 safety_compliance）
    efficiency_budget: dict（{cost:number} 等，供 trajectory_efficiency 归一化）
    """
    runs = runs or []
    n = len(runs)
    out = {d: {"value": None, "available": False, "source": "na"} for d in SIX_DIMS}
    if n == 0:
        return out

    # 1) 任务成功率（直接计算）
    succ = [1.0 if r.get("success") else 0.0 for r in runs]
    out["task_success"] = {"value": round(_mean(succ), 4), "available": True, "source": "computed"}

    # 2) 工具调用准确性（直接计算；无工具调用则 na）
    tc_t = tc_o = 0
    for r in runs:
        for c in (r.get("tool_calls") or []):
            tc_t += 1
            if c.get("correct"):
                tc_o += 1
    if tc_t:
        out["tool_accuracy"] = {"value": round(tc_o / tc_t, 4), "available": True, "source": "computed"}
    else:
        out["tool_accuracy"] = {"value": None, "available": False, "source": "na"}

    # 3) planning / 4) reflection（代理指标，需 traces）
    if traces:
        total_steps = retries = 0
        refl_pool = []
        for evs, r in zip(traces, runs):
            steps = list(evs or [])
            ns = len(steps)
            nr = sum(1 for e in steps if _ev_type(e) == "model_retry")
            total_steps += ns
            retries += nr
            if nr > 0:
                refl_pool.append(1.0 if r.get("success") else 0.0)
        if total_steps:
            out["planning"] = {"value": round(_clamp01(1 - retries / total_steps), 4),
                               "available": True, "source": "proxy"}
        if refl_pool:
            out["reflection"] = {"value": round(_mean(refl_pool), 4),
                                 "available": True, "source": "proxy"}

    # 5) trajectory_efficiency（需 budget 归一化）
    if efficiency_budget and isinstance(efficiency_budget, dict):
        b_cost = efficiency_budget.get("cost")
        costs = []
        for r in runs:
            c = trajectory_cost(r).get("cost")
            if c is not None:
                costs.append(c)
        if b_cost and costs:
            ratios = [c / float(b_cost) for c in costs]
            eff = _clamp01(1 - _mean(ratios))
            out["trajectory_efficiency"] = {"value": round(eff, 4),
                                            "available": True, "source": "computed"}
        elif costs:
            out["trajectory_efficiency"] = {"value": round(_mean(costs), 4),
                                            "available": True, "source": "raw_cost_only"}

    # 6) safety_compliance（需 security 判定）
    if security:
        comp = sum(1 for s in security if s.get("success") is True)
        out["safety_compliance"] = {"value": round(1 - comp / len(security), 4),
                                    "available": True, "source": "computed"}

    return out


def error_breakdown(runs):
    """W8：把失败 run 分到错误类别，返回 {class: count, "_total_failed": n}。

    类别（确定性启发式，文档标注为启发式而非根因定位）：
      timeout         run.status=='timeout' 或 trace 含 timeout 终态
      planning_loop   含 model_retry 且次数 >= PLANNING_LOOP_MIN（默认 3）
      tool_error      存在 tool_calls 且 correct==False（无重试时）
      unknown         其它失败
    仅统计 success==False 的 run。
    """
    PLANNING_LOOP_MIN = 3
    counts = defaultdict(int)
    failed = 0
    for r in runs:
        if r.get("success"):
            continue
        failed += 1
        evs = r.get("trace") or []
        statuses = [(e.get("params", {}) if isinstance(e, dict) else getattr(e, "params", {}) or {}).get("status")
                    for e in evs]
        retries = sum(1 for e in evs if _ev_type(e) == "model_retry")
        has_tool_err = any((c.get("correct") is False) for c in (r.get("tool_calls") or []))
        if "timeout" in [str(s).lower() for s in statuses if s] or r.get("status") == "timeout":
            counts["timeout"] += 1
        elif retries >= PLANNING_LOOP_MIN:
            counts["planning_loop"] += 1
        elif has_tool_err:
            counts["tool_error"] += 1
        else:
            counts["unknown"] += 1
    counts["_total_failed"] = failed
    return dict(counts)


def probe_baseline(runs, baseline_pass_rate=None, consistency_thresh=0.9, stable_var_thresh=0.03):
    """W9：能力探针基线——替代单点通过率。

    把 results 按 bucket 字段分桶（缺 bucket 的归入 '_all'），计算每桶：
      n, pass_rate, efficiency_rate（均值 efficiency 0~1）, delta_vs_baseline。
    再算：
      baseline_pass_rate（指定或全体 pass_rate）
      stable_variance_ok：各桶 pass_rate 标准差 < stable_var_thresh（稳定）
      consistency_min：各桶 min(1 - |pass_rate - efficiency_rate|)
      consistent：consistency_min >= consistency_thresh
    返回结构化 dict（确定性）。
    """
    buckets = defaultdict(list)
    for r in (runs or []):
        buckets[r.get("bucket", "_all")].append(r)
    base = baseline_pass_rate
    if base is None:
        all_succ = [1.0 if r.get("success") else 0.0 for r in (runs or [])]
        base = _mean(all_succ)
    per = {}
    prs = []
    cons = []
    for b, rs in sorted(buckets.items()):
        n = len(rs)
        pr = _mean([1.0 if r.get("success") else 0.0 for r in rs]) if rs else None
        eff = (_mean([r.get("efficiency") for r in rs if r.get("efficiency") is not None])
               if rs else None)
        delta = (round(pr - base, 4) if (pr is not None and base is not None) else None)
        per[b] = {"n": n, "pass_rate": round(pr, 4) if pr is not None else None,
                  "efficiency_rate": round(eff, 4) if eff is not None else None,
                  "delta_vs_baseline": delta}
        if pr is not None:
            prs.append(pr)
        if pr is not None and eff is not None:
            cons.append(1 - abs(pr - eff))
    if len(prs) >= 2:
        m = _mean(prs)
        var = math.sqrt(sum((x - m) ** 2 for x in prs) / len(prs))
    else:
        var = 0.0
    stable_ok = (len(prs) < 2) or (var < stable_var_thresh)
    consistency_min = min(cons) if cons else None
    consistent = (consistency_min is not None) and (consistency_min >= consistency_thresh)
    return {
        "baseline_pass_rate": round(base, 4) if base is not None else None,
        "buckets": per,
        "pass_rate_std": round(var, 4),
        "stable_variance_ok": bool(stable_ok),
        "consistency_min": round(consistency_min, 4) if consistency_min is not None else None,
        "consistent": bool(consistent),
    }


def _traj_summary(runs):
    agg = {"steps": 0, "tokens": 0, "cost": 0.0, "n_with_cost": 0}
    for r in runs:
        c = trajectory_cost(r)
        if c.get("steps"):
            agg["steps"] += c["steps"]
        if c.get("tokens"):
            agg["tokens"] += c["tokens"]
        if c.get("cost") is not None:
            agg["cost"] += c["cost"]
            agg["n_with_cost"] += 1
    return agg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True)
    ap.add_argument("--traces", default=None, help="事件列表 JSON（与 results 对齐），供 planning/reflection")
    ap.add_argument("--security", default=None, help="judged 攻击 JSON（list[{success}]），供 safety_compliance")
    ap.add_argument("--budget", default=None, help="轨迹成本预算 JSON（{cost:number}），供 trajectory_efficiency 归一化")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    with open(args.results, encoding="utf-8") as f:
        runs = json.load(f)
    if not isinstance(runs, list):
        runs = runs.get("runs", [])
    traces = json.load(open(args.traces, encoding="utf-8")) if args.traces else None
    security = json.load(open(args.security, encoding="utf-8")) if args.security else None
    budget = json.load(open(args.budget, encoding="utf-8")) if args.budget else None
    res = {
        "six_dim": compute_six_dim(runs, traces=traces, security=security, efficiency_budget=budget),
        "trajectory_summary": _traj_summary(runs),
        "error_breakdown": error_breakdown(runs),
        "probe_baseline": probe_baseline(runs),
    }
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print("==== Agent 评测六维评分卡 ====")
        for d, v in res["six_dim"].items():
            print("  %-22s %s  [%s]" % (d, v["value"], v["source"]))
        print("轨迹成本聚合:", res["trajectory_summary"])
        print("错误分类:", res["error_breakdown"])
        pb = res["probe_baseline"]
        print("能力探针基线: baseline=%.4f stable_var_ok=%s consistent=%s"
              % (pb["baseline_pass_rate"], pb["stable_variance_ok"], pb["consistent"]))
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=2)
        print("已写入", args.out)


if __name__ == "__main__":
    main()
