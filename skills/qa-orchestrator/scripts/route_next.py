#!/usr/bin/env python3
"""qa-orchestrator: 扫描变更目录，自动推断「下一步该调哪个 qa-* 技能」。

用法:
    python route_next.py --change changes/<slug> [--auto] [--json]

逻辑：按 stages.json 生命周期顺序检查各阶段目录产物是否齐备（非空且命中期望产物），
返回第一个未完成阶段对应的推荐技能。阶段定义来自 stages.json（单一事实源，修复 P0-B）。
- `--auto`：只打印技能名（供代理直接调用）。
- `--json`：打印结构化结果 {stage, skill, reason, alternates}。
"""
import argparse
import json
import os
import sys

import _stages

STAGES = _stages.resolve_stages()  # W7：默认 domain_extensions 为空 → 与 load_stages() 一致


def skills_root():
    """推导技能根目录（本脚本位于 <root>/qa-orchestrator/scripts/）。"""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(os.path.dirname(here))


def resolve_skill(stage):
    """解析可用技能：主技能目录缺失时回退到第一个存在的备选；都不存在则判 blocked。

    返回 (skill, fallback, blocked, note)。
    """
    primary = stage["skills"][0]
    alts = stage.get("alternates", [])
    candidates = [primary] + list(alts)
    for cand in candidates:
        if os.path.isdir(os.path.join(skills_root(), cand)):
            return cand, (cand != primary), False, None
    return None, False, True, "no_usable_skill_dir"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--change", required=True, help="变更目录（changes/<slug>）")
    ap.add_argument("--auto", action="store_true", help="只输出技能名")
    ap.add_argument("--json", action="store_true", help="JSON 输出")
    ap.add_argument("--max-steps", type=int, default=20,
                    help="编排循环上限（默认 20），超过则判 BLOCKED 防死循环/阶段卡死")
    args = ap.parse_args()

    if not os.path.isdir(args.change):
        err = {"error": "change_dir_not_found", "change": args.change}
        if args.json:
            print(json.dumps(err, ensure_ascii=False))
        else:
            print(f"[ERROR] 变更目录不存在: {args.change}", file=sys.stderr)
        return 2

    # P1-9：横切关注点推荐（按变更特征触发，与 8 阶段并行提示，不阻塞主流程）
    xc = _stages.recommend_cross_cutting(args.change, STAGES)

    # P0-A：编排步数守卫——超过上限即 BLOCKED，防外部驱动循环死循环/阶段卡死
    orch_st, orch_blocked = _stages.bump_step(args.change, args.max_steps)
    if orch_blocked:
        result = {"stage": None, "skill": None, "blocked": True,
                  "reason": "max_steps_exceeded", "cross_cutting_recommend": xc,
                  "step": orch_st["step"], "max_steps": args.max_steps}
        if args.auto:
            print("BLOCKED")
        elif args.json:
            print(json.dumps(result, ensure_ascii=False))
        else:
            print(f"⚠️ 编排步数超过上限 {args.max_steps}（已达 {orch_st['step']}），"
                  f"疑似阶段卡死/死循环，请检查各阶段产物文件名是否匹配 stages.json 契约。")
        return 1

    for st in STAGES:
        sd = os.path.join(args.change, st["dir"])
        if not _stages.is_stage_done(sd, st):
            reason = (f"阶段 {st['dir']} 产物缺失或为空"
                      if not st.get("optional")
                      else f"阶段 {st['dir']} 尚未准备测试数据（可选）")
            # P0-A：契约驱动——目录有非空产物但无一命中 stages.json 声明的 artifacts
            #（非可选阶段）→ 文件名契约不符，阻塞而非静默重复，避免黑洞
            has_out, actual_files = _stages.stage_dir_has_output(sd)
            if has_out and not st.get("optional"):
                result = {"stage": st["dir"], "skill": None, "blocked": True,
                          "reason": "artifact_mismatch", "cross_cutting_recommend": xc,
                          "actual_files": actual_files,
                          "expected_artifacts": st.get("artifacts", [])}
                if args.auto:
                    print("BLOCKED")
                elif args.json:
                    print(json.dumps(result, ensure_ascii=False))
                else:
                    print(f"⚠️ 阶段 {st['dir']} 目录存在产物但文件名未命中 stages.json 契约：")
                    print(f"    实际文件：{', '.join(actual_files)}")
                    print(f"    期望产物：{' / '.join(st.get('artifacts', []))}")
                    print(f"    请核对技能输出文件名，避免阶段永远判未完成（黑洞）。")
                    _print_xc(xc)
                return 1
            skill, fallback, blocked, note = resolve_skill(st)
            alts = st.get("alternates", [])
            if blocked:
                result = {"stage": st["dir"], "skill": None, "blocked": True,
                          "reason": "no_usable_skill_dir", "cross_cutting_recommend": xc,
                          "alternates": alts}
                if args.auto:
                    print("BLOCKED")
                elif args.json:
                    print(json.dumps(result, ensure_ascii=False))
                else:
                    print(f"⚠️ 阶段 {st['dir']} 无可用技能目录（主技能与备选均缺失），请检查技能安装。")
                    if alts:
                        print(f"   期望技能：{primary_hint(st)}；备选：{', '.join(alts)}")
                    _print_xc(xc)
                return 1
            result = {"stage": st["dir"], "skill": skill, "reason": reason,
                      "alternates": alts, "fallback": fallback,
                      "cross_cutting_recommend": xc}
            if args.auto:
                print(skill)
            elif args.json:
                print(json.dumps(result, ensure_ascii=False))
            else:
                print(f"下一步推荐技能：{skill}")
                print(f"  阶段：{st['dir']}")
                print(f"  原因：{reason}")
                if fallback:
                    print(f"  ⚠️ 主技能不可用，已回退到备选技能。")
                if alts:
                    print(f"  备选：{', '.join(alts)}")
                _print_xc(xc)
            return 0

    msg = "全部阶段已完成，可交付/归档。"
    if args.auto:
        print("DONE")
    elif args.json:
        print(json.dumps({"stage": None, "skill": None, "reason": msg,
                          "alternates": [], "cross_cutting_recommend": xc},
                          ensure_ascii=False))
    else:
        print(msg)
        _print_xc(xc)
    return 0


def _print_xc(xc):
    """human 路径打印横切关注点推荐（JSON / --auto 不打印，避免破坏代理契约）。"""
    if not xc:
        return
    print("\n— 横切关注点建议（根据变更特征触发，按需在阶段间隙执行）—")
    for r in xc:
        print(f"  • {r['skill']}：{r['reason']}")


def primary_hint(stage):
    return stage["skills"][0]


if __name__ == "__main__":
    sys.exit(main())
