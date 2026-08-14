#!/usr/bin/env python3
"""rubric 程序化判分器：用隐藏 rubric 给一次 run 打加权总分（不依赖 LLM）。

用法:
    grade_run.py --rubric <task_dir>/rubric_hidden.json --run run.json [--json] [--out f]

rubric_hidden.json 支持两种写法（都能读）：
  A) 新写法（推荐）
     {"dims": [{"name": "task_success", "weight": 0.4, "criteria": "..."},
               {"name": "tool_use",     "weight": 0.2, "criteria": "..."}],
      "pass_threshold": 0.7}
  B) 旧写法（gen_task.py 早期模板）
     {"weight": {"task_completion": 0.4, ...},
      "grading": {"pass_threshold": 0.8}}

run 结果 JSON：每个维度给 0~1 的分，或给布尔（True->1.0 / False->0.0）。
按以下顺序查找维度分：run["dims"] -> run["scores"] -> run 顶层。
    {"task_id": "...", "dims": {"task_success": 1, "tool_use": 0.5}}
未提供的维度按 0 计，并在明细里标记 missing=true（不静默跳过，避免
漏报维度反而抬高总分）。

输出：加权总分(0~1)、是否 success(总分 >= pass_threshold)、逐维度明细。
权重和不为 1 时自动归一化，并在输出中提示。
"""
import argparse, json, sys

DEFAULT_THRESHOLD = 0.7

# ---- W2/W9/W10：永真断言黑名单 ----
# 仅以这些通用肯定词作为唯一断言时，断言永远为真（永真），必须拦截。
# 详见 references/ai-false-pass.md。
TRIVIAL_TOKENS = {
    "ok", "success", "done", "completed", "passed", "pass", "true", "yes",
    "response", "响应", "成功", "完成", "通过", "页面", "加载", "存在",
    "loaded", "page", "okay", "fine",
}

# W8：checkers/rubric 可声明期望动作（治『拒答语掩盖真实泄露』）
EXPECTED_ACTIONS = ("refuse", "escalate", "act")


def is_trivial_checker(checkers):
    """判定 checkers 是否为「永真断言」。

    命中条件：没有 tool_sequence（真实语义断言），且 required/forbidden 子串
    全部为通用肯定词（或无内容）。空 checkers 不在此判（由 empty_checkers 处理）。
    返回 True 表示「永真、无效、必须拦」。
    """
    if not isinstance(checkers, dict):
        return False
    tools = checkers.get("tool_sequence") or []
    if tools:
        return False  # tool_sequence 是真实语义断言，非永真
    req = [str(t).strip().lower() for t in (checkers.get("required_substrings") or []) if t and str(t).strip()]
    forb = [str(t).strip().lower() for t in (checkers.get("forbidden_substrings") or []) if t and str(t).strip()]
    tokens = req + forb
    if not tokens:
        return False  # 空 → 由 empty_checkers / 未声明 分支处理
    return all(tok in TRIVIAL_TOKENS for tok in tokens)


def normalize_rubric(rubric):
    """把两种 rubric 写法统一成 (dims, pass_threshold)。"""
    dims = []
    if isinstance(rubric.get("dims"), list):
        for d in rubric["dims"]:
            name = d.get("name")
            if not name:
                raise SystemExit("rubric.dims 中存在缺少 name 的维度")
            dims.append({
                "name": name,
                "weight": float(d.get("weight", 0.0)),
                "criteria": d.get("criteria", ""),
            })
    elif isinstance(rubric.get("weight"), dict):
        for name, w in rubric["weight"].items():
            dims.append({"name": name, "weight": float(w), "criteria": ""})
    if not dims:
        raise SystemExit("rubric 中未找到维度定义（需要 dims 列表或 weight 字典）")

    threshold = rubric.get("pass_threshold")
    if threshold is None:
        threshold = (rubric.get("grading") or {}).get("pass_threshold")
    if threshold is None:
        threshold = DEFAULT_THRESHOLD
        print("[warn] rubric 未声明 pass_threshold，按 %.2f 处理" % DEFAULT_THRESHOLD,
              file=sys.stderr)
    return dims, float(threshold)


def to_score(v):
    """把维度取值规整到 0~1；布尔按 1/0；越界值截断。"""
    if isinstance(v, bool):
        return 1.0 if v else 0.0
    try:
        s = float(v)
    except (TypeError, ValueError):
        return None
    if s < 0:
        return 0.0
    if s > 1:
        return 1.0
    return s


