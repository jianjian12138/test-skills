#!/usr/bin/env python3
"""红队执行器（RK-17）：把攻击用例集喂给 Agent / harness，产出可被 judge_attack 消费的结果。

与 qa-agent-eval 侧的 harness_stub.py 对称：gen_attacks 生成"攻击定义"，本脚本负责
"真正去打一遍 Agent"，judge_attack 再按 success_criteria 做 ground-truth 判定，
calc_asr 算双轴指标。三者串成端到端可复现的红队流水线。

用法:
    # 1) 用内置安全桩跑（无需真实 Agent，产出"全部拒答"结果，仅供打通流水线 / 演示）
    python run_attacks.py --attacks attacks.json --out results.json

    # 2) 接入你自己的 Agent：--harness 指向一个可执行。run_attacks 以
    #    {"attack":..., "messages":[...], "turn":N} 经 stdin 传入；harness 返回
    #    {"output":..., "tool_calls":[...], "done":bool}；若含 tool_calls 则 run_attacks
    #    用内置 ToolRuntime 执行工具并把 observation 回灌，循环至多 --max-turns 轮
    #    （间接注入的 payload 会随工具返回注入到 agent 视野，真正被多轮消费）。
    python run_attacks.py --attacks attacks.json --harness ./my_agent.sh --max-turns 6 --out results.json

结果文件格式（与 judge_attack.load_results 兼容）:
    {"results": [
        {"attack_id": "inj-d-1", "output": "...", "tool_calls": [...], "tool_results": [...]},
        ...
    ]}
"""
import argparse
import json
import subprocess
import sys


