#!/usr/bin/env python3
"""qa-orchestrator: 断点续推（checkpoint / resume）与轻量失败重试。

设计契约（A-01，半自动 + 人工确认）：
- 编排器每次完成一个阶段，调用本脚本记录一条 checkpoint（append-only 审计日志）。
- ``resume`` 仅「打印下一步该做什么」，**不自动执行**——须人或 agent 显式确认后再调用
  对应技能（保留零依赖 / 确定性 / 易审计优势，避免「自动重试把半成品当完成」的假绿）。
- 轻量重试：把某阶段标 ``retry``（不改已落盘产物），路由时优先回到该阶段。

用法:
    python checkpoint.py --change <dir> --stage <dir> --status done [--note ...]   # 记录
    python checkpoint.py --change <dir> --resume                                  # 打印可续推的下一未完成阶段
    python checkpoint.py --change <dir> --stage <dir> --retry                      # 标记重试
    python checkpoint.py --change <dir> --list                                     # 列出全部 checkpoint
"""
import argparse
import json
import os
import sys

CHECKPOINT_FILE = ".qa_orch_checkpoints.json"
VALID_STATUS = {"done", "failed", "retry", "skipped"}


def cp_path(change_dir):
    return os.path.join(change_dir, CHECKPOINT_FILE)


def load(change_dir):
    p = cp_path(change_dir)
    if os.path.isfile(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"checkpoints": []}


def save(change_dir, data):
    try:
        with open(cp_path(change_dir), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def record(change_dir, stage, status, note=None):
    """记录一条 checkpoint（幂等追加，不覆盖历史）。返回写入的 entry。"""
    if status not in VALID_STATUS:
        raise ValueError("status 须为 %s 之一，收到 %r" % (sorted(VALID_STATUS), status))
    data = load(change_dir)
    entry = {"stage": stage, "status": status, "note": note or ""}
    data["checkpoints"].append(entry)
    save(change_dir, data)
    return entry


def next_resume(change_dir, stages):
    """返回第一个未完成阶段 dir（按 stages 顺序）；无则 None。resume **不执行**。

    以每阶段「最新一次」checkpoint 状态为准：``done`` 优先于 ``retry``
    （阶段被重做并标记为 done 后，先前的 retry 不再抢占）。
    重试优先：最新状态为 ``retry`` 的阶段最先被建议回到（轻量重试契约）。
    """
    data = load(change_dir)
    latest = {}
    for c in data.get("checkpoints", []):
        latest[c["stage"]] = c.get("status")
    completed = {s for s, st in latest.items() if st == "done"}
    retry_set = {s for s, st in latest.items() if st == "retry"}
    for st in stages:
        d = st["dir"]
        if d in retry_set:
            return d
        if d not in completed:
            return d
    return None


def list_checkpoints(change_dir):
    return load(change_dir).get("checkpoints", [])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--change", required=True, help="变更目录")
    ap.add_argument("--stage", help="阶段目录名（记录 / 重试时用）")
    ap.add_argument("--status", help="状态: %s" % "/".join(sorted(VALID_STATUS)))
    ap.add_argument("--note", help="备注")
    ap.add_argument("--retry", action="store_true", help="标记某阶段重试（等价 --status retry）")
    ap.add_argument("--resume", action="store_true", help="打印下一可续推阶段（不执行）")
    ap.add_argument("--list", action="store_true", help="列出全部 checkpoint")
    ap.add_argument("--json", action="store_true", help="JSON 输出")
    args = ap.parse_args()

    if args.list:
        cps = list_checkpoints(args.change)
        if args.json:
            print(json.dumps({"checkpoints": cps}, ensure_ascii=False))
        else:
            for c in cps:
                print(f"  [{c.get('status')}] {c.get('stage')}  {c.get('note','')}")
        return 0

    if args.resume:
        # 延迟导入，避免 CLI 路径下硬依赖；测试可直接传 stages 调 next_resume
        import _stages
        stages = _stages.load_stages()
        nxt = next_resume(args.change, stages)
        if args.json:
            print(json.dumps({"resume_stage": nxt}, ensure_ascii=False))
        else:
            if nxt:
                print(f"[RESUME] 下一阶段（须人工/agent 确认后执行对应技能）: {nxt}")
            else:
                print("[RESUME] 所有阶段已完成，无需续推。")
        return 0

    if not args.stage:
        print("[ERROR] --stage 必填（resume/list 除外）", file=sys.stderr)
        return 2
    status = "retry" if args.retry else args.status
    if not status:
        print("[ERROR] 须提供 --status 或 --retry", file=sys.stderr)
        return 2
    try:
        entry = record(args.change, args.stage, status, args.note)
    except ValueError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(entry, ensure_ascii=False))
    else:
        print(f"[OK] checkpoint 已记录: {entry['stage']} = {entry['status']}（{entry['note']}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