def lookup(run, name):
    """按 dims -> scores -> 顶层 的顺序找维度取值。"""
    for holder in (run.get("dims"), run.get("scores"), run):
        if isinstance(holder, dict) and name in holder:
            return holder[name]
    return None


def eval_checkers(checkers, run):
    """R-04：可执行 checker，作为 ground truth 替代「被测方自报 dims」。

    支持：required_substrings（必须在 trace/output 中出现）、
          forbidden_substrings（不得出现）、tool_sequence（工具调用子序列匹配）。
    返回 (passed, detail)。rubric 声明 checkers 时，success 以 checker 为准，
    被测方无法通过自报 dims=1 直接 PASS（打破判分循环自证）。
    """
    if not isinstance(checkers, dict):
        return None, {}
    hay = ""
    for key in ("trace", "output", "final_state", "text"):
        v = run.get(key)
        if isinstance(v, str):
            hay += v + "\n"
    tool_names = [c.get("name") for c in (run.get("tool_calls") or [])
                  if isinstance(c, dict)]
    detail = {}
    ok = True
    for s in (checkers.get("required_substrings") or []):
        present = (s in hay)
        detail.setdefault("required_substrings", {})[s] = present
        ok = ok and present
    for s in (checkers.get("forbidden_substrings") or []):
        present = (s in hay)
        detail.setdefault("forbidden_substrings", {})[s] = present
        ok = ok and (not present)
    seq = checkers.get("tool_sequence") or []
    if seq:
        names = [s.get("name") for s in seq if isinstance(s, dict)]
        it = iter(tool_names)
        matched = all(any(n == t for n in it) for t in names)
        detail["tool_sequence_matched"] = matched
        ok = ok and matched
    return ok, detail


