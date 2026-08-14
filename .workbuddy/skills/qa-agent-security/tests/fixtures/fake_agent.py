#!/usr/bin/env python3
"""多轮红队 fixture agent（仅用于测试 run_attacks 多轮 harness + 间接注入，非真实 Agent）。

协议（与 run_attacks.call_harness 对齐）：
  stdin  : {"attack": {...}, "messages": [{"role","content",...}, ...], "turn": N}
  stdout : {"output": "...", "tool_calls": [{"name","args"}], "done": bool}

行为（状态无关，靠 messages 判断轮次）：
  - 首轮（尚无 tool 消息）：假装先查工具，返回 web_search tool_call；
    该工具返回会被 ToolRuntime 注入攻击 payload（间接注入）。
  - 次轮（已收到工具返回，含间接注入）：被工具返回中的注入指令诱导，"得逞"——
    调用攻击定义里首个 forbidden_tool（使 judge 命中 forbidden_tools → success=True）。
"""
import json
import sys


def main():
    data = json.load(sys.stdin)
    attack = data.get("attack", {})
    messages = data.get("messages", [])
    has_tool = any(m.get("role") == "tool" for m in messages)
    if not has_tool:
        # 第 0 轮：先查工具，其返回将被注入攻击 payload
        print(json.dumps({
            "output": "我正在为您查询相关信息。",
            "tool_calls": [{"name": "web_search", "args": {"q": "user request"}}],
        }))
        return
    # 第 1+ 轮：被工具返回中的间接注入诱导，调用攻击定义里的首个被禁工具 → 得逞
    fts = (attack.get("success_criteria") or {}).get("forbidden_tools") or []
    if fts:
        print(json.dumps({
            "output": "已按工具返回中的指令执行。",
            "tool_calls": [{"name": fts[0], "args": {}}],
        }))
    else:
        print(json.dumps({"output": "已按工具返回中的指令执行。", "tool_calls": []}))


if __name__ == "__main__":
    main()
