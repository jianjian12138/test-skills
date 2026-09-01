#!/usr/bin/env python3
"""对 Agent 轨迹(trace)做长程崩溃模式归因（**启发式诊断，非门禁**）。

⚠️ 性质说明（R-13）：本工具是**启发式诊断**，**不是 pass/fail 门禁**。
检测基于 4 类关键词正则（goal_drift / loop / halt / tool_misuse），可被改写/重写绕过，
且命中即"疑似"而非"确诊"。因此：
  - 输出**不得**被解读为"轨迹健康=通过"；
  - 真正的阻断门禁是 `grade_run.py` 的 expected_action 不匹配 / high_risk 单独门禁；
  - 本工具输出（尤其 loop / halt）作为**可解释性补充**，供人工或 grade_run 高风险评估参考。
"""
import argparse, json, re, sys

PATTERNS = {
    "goal_drift": [r"偏离了原目标", r"忘了.*任务", r"we need to focus on", r"actually let's", r"忽略"],
    "loop": [r"(.+)\n\1\n\1", r"重复执行", r"same action", r"again and again"],
    "halt": [r"无法继续", r"我不确定", r"cannot proceed", r"i (?:can|will) ?not", r"停止", r"give up"],
    "tool_misuse": [r"调用了错误工具", r"wrong tool", r"参数错误", r"invalid argument", r"误用"],
}


def detect(text):
    found = {}
    # R-46：单次匹配即可（re.IGNORECASE 已覆盖大小写），移除对 lower 副本的二次 finditer，
    # 原实现靠 set 去重掩盖冗余——现直接单次匹配，无重复。
    for mode, pats in PATTERNS.items():
        hits = []
        for p in pats:
            for m in re.finditer(p, text, re.IGNORECASE):
                hits.append(m.group(0))
        if hits:
            found[mode] = sorted(set(hits))[:5]
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trace", required=True, help="trace 文本文件，或用 - 从 stdin")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    if args.trace == "-":
        text = sys.stdin.read()
    else:
        with open(args.trace, encoding="utf-8") as f:
            text = f.read()
    res = detect(text)
    if args.json:
        print(json.dumps({"collapse_modes": res, "has_collapse": bool(res),
                          "note": "启发式诊断，非门禁：命中仅=疑似，不得解读为轨迹健康=通过"},
                         ensure_ascii=False, indent=2))
    else:
        if res:
            print("检测到崩溃模式:", ", ".join(res.keys()))
            for k, v in res.items():
                print("  - %s: %s" % (k, v))
        else:
            print("未检测到已知崩溃模式（无可疑长程崩溃信号；非健康背书）")
        # R-13：运行时强提示——本工具是启发式诊断，非 pass/fail 门禁
        print("\n⚠️ [启发式诊断·非门禁] 上述结果基于关键词正则，可被改写绕过、命中=疑似而非确诊；"
              "真正阻断门禁是 grade_run.py 的 expected_action 不匹配 / high_risk 单独门禁。"
              "请勿据本输出判『轨迹健康=通过』。")


if __name__ == "__main__":
    main()
