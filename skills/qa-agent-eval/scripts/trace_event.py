#!/usr/bin/env python3
"""qa-agent-eval: 结构化事件流（W3 增强）。

把 Agent 评测 / 运行的 trace 升级为「结构化事件流」：每次工具调用、状态写入、模型重试、
任务结束都成为一条带类型与上下文的事件，关联 Run ID / 步骤 / 参数 / 上下游，支撑：
  - 可重放（replay 按序还原执行过程）；
  - 失败分类（模型重试次数、任务终态归因）。

事件类型（EVENT_TYPES）：
  tool_call    工具调用（参数 / 返回）
  state_write  状态写入（被测系统 / 记忆）
  model_retry  模型重试（含原因）
  task_end     任务结束（含终态 success / fail / 超时）

用法:
    python trace_event.py --append --trace t.json --run-id R1 --step 1 --type tool_call \
        --params '{"tool":"search","args":{...}}' [--upstream E0]
    python trace_event.py --replay --trace t.json            # 打印有序事件
    python trace_event.py --classify --trace t.json          # 失败分类摘要
"""
import argparse
import json
import os
import sys
import uuid

EVENT_TYPES = ["tool_call", "state_write", "model_retry", "task_end"]


class Event:
    def __init__(self, run_id, step, type, params=None, upstream=None,
                 downstream=None, event_id=None, ts=None):
        if type not in EVENT_TYPES:
            raise ValueError("type 须为 %s 之一，收到 %r" % (EVENT_TYPES, type))
        self.event_id = event_id or ("E" + uuid.uuid4().hex[:8])
        self.run_id = run_id
        self.step = step
        self.type = type
        self.params = params or {}
        self.upstream = upstream
        self.downstream = downstream
        self.ts = ts

    def to_dict(self):
        return {
            "event_id": self.event_id,
            "run_id": self.run_id,
            "step": self.step,
            "type": self.type,
            "params": self.params,
            "upstream": self.upstream,
            "downstream": self.downstream,
            "ts": self.ts,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(event_id=d.get("event_id"), run_id=d.get("run_id"),
                   step=d.get("step"), type=d.get("type"), params=d.get("params"),
                   upstream=d.get("upstream"), downstream=d.get("downstream"),
                   ts=d.get("ts"))


def load_trace(path):
    if not os.path.isfile(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [Event.from_dict(e) for e in data.get("events", [])]
    except Exception:
        return []


def save_trace(path, events):
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"events": [e.to_dict() for e in events]}, f,
                  ensure_ascii=False, indent=2)


def append_event(path, event):
    events = load_trace(path)
    # 维护上下游链：若未指定 upstream，则上游为同 run 的最后一个事件
    if event.upstream is None and events:
        event.upstream = events[-1].event_id
    events.append(event)
    save_trace(path, events)
    return event


def replay(path):
    """按记录顺序返回事件列表（事件流本身有序，此处做规范化）。"""
    return load_trace(path)


def classify_failures(path):
    """失败分类：模型重试次数、任务终态分布。"""
    events = load_trace(path)
    retries = [e for e in events if e.type == "model_retry"]
    ends = [e for e in events if e.type == "task_end"]
    terminal = {}
    for e in ends:
        st = (e.params or {}).get("status", "unknown")
        terminal[st] = terminal.get(st, 0) + 1
    return {
        "n_events": len(events),
        "types": sorted({e.type for e in events}),
        "model_retries": len(retries),
        "task_terminal": terminal,
    }