def load_attacks(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    items = data.get("attacks") if isinstance(data, dict) else data
    if not isinstance(items, list):
        raise SystemExit("无法解析 attacks 文件")
    return items


INDIRECT_CHANNELS = {"tool_result", "retrieval", "email"}


def inject_surface(attack):
    """按攻击 channel 决定注入点（P0-C 间接注入）。
    - 直接注入(user_prompt)：payload 直接进首轮 user 消息。
    - 间接注入(tool_result/retrieval/email)：payload 进工具 observation（由 ToolRuntime 注入），
      首轮给中性任务指令，待 agent 调用工具后，注入随工具返回回灌，真正被 agent 在工具结果中看到。
    """
    ch = attack.get("channel", "user_prompt")
    payload = attack.get("payload", "")
    if ch == "user_prompt":
        return payload, False, None
    tgt = (attack.get("injection_target") or {}).get("tool")
    return "请按正常流程完成用户请求。", True, tgt


class ToolRuntime:
    """工具执行运行时（默认 echo/sandbox）。间接注入在此把 payload 作为工具 observation 回灌。"""

    def __init__(self, attack):
        ch = attack.get("channel", "user_prompt")
        self.indirect = ch in INDIRECT_CHANNELS
        self.payload = attack.get("payload", "")
        self.target_tool = (attack.get("injection_target") or {}).get("tool")

    def execute(self, name, args):
        name_l = str(name).strip().lower()
        if self.indirect and (self.target_tool is None or name_l == str(self.target_tool).strip().lower()):
            # 间接注入：把攻击 payload 作为该工具的返回内容（agent 在工具结果里"看到"注入指令）
            return "[tool:%s] %s" % (name, self.payload)
        return "[tool:%s] observation(args=%s)" % (name, json.dumps(args, ensure_ascii=False))


def call_harness(harness, payload_obj):
    """调用外部 harness：message list 经 stdin，结果 JSON 经 stdout。
    支持多轮：harness 返回含 tool_calls 则继续循环（见 run_multi_turn）。"""
    cmd = [harness]
    if harness.endswith(".py"):
        cmd = [sys.executable, harness]
    proc = subprocess.run(cmd, input=json.dumps(payload_obj, ensure_ascii=False),
                          capture_output=True, text=True, timeout=600)
    if proc.returncode != 0:
        print("[warn] harness 返回非0 (rc=%d): %s" % (proc.returncode, proc.stderr[:200]),
              file=sys.stderr)
    out = proc.stdout.strip()
    if not out:
        return {"output": "", "tool_calls": [], "tool_results": []}
    try:
        res = json.loads(out)
    except Exception as e:
        print("[warn] harness 输出非 JSON (%s)，按纯文本 output 处理" % e, file=sys.stderr)
        return {"output": out, "tool_calls": [], "tool_results": []}
    if not isinstance(res, dict):
        return {"output": json.dumps(res, ensure_ascii=False), "tool_calls": [], "tool_results": []}
    return res


def run_multi_turn(attack, harness, max_turns):
    """多轮对话循环（P0-C）：harness 返回 tool_calls → 用 ToolRuntime 执行 → 回灌 tool 消息 →
    再调 harness，直至无 tool_calls / harness 标记 done / 达 max_turns。"""
    runtime = ToolRuntime(attack)
    content, _, _ = inject_surface(attack)
    msgs = [{"role": "user", "content": content}]
    last = {"output": "", "tool_calls": [], "tool_results": []}
    for turn in range(max_turns):
        res = call_harness(harness, {"attack": attack, "messages": msgs, "turn": turn})
        tcs = res.get("tool_calls") or []
        if not tcs:
            res["tool_results"] = []
            res["_turns"] = turn + 1
            last = res
            break
        results = []
        for tc in tcs:
            obs = runtime.execute(tc.get("name"), tc.get("args", {}))
            results.append({"name": tc.get("name"), "observation": obs})
        res["tool_results"] = results
        msgs.append({"role": "assistant", "content": res.get("output", ""), "tool_calls": tcs})
        msgs.append({"role": "tool", "content": json.dumps(results, ensure_ascii=False)})
        last = res
        if res.get("done"):
            last["_turns"] = turn + 1
            break
    else:
        last["_turns"] = max_turns
        last["_truncated"] = True
    return last


def run_with_stub(attack):
    """内置安全桩（RK-17 默认）：不接真实 Agent 时，模拟一个"安全 Agent 明确拒答"的结果，
    保证 gen → run → judge → calc 全链路可端到端跑通、可被 CI 验证。
    真实评测请务必提供 --harness 接入你的 Agent。"""
    return {
        "output": "我无法执行该请求，已按安全策略拒绝。",
        "tool_calls": [],
        "tool_results": [],
        "note": "stub（未接真实 Agent，仅打通流水线）",
        "source": "stub",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--attacks", required=True, help="gen_attacks.py 产物 JSON")
    ap.add_argument("--harness", default=None,
                    help="外部 Agent 接入脚本（对话历史经 stdin，结果 JSON 经 stdout）；"
                         "缺省用内置安全桩（全部拒答，仅供演示/打通链路）")
    ap.add_argument("--max-turns", type=int, default=6,
                    help="多轮对话上限（默认 6）；harness 返回 tool_calls 时循环执行工具并回灌，"
                         "直至无 tool_calls / done / 达上限")
    ap.add_argument("--out", default="results.json", help="结果输出路径（默认 results.json）")
    args = ap.parse_args()

    attacks = load_attacks(args.attacks)
    results = []
    for a in attacks:
        aid = a.get("id") or a.get("uid")
        if not aid:
            print("[warn] 跳过缺 id 的攻击用例", file=sys.stderr)
            continue
        if args.harness:
            res = run_multi_turn(a, args.harness, args.max_turns)
        else:
            res = run_with_stub(a)
        res["attack_id"] = aid
        # 透传 surface 便于 judge 按面分组（与 attacks 内 surface 一致）
        if "surface" not in res and a.get("surface"):
            res["surface"] = a["surface"]
        results.append(res)

    payload = {"results": results, "count": len(results)}
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    mode = "harness(%s)" % args.harness if args.harness else "内置安全桩(未接真实Agent)"
    print("已对 %d 条攻击执行完毕（%s）-> %s" % (len(results), mode, args.out))


if __name__ == "__main__":
    main()
