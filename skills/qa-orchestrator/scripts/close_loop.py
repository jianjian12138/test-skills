#!/usr/bin/env python3
"""qa-orchestrator: 按生命周期顺序把变更目录推进到归档，并做「质量闭合」判定（真闭环）。

用法:
    python close_loop.py --change changes/<slug> [--apply] [--strict]

逻辑：
  1. 从 stages.json（单一事实源）依次检查 8 个阶段目录是否已有非空产物。
  2. 对每个阶段，输出「该调哪个技能 + 期望产物 + 当前状态」。
  3. `--apply` 实标完成前先做 R-14 内容校验：已完成阶段若其全部产物均为「空壳」
     （JSON 无关键字段 / 空集合 / 损坏），则**不得**标完成，记入 shell_stages 并告警，
     防止「空壳阶段」被误标就绪（fail-closed）。
  4. 质量闭合判定（修复 P0-A/C「伪闭环」）：消费 06/07 阶段的上游质量产物
     （test-report.json / bug_report.json / security_findings.json），用「闭合度三问」
     程序化评估是否真闭环：
        ① 是谁 —— 是否定位到具体失败/缺陷（有 failed case 或 open bug）
        ② 为什么 —— 是否有因果链（失败有归因，否则标「归因缺失」）
        ③ 可处置 —— 是否给出可处置动作（open S1/S2 需有处置建议）
  4. 若任一质量门不过 → 判「未闭合」；`--strict` 时 sys.exit(1)。

本脚本只负责编排与状态更新，不替代具体技能执行；但相比旧版，它**会消费质量产物**
而非只看目录是否存在，从而具备「质量守门」能力。
"""
import argparse
import json
import os
import re
import sys

import _stages

STAGES = _stages.resolve_stages()  # W7：默认 domain_extensions 为空 → 与 load_stages() 一致

SEVERITY_OPEN_BLOCK = {"S1", "S2"}
SEC_HIGH_BLOCK = {"Critical", "High", "严重", "高"}


def find_file(change_dir, fname, subdirs=None):
    """在 change_dir 及其指定子目录里找文件（忽略大小写）。"""
    candidates = [change_dir]
    if subdirs:
        candidates += [os.path.join(change_dir, s) for s in subdirs]
    for d in candidates:
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if f.lower() == fname.lower():
                return os.path.join(d, f)
    return None