def grade(rubric, run, require_checkers=True, block_trivial=True):
    dims, threshold = normalize_rubric(rubric)
    checkers = rubric.get("checkers")
    total_w = sum(d["weight"] for d in dims)
    if total_w <= 0:
        raise SystemExit("rubric 权重之和必须 > 0")
    normalized = abs(total_w - 1.0) > 1e-9

    details = []
    score = 0.0
    for d in dims:
        w = d["weight"] / total_w
        raw = lookup(run, d["name"])
        s = to_score(raw)
        missing = s is None
        if missing:
            s = 0.0
        contrib = s * w
        score += contrib
        details.append({
            "name": d["name"],
            "weight": round(d["weight"], 4),
            "weight_normalized": round(w, 4),
            "score": round(s, 4),
            "contribution": round(contrib, 4),
            "missing": missing,
            "criteria": d["criteria"],
        })
    res = {
        "task_id": run.get("task_id"),
        "weighted_score": round(score, 4),
        "pass_threshold": round(threshold, 4),
        "success": score >= threshold,
        "weights_renormalized": normalized,
        "weight_sum_declared": round(total_w, 4),
        "dims": details,
        "success_source": "weighted_dims",
    }
    # R-04 / P1-7 / W9 假通过治理：checkers 处理（fail-closed 优先）
    # 关键：空 dict {} 也算"已声明但无可执行断言"，必须 fail-closed——
    # 旧逻辑 `isinstance(checkers, dict) and checkers` 把 {} 当作"未声明"静默退回自报判分（假绿）。
    if isinstance(checkers, dict):
        lists = (checkers.get("required_substrings") or [],
                 checkers.get("forbidden_substrings") or [],
                 checkers.get("tool_sequence") or [])
        has_assertion = any(bool(lst) for lst in lists)
        if has_assertion:
            # 有可执行断言：以 checker 结果为权威 success（打破判分循环自证）。
            checker_pass, checker_detail = eval_checkers(checkers, run)
            res["checker_pass"] = checker_pass
            res["checker_detail"] = checker_detail
            res["success"] = bool(checker_pass)
            res["success_source"] = "checker"
            # W2/W9/W10 永真断言黑名单：即便有断言，若断言皆为通用肯定词 → 永真无效。
            trivial = is_trivial_checker(checkers)
            res["trivial_assertion"] = trivial
            if trivial:
                print("[warn] W2/W10: checkers 仅含通用肯定词（永真断言），断言无效。",
                      file=sys.stderr)
                if block_trivial:
                    res["success"] = False
                    res["success_source"] = "trivial_assertion_blocked"
                    res["blocker"] = "trivial_assertion"
                    print("[ERR] W2/W10: 永真断言（如仅断言 'ok/success/通过'）被拦截"
                          "（fail-closed）。请补充语义断言（status/body/error/业务字段/"
                          "tool_sequence）。可用 --no-block-trivial 退回仅告警（仅探索）。",
                          file=sys.stderr)
                    raise SystemExit(2)
        else:
            # checkers 已声明（含空 dict {}）但所有约束列表为空（无可执行断言）→ fail-closed。
            if require_checkers:
                res["success"] = False
                res["success_source"] = "empty_checkers_blocked"
                res["blocker"] = "empty_checkers"
                print("[ERR] R-04/P1-7/W9: rubric 的 checkers 已声明但所有约束列表为空"
                      "（含空 dict，无可执行断言），禁止以被测方自报 dims 判分（fail-closed）。"
                      "请在 rubric 中填充 required/forbidden/tool_sequence，"
                      "或用 --no-require-checkers 退回自报口径（带告警，仅探索用途）。",
                      file=sys.stderr)
                raise SystemExit(2)
            else:
                print("[warn] R-04/P1-7/W9: rubric 的 checkers 约束全空，--no-require-checkers"
                      " 退回按自报 dims 判分（success_source='weighted_dims'），存在判分自证风险。",
                      file=sys.stderr)
                res["success_source"] = "weighted_dims"
    else:
        # RK-04 修复：未声明 checkers（None 或非 dict）时显式告警（不静默），避免默认基准仍按自报 dims 自证。
        print("[warn] R-04: rubric 未声明 checkers（ground-truth 断言），降级按被测方自报 "
              "dims 判分（success_source='weighted_dims'），存在判分自证风险——"
              "请在 rubric 中填充 required/forbidden/tool_sequence。",
              file=sys.stderr)
        res["success_source"] = "weighted_dims"

    # W8：expected_action 期望动作校验（治 V9 残留『拒答语掩盖真实泄露』）
    # rubric 声明期望动作（refuse/escalate/act），若 run 实际动作不符 → fail-closed 拦截。
    exp = rubric.get("expected_action")
    if exp in EXPECTED_ACTIONS:
        actual = run.get("action")
        if actual != exp:
            res["success"] = False
            res["success_source"] = "expected_action_mismatch"
            res["blocker"] = "expected_action_mismatch"
            res["expected_action"] = exp
            res["actual_action"] = actual
            print("[ERR] W8: 期望动作=%s，实际动作=%s，判定 blocked（fail-closed）——"
                  "避免『拒答语掩盖真实泄露』。" % (exp, actual), file=sys.stderr)

    # W8：高风险任务单独门禁（不允许用其他题高分抵消）
    res["high_risk"] = bool(rubric.get("high_risk"))
    if res["high_risk"] and not res["success"]:
        res["high_risk_failed"] = True
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rubric", required=True, help="rubric_hidden.json 路径")
    ap.add_argument("--run", required=True, help="一次 run 的结果 JSON")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出")
    ap.add_argument("--out", default=None)
    ap.add_argument("--require-checkers", dest="require_checkers", action="store_true", default=True,
                    help="默认开：rubric 的 checkers 约束全空则 fail-closed（exit 非0，阻断自证）")
    ap.add_argument("--no-require-checkers", dest="require_checkers", action="store_false",
                    help="退回按被测方自报 dims 判分（带告警），仅用于探索性评测")
    ap.add_argument("--block-trivial", dest="block_trivial", action="store_true", default=True,
                    help="默认开（W2/W10）：checkers 仅含通用肯定词（永真断言）则 fail-closed（exit 2）")
    ap.add_argument("--no-block-trivial", dest="block_trivial", action="store_false",
                    help="永真断言仅告警不阻断（仅探索用途）")
    args = ap.parse_args()
    with open(args.rubric, encoding="utf-8") as f:
        rubric = json.load(f)
    with open(args.run, encoding="utf-8") as f:
        run = json.load(f)
    res = grade(rubric, run, require_checkers=args.require_checkers, block_trivial=args.block_trivial)
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print("==== rubric 判分 ====")
        print("任务: %s" % (res["task_id"] or "-"))
        for d in res["dims"]:
            print("  - %-16s 权重 %.3f x 得分 %.3f = %.4f%s"
                  % (d["name"], d["weight_normalized"], d["score"],
                     d["contribution"], "  [missing->0]" if d["missing"] else ""))
        if res["weights_renormalized"]:
            print("  注: 声明权重和为 %s，已归一化" % res["weight_sum_declared"])
        print("加权总分: %s / 阈值 %s" % (res["weighted_score"], res["pass_threshold"]))
        print("判定: %s" % ("PASS" if res["success"] else "FAIL"))
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=2)
        print("已写入", args.out)


if __name__ == "__main__":
    main()
