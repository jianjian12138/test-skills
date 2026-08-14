#!/usr/bin/env python3
"""从 results.jsonl / results.json 计算 Agent 评测指标。

支持: Pass@1, Pass^k(逐任务), Pass@k(无偏), 工具调用准确率, 五维度均值。

======================================================================
Pass^k 与 Pass@k 的语义差异（两者方向相反，切勿混用）
======================================================================
设某任务采样 n 次，其中 c 次成功，点估计 p = c / n。

* Pass^k（pass_hat_k，"可靠性 / 一致性"指标）
    含义：同一任务独立采样 n 次、其中 c 次成功，问"不放回抽 k 次**全部成功**"的概率。
    算法（tau-bench 口径，无放回）：逐任务算 **C(c, k) / C(n, k)**，再对所有任务取平均。
        —— 即"从 n 次采样中不放回抽取 k 次，每次都成功"的概率；n<k 或 c<k 时为 0。
    严禁写成"先对每任务算 (c/n)**k 再平均"（那是 i.i.d. 有放回近似，会在小样本 /
    部分成功区**系统性高估**可靠性，已降为 pass_hat_k_iid_mc_legacy 仅供对照）。
    也严禁写成"先把所有任务的 p 平均，再对均值 ^k"（Jensen 不等式，均值的幂 != 幂的均值）。
    k 越大数值越低；用来回答"这个 Agent 稳不稳，能不能每次都做对"。
    出处：tau-bench 的 pass^k 可靠性口径（C(c,k)/C(n,k)）。

* Pass@k（pass_at_k，"能力上限 / 重试兜底"指标）
    含义：同一任务独立跑 k 次，**至少一次成功**的概率。
    算法（无偏估计，Codex/HumanEval 口径）：
        pass@k = 1 - C(n-c, k) / C(n, k)      （要求 n >= k）
    k 越大数值越高；用来回答"允许重试 k 次的话能不能兜住"。
    注意不要用 1-(1-p)**k 这个 Monte-Carlo 近似替代无偏估计——
    小样本下它是有偏的（本脚本仅把它作为 *_mc_legacy 字段保留对照）。

一句话：Pass^k 往下走（越严格越低），Pass@k 往上走（越多重试越高）。
======================================================================

输入数据结构（向后兼容，未变更）：
    每行 / 每个元素是一次 run：
    {"task_id": str, "success": bool,
     "tool_calls": [{"name": str, "correct": bool}, ...],
     "dims": {"task_completion": 0~1, ...}, "trace": str}
    同一 task_id 的多条 run 会被聚合成 (n 次采样, c 次成功)。
"""
import argparse, json, math, os, statistics, sys
from collections import defaultdict
from datetime import datetime

DIMS = ["task_completion", "tool_use", "planning", "memory", "reliability"]