def load_json(path):
    if not path:
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def evaluate_closure(change_dir, allow_no_evidence=False):
    """程序化「闭合度三问」评估，返回 (closed: bool, answers: dict, blockers: list)。

    P0-B（fail-closed）：进入评估即先做「证据存在性硬闸」——若三份质量产物
    （test-report/bug_report/security_findings）全部缺失，且变更未显式声明
    qa_required=false，则直接判未闭合（no_quality_evidence），与信号门禁
    fail-closed 哲学一致。下方三问逻辑保持不变。
    """
    report = load_json(find_file(change_dir, "test-report.json", ["07-report"]))
    bugs = load_json(find_file(change_dir, "bug_report.json", ["07-report"])) or []
    sec = load_json(find_file(change_dir, "security_findings.json", ["06-execution", "07-report"])) or []

    if isinstance(bugs, dict):
        bugs = bugs.get("bugs", bugs.get("items", []))
    if isinstance(sec, dict):
        sec = sec.get("findings", sec.get("items", []))

    # —— P0-B：证据存在性硬闸（fail-closed）——
    # R-37 修复：需要 QA 的变更（qa_required=true，含缺省），证据硬闸**不可**被 --allow-no-evidence
    # 绕过（fail-closed）；该 flag 仅在「显式声明 qa_required=false 并留痕」时才有意义（此时本就放行）。
    meta = load_json(os.path.join(change_dir, "00-init", "change_meta.json")) or {}
    qa_required = meta.get("qa_required", True)
    has_evidence = bool(report) or bool(bugs) or bool(sec)
    if not has_evidence:
        if qa_required:
            return (False,
                    {"who": "⛔ 未提供任何质量证据（qa_required=true，证据硬闸不可被 --allow-no-evidence 绕过，fail-closed）"},
                    ["no_quality_evidence:change_requires_qa_but_none_provided"])
        else:
            return (True,
                    {"who": "✅ 变更声明无需 QA（qa_required=false，已留痕）"},
                    [])

    answers = {}
    blockers = []

    # ① 是谁 —— 是否定位到具体失败/缺陷
    failed = []
    if report:
        failed = report.get("failed_cases") or report.get("failed") or []
        p0_total = report.get("p0_total", 0)
        p0_pass = report.get("p0_pass", 0)
        if p0_total and p0_pass < p0_total:
            failed.append(f"P0 用例 {p0_pass}/{p0_total} 未通过")
    open_bugs = [b for b in bugs if str(b.get("status", "")).lower() in ("open", "未关闭", "")]
    if not failed and not open_bugs:
        answers["who"] = "✅ 无未定位失败（测试通过、无未关缺陷）"
    else:
        who_items = [str(x) for x in failed[:5]] + [f"{b.get('id','')}:{b.get('title','')}" for b in open_bugs[:5]]
        answers["who"] = "❌ 已定位：" + "；".join(who_items)

    # ② 为什么 —— 是否有因果链（失败需有归因 / 缺陷需有根因）
    missing_rootcause = False
    if failed:
        # 报告里若没有 root_cause 字段或为空，视为归因缺失
        if not report.get("root_cause") and not report.get("analysis"):
            missing_rootcause = True
    for b in open_bugs:
        if not b.get("root_cause") and not b.get("reason"):
            missing_rootcause = True
    if not (failed or open_bugs):
        answers["why"] = "✅ 无可分析现象"
    elif missing_rootcause:
        answers["why"] = "❌ 现象已现但缺因果链（未写根因/分析）"
        blockers.append("why:missing_rootcause")
    else:
        answers["why"] = "✅ 现象→根因因果链完整"

    # ③ 可处置 —— 是否给出可处置动作（open S1/S2 需有处置建议/负责人）
    unactionable = [b for b in open_bugs
                    if str(b.get("severity", "")).upper() in SEVERITY_OPEN_BLOCK
                    and not (b.get("action") or b.get("owner") or b.get("fix"))]
    if not unactionable:
        answers["actionable"] = "✅ 高优缺陷均有处置方案"
    else:
        answers["actionable"] = (f"❌ {len(unactionable)} 个 S1/S2 缺陷无处置方案/负责人")
        blockers.append("actionable:missing_plan")

    # 硬门禁：存在未关 S1/S2 或 Critical/High 安全项 → 直接未闭合
    open_critical = [b for b in open_bugs if str(b.get("severity", "")).upper() in SEVERITY_OPEN_BLOCK]
    if open_critical:
        blockers.append(f"blocker:open_{len(open_critical)}_S1/S2_bugs")
    high_sec = [s for s in sec if str(s.get("severity", "")).lower() in
                {x.lower() for x in SEC_HIGH_BLOCK}]
    if high_sec:
        blockers.append(f"blocker:{len(high_sec)}_Critical/High_security")

    closed = len(blockers) == 0
    return closed, answers, blockers