def import_trace(path, run_id=None):
    """G-02：把通用 agent 轨迹（非本项目合成 harness）转换为结构化 Event 模型。

    自动探测两种常见格式：
      1) OpenTelemetry-like spans:
         {"spans":[{"span_id","parent_span_id","name","start_time","end_time",
                    "attributes":{"tool","args"}}]}
      2) agentdojo-like trajectory（步骤元组列表）:
         {"trajectory":[["user",text],["assistant",text],
                        ["tool_call",{"name","args"}],["tool_result",obs],
                        ["final",answer]]}
       或直接一个步骤列表（list of [type, payload]）。

    转换规则（确定性，不实际运行 agent）：
      - 工具调用 → tool_call（params={tool,args}）
      - 工具返回/观测/状态 → state_write（params={observation}）
      - 模型生成/助手回复 → state_write（kind=model，不冒充 model_retry）
      - 终态/收尾 → task_end（params={status}）
      - 名称含 retry 的 span → model_retry
    上下游链按出现顺序串联（每事件 upstream=上一事件 event_id）。
    空文件/解析失败返回 []。
    """
    if not os.path.isfile(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return []
    events = []
    prev_id = None

    def _mk(ev_type, params, step):
        nonlocal prev_id
        ev = Event(run_id=run_id or "imported", step=step, type=ev_type,
                   params=params or {}, upstream=prev_id)
        prev_id = ev.event_id
        events.append(ev)
        return ev

    def _span_type(name):
        n = (name or "").lower()
        if "retry" in n:
            return "model_retry"
        if "tool" in n or "call" in n:
            return "tool_call"
        if "end" in n or "final" in n or "finish" in n:
            return "task_end"
        return "state_write"

    if isinstance(data, dict) and "spans" in data:
        spans = sorted(data["spans"], key=lambda s: s.get("start_time") or "")
        for i, s in enumerate(spans, 1):
            t = _span_type(s.get("name", ""))
            params = {}
            if t == "tool_call":
                attrs = s.get("attributes", {}) or {}
                params = {"tool": attrs.get("tool", s.get("name")),
                          "args": attrs.get("args", {})}
            elif t == "task_end":
                params = {"status": "done"}
            _mk(t, params, i)
    else:
        traj = data.get("trajectory") if isinstance(data, dict) else data
        if not isinstance(traj, list):
            traj = []
        for i, entry in enumerate(traj, 1):
            if not isinstance(entry, (list, tuple)) or len(entry) < 2:
                _mk("state_write", {"raw": entry}, i)
                continue
            kind, payload = entry[0], entry[1]
            k = str(kind).lower()
            if k in ("tool_call", "tool"):
                p = payload if isinstance(payload, dict) else {}
                _mk("tool_call", {"tool": p.get("name"), "args": p.get("args", {})}, i)
            elif k in ("tool_result", "observation", "state", "result"):
                _mk("state_write", {"observation": payload}, i)
            elif k in ("final", "task_end", "end"):
                _mk("task_end", {"status": "done"}, i)
            else:  # user / assistant / model / 其它 → 状态写入（含模型生成）
                _mk("state_write", {"kind": k, "content": payload}, i)
    return events


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trace", required=True, help="trace 文件路径（JSON）")
    ap.add_argument("--import-trace", default=None,
                    help="G-02: 读入通用轨迹（OTel spans / agentdojo trajectory）并转为本项目事件格式")
    ap.add_argument("--out", default=None, help="写出路径（import-trace 转换产物）")
    ap.add_argument("--append", action="store_true", help="追加一条事件")
    ap.add_argument("--replay", action="store_true", help="打印有序事件")
    ap.add_argument("--classify", action="store_true", help="输出失败分类摘要")
    ap.add_argument("--run-id", help="Run ID")
    ap.add_argument("--step", type=int, default=0, help="步骤序号")
    ap.add_argument("--type", help="事件类型: " + "/".join(EVENT_TYPES))
    ap.add_argument("--params", help="参数 JSON")
    ap.add_argument("--upstream", help="上游 event_id")
    ap.add_argument("--downstream", help="下游 event_id")
    args = ap.parse_args()

    if args.import_trace:
        evs = import_trace(args.import_trace, run_id=args.run_id)
        out = args.out or (args.import_trace + ".converted.json")
        save_trace(out, evs)
        print("[OK] 导入 %d 条事件 → %s" % (len(evs), out))
        return 0

    if args.append:
        if not args.type:
            print("[ERROR] --type 必填", file=sys.stderr)
            return 2
        params = {}
        if args.params:
            try:
                params = json.loads(args.params)
            except Exception as e:
                print(f"[ERROR] --params 非法 JSON: {e}", file=sys.stderr)
                return 2
        ev = Event(run_id=args.run_id or "", step=args.step, type=args.type,
                   params=params, upstream=args.upstream, downstream=args.downstream)
        append_event(args.trace, ev)
        print(f"[OK] 事件已追加: {ev.event_id}（type={ev.type}, run={ev.run_id}）")
        return 0

    if args.classify:
        summary = classify_failures(args.trace)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    # 默认：replay
    events = replay(args.trace)
    for e in events:
        print(json.dumps(e.to_dict(), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