def emit_signal(skill, signals, signals_dir="signals"):
    """Write signals/<skill>.json per the quality-signal contract.

    No file is written when signals is empty (clean run).
    """
    if not signals:
        return
    os.makedirs(signals_dir, exist_ok=True)
    doc = {
        "source": skill,
        "generated_at": datetime.now().isoformat(),
        "schema_version": "1.0",
        "signals": signals,
    }
    with open(os.path.join(signals_dir, f"{skill}.json"), "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
def load(path):
    if path.endswith(".jsonl"):
        out = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
        return out
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "runs" in data:
        return data["runs"]
    if isinstance(data, list):
        return data
    raise SystemExit("无法解析 results 文件")


def pass_hat_k_task(n, c, k):
    """单个任务的 Pass^k（k 次全部成功，无放回）tau-bench 口径：

        C(c, k) / C(n, k)

    即“从 n 次采样中不放回抽取 k 次，全部成功”的概率。n<k 或 c<k 时
    不可能 k 次全成功，返回 0.0。
    """
    n, c, k = int(n), int(c), int(k)
    if k < 1:
        raise ValueError("k 必须 >= 1")
    if n < k or c < k:
        return 0.0
    return math.comb(c, k) / math.comb(n, k)


def pass_hat_k(per_task_nc, k):
    """Pass^k：k 次全部成功的概率（tau-bench 口径，无放回，逐任务 C(c,k)/C(n,k) 后平均）。

    per_task_nc: 每个任务的 (n, c) 采样计数组成的列表。
    返回 mean_i( C(c_i, k) / C(n_i, k) )。空列表返回 None。
    """
    if not per_task_nc:
        return None
    if k < 1:
        raise ValueError("k 必须 >= 1")
    vals = [pass_hat_k_task(n, c, k) for (n, c) in per_task_nc]
    return sum(vals) / len(vals)


def pass_hat_k_iid(per_task_success_rates, k):
    """旧的 i.i.d. 近似 mean_i( p_i ** k )，仅作 *_iid_mc_legacy 对照（有偏，勿作主指标）。

    与 Pass@k 的 Monte-Carlo 近似 1-(1-p)^k 同源，会在小样本/部分成功区系统性
    高估可靠性——这正是 E-01 面板指出的误归 tau-bench 的遗留问题。
    """
    rates = [float(p) for p in per_task_success_rates]
    if not rates:
        return None
    if k < 1:
        raise ValueError("k 必须 >= 1")
    return sum(p ** k for p in rates) / len(rates)


def pass_at_k(n, c, k):
    """Pass@k 无偏估计（单个任务）：k 次中至少一次成功的概率。

    公式: 1 - C(n-c, k) / C(n, k)，要求 n >= k。
    n < k 时无法无偏估计，返回 None 并打印告警（不崩溃）。
    """
    n, c, k = int(n), int(c), int(k)
    if k < 1:
        raise ValueError("k 必须 >= 1")
    if n < k:
        print("[warn] 采样次数 n=%d < k=%d，无法计算无偏 Pass@%d，跳过该任务"
              % (n, k, k), file=sys.stderr)
        return None
    if c < 0 or c > n:
        raise ValueError("c 必须落在 [0, n] 内")
    return 1.0 - math.comb(n - c, k) / math.comb(n, k)


def pass_at_k_mc(p, k):
    """旧的 Monte-Carlo 近似 1-(1-p)^k，仅作对照保留（有偏，勿作主指标）。"""
    if p <= 0:
        return 0.0
    if p >= 1:
        return 1.0
    return 1 - (1 - p) ** k


def wilson_ci(p, n, z=1.96):
    """Wilson 置信区间（95% 默认），解决小样本下正态近似过窄的问题。

    p: 点估计成功率（0~1）；n: 样本量。返回 (lower, upper)，均夹在 [0,1]。
    当 n=0 返回 (0.0, 0.0)。
    """
    if n <= 0:
        return (0.0, 0.0)
    denom = 1.0 + z * z / n
    center = (p + z * z / (2.0 * n)) / denom
    spread = z * math.sqrt(p * (1 - p) / n + z * z / (4.0 * n * n)) / denom
    return (max(0.0, center - spread), min(1.0, center + spread))


def two_prop_z(p1, n1, p2, n2):
    """两比例 z 检验（双尾），用于 --compare 两版结果显著性。

    返回 p-value；样本量任一为 0 时返回 None。
    """
    if n1 <= 0 or n2 <= 0:
        return None
    pp = (p1 * n1 + p2 * n2) / (n1 + n2)
    if pp <= 0 or pp >= 1:
        return 1.0
    se = math.sqrt(pp * (1 - pp) * (1.0 / n1 + 1.0 / n2))
    if se == 0:
        return 1.0
    z = (p1 - p2) / se
    return 2.0 * (1.0 - 0.5 * (1.0 + math.erf(abs(z) / math.sqrt(2.0))))


def paired_bootstrap_pvalue(a_rates, b_rates, n_boot=2000, seed=1234):
    """R-02/R-18：配对 bootstrap 显著性（带种子，p 值可复现）。

    对每对任务的宏平均差异做符号翻转 bootstrap，返回双侧 p 值。
    相比 two_prop_z（微平均 z 检验），此处两侧统一 per-task 宏平均口径，
    且配对比较不受任务间 n 不均衡影响；种子固定保证同一输入 p 值稳定。
    """
    if len(a_rates) < 2 or len(a_rates) != len(b_rates):
        return None
    import random
    rng = random.Random(seed)
    diffs = [a - b for a, b in zip(a_rates, b_rates)]
    obs = abs(sum(diffs) / len(diffs))
    if obs == 0:
        return 1.0
    hits = 0
    for _ in range(n_boot):
        samp = [d if rng.random() < 0.5 else -d for d in diffs]
        if abs(sum(samp) / len(samp)) >= obs:
            hits += 1
    return hits / n_boot


def bootstrap_ci(values, n_boot=2000, seed=1234):
    """P1-8：对一组逐任务指标值做有放回 bootstrap，返回 95% 百分位置信带 [low, high]。

    固定 seed 保证同一输入结果可复现（与 paired_bootstrap_pvalue 同策略）。
    样本为空返回 [None, None]；样本只有 1 个时退化为其自身（无方差）。
    """
    if not values:
        return [None, None]
    import random
    rng = random.Random(seed)
    n = len(values)
    samples = []
    for _ in range(n_boot):
        samp = [values[rng.randrange(n)] for _ in range(n)]
        samples.append(sum(samp) / n)
    samples.sort()
    lo = samples[int(0.025 * n_boot)]
    hi = samples[int(0.975 * n_boot)]
    return [round(lo, 4), round(hi, 4)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--seed", type=int, default=None, help="采样种子（透传记录，便于复现）")
    ap.add_argument("--compare", default=None, help="另一版 results 路径，做两比例 z 检验显著性")
    ap.add_argument("--strict-k", action="store_true",
                    help="R-18: 任一任务采样 n<k 即退出非0，禁止静默剔除低样本任务（默认关，仅告警）")
    ap.add_argument("--json", action="store_true", help="R-26: 以 JSON 输出指标（供多 agent 出口消费）")
    ap.add_argument("--out", default=None)
    ap.add_argument("--signals-dir", default="signals",
                    help="P1-6: 质量信号写出目录（默认 ./signals）；门禁 qa-release-check 聚合")
    ap.add_argument("--signal-threshold", type=float, default=0.8,
                    help="P1-6: Pass@k 低于该阈值则产出阻断信号（默认 0.8）")
    ap.add_argument("--min-tasks", type=int, default=8,
                    help="P1-8: 任务数低于该阈值时标记 small_sample_warn（默认 8）")
    args = ap.parse_args()
    k = args.k
    if k < 1:
        raise SystemExit("--k 必须 >= 1")
    runs = load(args.results)
    if not runs:
        raise SystemExit("无 run 数据")
    n = len(runs)
    by_task = defaultdict(list)
    for r in runs:
        by_task[r.get("task_id", "t")].append(r)

    task_success = []          # 每个任务的成功率 c/n
    per_task_nc = []            # 每个任务的 (n, c) 采样计数（供 Pass^k 无放回口径）
    per_task_detail = []       # 逐任务明细
    at_k_values = []           # 各任务的无偏 pass@k（None 表示 n<k 被跳过）
    skipped = []
    for tid, rs in sorted(by_task.items()):
        n_i = len(rs)
        c_i = sum(1 for r in rs if r.get("success"))
        p_i = c_i / n_i
        task_success.append(p_i)
        per_task_nc.append((n_i, c_i))
        v = pass_at_k(n_i, c_i, k)
        if v is None:
            skipped.append(tid)
        else:
            at_k_values.append(v)
        per_task_detail.append({
            "task_id": tid, "n": n_i, "c": c_i,
            "p": round(p_i, 4),
            "pass_at_1_macro_wilson_95ci": [round(x, 4) for x in wilson_ci(p_i, n_i)],
            # Pass^k：tau-bench 无放回口径 C(c,k)/C(n,k)
            "pass_hat_%d" % k: round(pass_hat_k_task(c_i, n_i, k), 4),
            # 旧 i.i.d. 近似 (c/n)^k，仅对照（有偏，系统性高估）
            "pass_hat_%d_iid_mc_legacy" % k: round(p_i ** k, 4),
            "pass_at_%d" % k: (round(v, 4) if v is not None else None),
        })

    # R-18: n<k 任务不得静默剔除——显式暴露覆盖率，--strict-k 时直接退出非0。
    if args.strict_k and skipped:
        raise SystemExit(
            "[ERR] --strict-k: 以下任务采样 n<k=%d，无偏 Pass@%d 不可计算且已被剔除: %s\n"
            "请补充采样到 n>=k，或用任务级 Wilson CI（per_task.pass_at_1_macro_wilson_95ci）替代。"
            % (k, k, ", ".join(skipped)))
    if skipped:
        print("[warn] 任务级 n<k 被剔除（不计入无偏 Pass@%d）：%s；"
              "覆盖率=%d/%d。如需禁止剔除请加 --strict-k"
              % (k, ", ".join(skipped), len(at_k_values), len(by_task)), file=sys.stderr)

    pass1 = statistics.mean(task_success)
    hat_k = pass_hat_k(per_task_nc, k)
    hat_k_iid = pass_hat_k_iid(task_success, k)
    at_k = (sum(at_k_values) / len(at_k_values)) if at_k_values else None

    tc_total = tc_ok = 0
    for r in runs:
        for c in (r.get("tool_calls") or []):
            tc_total += 1
            if c.get("correct"):
                tc_ok += 1
    tc_acc = (tc_ok / tc_total) if tc_total else None

    dim_sum = {d: 0.0 for d in DIMS}
    dim_vals = {d: [] for d in DIMS}
    dim_n = 0
    for r in runs:
        d = r.get("dims") or {}
        if any(key in d for key in DIMS):
            dim_n += 1
            for key in DIMS:
                if key in d:
                    v = float(d[key])
                    dim_sum[key] += v
                    dim_vals[key].append(v)
    dims_avg = {key: (dim_sum[key] / dim_n if dim_n else None) for key in DIMS}
    # P1-8：任务级维度方差（每维度逐 run 样本标准差）。
    dims_std = {key: (round(statistics.stdev(v), 4) if len(v) > 1 else 0.0)
                for key, v in dim_vals.items()}

    # Wilson 95% 置信区间。
    # RK-16：pass1 是「逐任务成功率」的宏平均（per-task 点估计取均值），
    # 因此 CI 的有效样本量应是**任务数 n_tasks**，而非总 run 数 n——否则口径错配
    # 会把区间人为收窄。这里显式用 n_tasks 并标注为任务级近似。
    n_tasks = len(by_task)
    ci_low, ci_high = wilson_ci(pass1, n_tasks)
    res = {
        "n_runs": n,
        "n_tasks": len(by_task),
        "k": k,
        "seed": args.seed,
        # R-31：pass_at_1_macro 实为「逐任务成功率宏平均」（各任务通过率取均值），
        # 非无放回/无偏 Pass@1；字段改名以与 pass@k（至少一次成功）明确区分，避免混淆。
        "pass_at_1_macro": round(pass1, 4),
        "pass_at_1_macro_wilson_95ci": [round(ci_low, 4), round(ci_high, 4)],
        # Pass^k：k 次全过（tau-bench 无放回口径 C(c,k)/C(n,k)，逐任务后平均）
        "pass_hat_%d" % k: round(hat_k, 4) if hat_k is not None else None,
        # Pass^k 旧 i.i.d. 近似 (c/n)^k，仅供对照，系统性高估，勿作主指标
        "pass_hat_%d_iid_mc_legacy" % k: round(hat_k_iid, 4) if hat_k_iid is not None else None,
        # Pass@k：至少一次成功（无偏估计，逐任务后平均）
        "pass_at_%d" % k: round(at_k, 4) if at_k is not None else None,
        # 旧的 Monte-Carlo 近似，仅供对照，勿作主指标
        "pass_at_%d_mc_legacy" % k: round(pass_at_k_mc(pass1, k), 4),
        "pass_at_k_skipped_tasks": skipped,
        # R-18: 无偏 Pass@k 覆盖透明度——剔除任务数与被纳入任务数（禁止静默偏差）
        "pass_at_k_included_tasks": len(at_k_values),
        "pass_at_k_excluded_tasks": len(skipped),
        "pass_at_k_coverage": (round(len(at_k_values) / len(by_task), 4)
                               if by_task else None),
        "tool_call_accuracy": round(tc_acc, 4) if tc_acc is not None else None,
        "dims_avg": {key: (round(v, 4) if v is not None else None)
                     for key, v in dims_avg.items()},
        "per_task": per_task_detail,
    }

    # ---- P1-8：任务级方差 + bootstrap 置信带 + 小样本告警 ----
    # 逐任务指标值（per_task_detail 已含每个任务的 pass_hat_k / pass_at_k 点估计）。
    hat_k_task_vals = [d["pass_hat_%d" % k] for d in per_task_detail]
    at_k_task_vals = [d["pass_at_%d" % k] for d in per_task_detail
                      if d["pass_at_%d" % k] is not None]

    def _mean_std(vals):
        if not vals:
            return None, None
        m = statistics.mean(vals)
        s = statistics.stdev(vals) if len(vals) > 1 else 0.0
        return m, s

    hk_mean, hk_std = _mean_std(hat_k_task_vals)
    ak_mean, ak_std = _mean_std(at_k_task_vals)
    hk_ci = bootstrap_ci(hat_k_task_vals, n_boot=2000, seed=1234)
    ak_ci = bootstrap_ci(at_k_task_vals, n_boot=2000, seed=1234)
    small_sample = n_tasks < args.min_tasks
    res["pass_hat_%d_task_mean" % k] = round(hk_mean, 4) if hk_mean is not None else None
    res["pass_hat_%d_task_std" % k] = round(hk_std, 4) if hk_std is not None else None
    res["pass_hat_%d_bootstrap_95ci" % k] = hk_ci if hk_ci[0] is not None else None
    res["pass_at_%d_task_mean" % k] = round(ak_mean, 4) if ak_mean is not None else None
    res["pass_at_%d_task_std" % k] = round(ak_std, 4) if ak_std is not None else None
    res["pass_at_%d_bootstrap_95ci" % k] = ak_ci if ak_ci[0] is not None else None
    # AG-02：pass_at_1_macro 的 bootstrap 置信带（任务级重采样），与 Wilson 解析区间互为补充。
    # 对 per_task_detail[].p（逐任务成功率）有放回重采样求宏平均，不假设正态，对偏态任务分布更稳健。
    task_p_vals = [d["p"] for d in per_task_detail]
    macro_boot_ci = bootstrap_ci(task_p_vals, n_boot=2000, seed=1234)
    res["pass_at_1_macro_bootstrap_95ci"] = (list(macro_boot_ci)
                                             if macro_boot_ci[0] is not None else None)
    res["dims_std"] = {key: (round(v, 4) if v is not None else None)
                       for key, v in dims_std.items()}
    res["small_sample_warn"] = small_sample
    res["min_tasks"] = args.min_tasks

    # 显著性检验（R-02 修复：两侧统一 per-task 宏平均口径 + 配对 bootstrap，p 值可复现）
    compare = None
    if args.compare:
        other = load(args.compare)
        o_by_task = defaultdict(list)
        for r in other:
            o_by_task[r.get("task_id", "t")].append(r)
        # 仅取两侧均出现的任务做配对比较，避免口径混用（宏平均 vs 微平均）
        common = [t for t in by_task if t in o_by_task]
        a_rates = [sum(1 for r in by_task[t] if r.get("success")) / len(by_task[t])
                   for t in common]
        b_rates = [sum(1 for r in o_by_task[t] if r.get("success")) / len(o_by_task[t])
                   for t in common]
        a_macro = statistics.mean(a_rates) if a_rates else 0.0
        b_macro = statistics.mean(b_rates) if b_rates else 0.0
        pval = paired_bootstrap_pvalue(a_rates, b_rates) if len(common) >= 2 else None
        sig = (pval is not None and pval < 0.05)
        compare = {
            "pass_at_1_macro": round(a_macro, 4), "other_pass_at_1_macro": round(b_macro, 4),
            "other_n": len(other), "tasks_compared": len(common),
            "p_value": (round(pval, 4) if pval is not None else None),
            "significant_at_0.05": sig,
        }
        res["compare"] = compare

    txt = "==== Agent 评测指标 ====\n"
    txt += "run 数: %d | 任务数: %d | k = %d%s\n" % (
        res["n_runs"], res["n_tasks"], k, f" | seed={args.seed}" if args.seed is not None else "")
    txt += "Pass@1: %s  (Wilson 95%% CI: [%.4f, %.4f], 基于任务数 n_tasks=%d 的近似)\n" % (
        res["pass_at_1_macro"], ci_low, ci_high, n_tasks)
    # RK-20：明确标注 Pass@1 与 Pass^k / Pass@k 的分母不共线，避免同屏误导。
    txt += "Pass^%d (k 次全过, tau-bench 无放回 C(c,k)/C(n,k) 逐任务平均): %s  [分母: 全部 %d 任务, n<k 任务贡献 0]\n" % (
        k, res["pass_hat_%d" % k], n_tasks)
    txt += "Pass^%d (旧 i.i.d. 近似 (c/n)^k, 仅供对照, 勿作主指标): %s\n" % (k, res["pass_hat_%d_iid_mc_legacy" % k])
    txt += "Pass@%d (至少一次成功, 无偏估计): %s  [分母: 仅 %d 个 n>=k 任务, 剔除 %d]\n" % (
        k, res["pass_at_%d" % k], res["pass_at_k_included_tasks"], res["pass_at_k_excluded_tasks"])
    txt += "Pass@%d (旧 MC 近似, 仅对照): %s\n" % (k, res["pass_at_%d_mc_legacy" % k])
    if skipped:
        txt += "  注: 以下任务采样 n < k，未计入无偏 Pass@%d: %s\n" % (k, ", ".join(skipped))
    if compare:
        txt += ("显著性(--compare): 另一版 Pass@1=%s (n=%d), p=%.4f → %s\n"
                % (compare["other_pass_at_1_macro"], compare["other_n"], compare["p_value"],
                   "两版差异显著" if compare["significant_at_0.05"] else "两版差异不显著(α=0.05)"))
    txt += "工具调用准确率: %s\n" % res["tool_call_accuracy"]
    txt += "五维度均值: " + ", ".join("%s=%s" % (key, v) for key, v in res["dims_avg"].items()) + "\n"
    # R-12：五维度为被测方自报（非 ground-truth），明示避免被自评拉高。
    txt += "⚠️ 五维度均值为**被测方自报**（非 ground-truth）；若评测集提供 checkers 实测判定，应以 checkers 结果为准，本值仅作参考。\n"
    # P1-8：任务级方差与 bootstrap 置信带（取代"仅点估计"）。
    txt += "Pass^%d 任务级 mean±std: %s ± %s (bootstrap 95%% CI: [%s, %s])\n" % (
        k, res["pass_hat_%d_task_mean" % k], res["pass_hat_%d_task_std" % k],
        (res["pass_hat_%d_bootstrap_95ci" % k] or [None, None])[0],
        (res["pass_hat_%d_bootstrap_95ci" % k] or [None, None])[1])
    txt += "Pass@%d 任务级 mean±std: %s ± %s (bootstrap 95%% CI: [%s, %s])\n" % (
        k, res["pass_at_%d_task_mean" % k], res["pass_at_%d_task_std" % k],
        (res["pass_at_%d_bootstrap_95ci" % k] or [None, None])[0],
        (res["pass_at_%d_bootstrap_95ci" % k] or [None, None])[1])
    txt += "五维度 std: " + ", ".join("%s=%s" % (key, v) for key, v in res["dims_std"].items()) + "\n"
    if small_sample:
        txt += ("⚠️ 任务数 n_tasks=%d < min_tasks=%d，置信带加宽，结论谨慎"
                "（small_sample_warn=true）\n" % (n_tasks, args.min_tasks))
    txt += "逐任务明细:\n"
    for d in per_task_detail:
        txt += "  - %s: n=%d c=%d p=%s pass^%d=%s pass@%d=%s\n" % (
            d["task_id"], d["n"], d["c"], d["p"],
            k, d["pass_hat_%d" % k], k, d["pass_at_%d" % k])
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(txt)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=2)
        print("已写入", args.out)

    # ---- P1-6：质量信号契约（接入 qa-release-check 门禁）----
    # agent_eval_pass_at_k：Pass@k 低于阈值→阻断（high）；否则非阻断信息信号。
    # agent_eval_low_ci：置信区间过宽→非阻断告警（信息性，不阻断）。
    signals = []
    at_k = res.get("pass_at_%d" % k)
    if at_k is None:
        signals.append({
            "signal": "agent_eval_pass_at_k", "severity": "info", "count": 1,
            "blocking": False,
            "verdict": "not_computable_n<k", "detail_ref": args.out or "stdout",
        })
    else:
        blocking = at_k < args.signal_threshold
        signals.append({
            "signal": "agent_eval_pass_at_k", "severity": "high" if blocking else "info",
            "count": 1, "blocking": blocking, "detail_ref": args.out or "stdout",
            "verdict": "pass_at_%d=%.4f(阈值%.2f)" % (k, at_k, args.signal_threshold),
        })
    ci = res.get("pass_at_1_macro_wilson_95ci") or [0.0, 1.0]
    ci_width = round(ci[1] - ci[0], 4)
    if ci_width > 0.2:
        signals.append({
            "signal": "agent_eval_low_ci", "severity": "info", "count": 1,
            "blocking": False, "detail_ref": args.out or "stdout",
            "verdict": "pass@1 Wilson 95%% CI 宽度=%.4f(>0.2 样本不足)" % ci_width,
        })
    emit_signal("qa-agent-eval", signals, args.signals_dir)
    if signals:
        print("[signal] 已写出 %d 条信号到 %s/qa-agent-eval.json"
              % (len(signals), args.signals_dir), file=sys.stderr)


if __name__ == "__main__":
    main()