def update_readme(readme_path, stage, status):
    if not os.path.exists(readme_path):
        return
    with open(readme_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    pat = re.compile(r"^(\|\s*\d+\s*\|\s*" + re.escape(stage) + r"\s*\|)")
    out = []
    for ln in lines:
        if pat.match(ln):
            parts = ln.rstrip("\n").split("|")
            if len(parts) >= 7:
                parts[5] = " " + status + " "
            ln = "|".join(parts) + "\n"
        out.append(ln)
    with open(readme_path, "w", encoding="utf-8") as f:
        f.writelines(out)


def build_model(change_dir, apply=False, allow_no_evidence=False, strict_cross=False):
    """收集闭环模型（人读与 JSON 共用），返回 dict。"""
    stages_out = []
    pending = []
    shell_stages = []  # R-14：已完成但产物为空壳、--apply 不得标完成的阶段
    for st in STAGES:
        sd = os.path.join(change_dir, st["dir"])
        done = _stages.is_stage_done(sd, st)
        skill = st["skills"][0]
        alts = st.get("alternates", [])
        stages_out.append({
            "dir": st["dir"],
            "title": st["title"],
            "status": "done" if done else "pending",
            "skill": skill,
            "alternates": alts,
            "artifacts": st.get("artifacts", []),
        })
        if done:
            ok, reason = _stages.validate_artifact_content(sd, st)
            if apply:
                if ok:
                    update_readme(os.path.join(change_dir, "README.md"), st["dir"], "已完成")
                else:
                    shell_stages.append({"dir": st["dir"], "reason": reason})
            else:
                # R-36：非 --apply 路径也做 R-14 空壳检测，提前暴露空壳阶段（fail-closed 透明化），
                # 使 shell_stages 在 --strict 下同样能拦（无论是否 --apply），route_next/非 apply
                # close_loop 不再对 {"cases":[]} 这类空壳放行。
                if not ok:
                    shell_stages.append({"dir": st["dir"], "reason": reason})
        else:
            pending.append({"dir": st["dir"], "skill": skill})

    closed, answers, blockers = evaluate_closure(change_dir, allow_no_evidence=allow_no_evidence)
    nxt = None
    if pending and closed:
        nxt = {"stage": pending[0]["dir"], "skill": pending[0]["skill"]}
    elif not pending and not closed:
        nxt = {"stage": None, "skill": None, "note": "all_stages_done_but_unclosed"}
    elif not pending and closed:
        nxt = {"stage": None, "skill": None, "note": "all_done_and_closed"}

    # P1-9：横切关注点追踪——根据变更特征推荐，并对照 cross_cutting_done.json
    # 标记哪些已执行。默认仅提示；--strict-cross 时将未跑的高相关项转门禁。
    xc_done = _stages.load_cross_cutting_done(change_dir)
    xc_rec = _stages.recommend_cross_cutting(change_dir, STAGES)
    cross_cutting = [{"skill": r["skill"], "reason": r["reason"],
                      "done": r["skill"] in xc_done} for r in xc_rec]
    pending_xc = [r["skill"] for r in cross_cutting if not r["done"]]
    cross_cutting_blocked = bool(strict_cross and pending_xc)
    if nxt is not None:
        nxt["cross_cutting_hint"] = pending_xc

    return {
        "change": change_dir,
        "stages": stages_out,
        "closure": {
            "closed": closed,
            "answers": answers,
            "blockers": blockers,
        },
        "cross_cutting": cross_cutting,
        "cross_cutting_hint": pending_xc,
        "cross_cutting_blocked": cross_cutting_blocked,
        "shell_stages": shell_stages,  # R-14：空壳阶段（--apply 不得标完成）
        "next": nxt,
        "apply": apply,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--change", required=True)
    ap.add_argument("--apply", action="store_true", help="把已完成阶段标记到 README 看板")
    ap.add_argument("--strict", action="store_true", help="未闭合时 sys.exit(1)")
    ap.add_argument("--allow-no-evidence", action="store_true",
                    help="显式豁免 P0-B 证据硬闸（仅人工归档/紧急用，须 change_meta qa_required=false 留痕），默认关")
    ap.add_argument("--mark-cross", metavar="SKILL",
                    help="记录某横切技能已在本次变更中执行（写入 cross_cutting_done.json）；不影响闭合判定")
    ap.add_argument("--strict-cross", action="store_true",
                    help="P1-9：高相关横切技能未跑时，连同 --strict 一起转门禁（fail-closed，默认关，须显式开启）")
    ap.add_argument("--json", action="store_true", help="输出机器可读 JSON（供代理/CI 消费）")
    args = ap.parse_args()

    if not os.path.isdir(args.change):
        err = {"error": "change_dir_not_found", "change": args.change}
        if args.json:
            print(json.dumps(err, ensure_ascii=False))
        else:
            print(f"[ERROR] 变更目录不存在: {args.change}", file=sys.stderr)
        return 2

    # P1-9：先记录横切执行（若有），再构建模型使其状态反映
    if args.mark_cross:
        ok = _stages.mark_cross_cutting(args.change, args.mark_cross)
        if not args.json:
            print(f"[{'ok' if ok else 'ERR'}] 横切执行记录 {'已写入' if ok else '失败'}：{args.mark_cross}")

    model = build_model(args.change, apply=args.apply,
                        allow_no_evidence=args.allow_no_evidence,
                        strict_cross=args.strict_cross)

    if args.json:
        print(json.dumps(model, ensure_ascii=False))
        if args.strict and not (model["closure"]["closed"]
                                and not model.get("cross_cutting_blocked")
                                and not model.get("shell_stages")):
            return 1
        return 0

    print(f"# 闭环推进：{args.change}\n")
    for st in model["stages"]:
        state = "已完成" if st["status"] == "done" else "待执行"
        alts_s = f"（备选：{', '.join(st['alternates'])}）" if st["alternates"] else ""
        print(f"[{state}] {st['dir']}  ({st['title']})")
        print(f"    调用：{st['skill']}  {alts_s}")
        arts = " / ".join(st["artifacts"])
        print(f"    期望产物：{arts}")
        print()

    print("--- 质量闭合判定（闭合度三问）---")
    closure = model["closure"]
    for q, a in closure["answers"].items():
        print(f"  [{q}] {a}")
    print()
    if closure["closed"]:
        print(">> 质量闭合：✅ 已闭合，可交付/归档。")
    else:
        print(">> 质量闭合：❌ 未闭合，禁止归档/上线。阻断项：")
        for b in closure["blockers"]:
            print(f"     - {b}")

    nxt = model["next"]
    if nxt and nxt.get("skill"):
        print(f"\n>> 下一步建议从 [{nxt['stage']}] 调用 {nxt['skill']} 开始。")
    elif nxt and nxt.get("note") == "all_stages_done_but_unclosed":
        print("\n>> 所有阶段已有产物，但质量未闭合，需先处置阻断项。")
    elif nxt and nxt.get("note") == "all_done_and_closed":
        print("\n>> 全部阶段已完成且质量闭合，可直接交付/归档。")

    # P1-9：横切关注点追踪提示
    xc = model.get("cross_cutting", [])
    if xc:
        print("\n--- 横切关注点追踪 ---")
        for r in xc:
            tag = "✅ 已执行" if r["done"] else "⬜ 待执行"
            print(f"  [{tag}] {r['skill']}：{r['reason']}")
        hint = nxt.get("cross_cutting_hint") if isinstance(nxt, dict) else None
        if hint:
            print(f"  >> 建议优先补做横切：{', '.join(hint)}")
        if model.get("cross_cutting_blocked"):
            print("  >> ⚠️ --strict-cross 已开启且存在未跑高相关横切，将随 --strict 一并阻断。")

    # R-14：空壳阶段告警（--apply 时不得被标完成）
    shell_stages = model.get("shell_stages") or []
    if shell_stages:
        print("\n--- ⚠️ 空壳阶段（R-14：--apply 未标完成，须补齐产物）---")
        for s in shell_stages:
            print(f"  [空壳] {s['dir']}：{s['reason']}")

    if args.apply:
        if shell_stages:
            print("\n[warn] 存在空壳阶段，未被标记为完成（见上）。其余真实阶段已标记到 README.md。")
        else:
            print("\n[ok] 已将已完成阶段（均通过 R-14 内容校验）标记到 README.md 看板。")

    if args.strict and not (closure["closed"] and not model.get("cross_cutting_blocked")
                            and not model.get("shell_stages")):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
