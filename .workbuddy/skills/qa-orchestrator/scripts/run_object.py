#!/usr/bin/env python3
"""qa-orchestrator: Run 对象生命周期模型（W3 增强）。

把「一次测试 / 一次变更推进」建模为 Run，承载运行态元数据，使编排从「目录产物状态机」
升级为「Run 对象 + 事件流」的可重放架构。

核心原则（W3，企业架构研究会）：
  **协议层（MCP / CLI / API）不能代替运行架构。** 协议只是交互面；Run 对象才是执行态的
  真实载体——超时、取消、重试、重放、配置覆盖都发生在 Run 层，而非协议层。

Run 字段：
  run_id, model, prompt_version, tool_versions(dict), timeout, config(dict), status
方法：
  cancel() / retry() / apply_config_override(override) / replay(events)
状态机：created → running → {cancelled | retried | done}，replay 标记 replayed。
⚠️ replay 是「标记该 Run 可被重放还原（按事件流还原执行过程）」的**元数据动作**，
并不重新执行底层任务——重放的是**记录**，不是真实运行。真正需要重跑请用 retry（标记待重做）
或重新发起一次新 Run。
"""
import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone

STATUS = ["created", "running", "cancelled", "retried", "replayed", "done"]
_RUN_FIELDS = ("run_id", "model", "prompt_version", "tool_versions",
               "timeout", "config", "status", "history")


class Run:
    def __init__(self, run_id=None, model="", prompt_version="", tool_versions=None,
                 timeout=0, config=None, status="created"):
        self.run_id = run_id or ("run-" + uuid.uuid4().hex[:12])
        self.model = model
        self.prompt_version = prompt_version
        self.tool_versions = dict(tool_versions or {})
        self.timeout = timeout
        self.config = dict(config or {})
        self.status = status if status in STATUS else "created"
        self.history = []

    # —— 生命周期动作（均记入 history，确定性、可审计）——
    def cancel(self):
        self.status = "cancelled"
        self._log("cancel")
        return self

    def retry(self):
        self.status = "retried"
        self._log("retry")
        return self

    def apply_config_override(self, override):
        self.config.update(override)
        self._log("config_override", override)
        return self

    def replay(self, events=None):
        self.status = "replayed"
        self._log("replay", {"n_events": len(events or [])})
        return self

    def _log(self, action, payload=None):
        self.history.append({
            "action": action,
            "payload": payload,
            "ts": datetime.now(timezone.utc).isoformat(),
        })

    def to_dict(self):
        return {k: getattr(self, k) for k in _RUN_FIELDS}

    @classmethod
    def from_dict(cls, d):
        r = cls(run_id=d.get("run_id"), model=d.get("model", ""),
                prompt_version=d.get("prompt_version", ""),
                tool_versions=d.get("tool_versions") or {},
                timeout=d.get("timeout", 0), config=d.get("config") or {},
                status=d.get("status", "created"))
        r.history = d.get("history") or []
        return r


def write_run(run, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(run.to_dict(), f, ensure_ascii=False, indent=2)
    return path


def read_run(path):
    with open(path, "r", encoding="utf-8") as f:
        return Run.from_dict(json.load(f))


def _parse_kv(text):
    """解析 'k=v,k2=v2' 为 dict（CLI 传参用）。"""
    out = {}
    for part in (text or "").split(","):
        part = part.strip()
        if not part:
            continue
        if "=" in part:
            k, v = part.split("=", 1)
            out[k.strip()] = v.strip()
        else:
            out[part] = ""
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-json", help="已有 Run 文件路径（cancel/retry/override/replay 用）")
    ap.add_argument("--new", action="store_true", help="新建 Run")
    ap.add_argument("--run-id", help="显式 run_id（--new 时）")
    ap.add_argument("--model", default="", help="模型标识")
    ap.add_argument("--prompt", default="", help="prompt / 版本标识")
    ap.add_argument("--tools", default="", help="工具版本 k=v,k2=v2")
    ap.add_argument("--timeout", type=int, default=0, help="超时（秒）")
    ap.add_argument("--config", default="", help="配置 k=v,k2=v2")
    ap.add_argument("--cancel", action="store_true")
    ap.add_argument("--retry", action="store_true")
    ap.add_argument("--override", help="配置覆盖 k=v,k2=v2")
    ap.add_argument("--replay", action="store_true")
    ap.add_argument("--out", help="写出路径（--new 时默认 ./run.json）")
    ap.add_argument("--json", action="store_true", help="JSON 输出当前 Run")
    args = ap.parse_args()

    run = None
    if args.new:
        run = Run(run_id=args.run_id, model=args.model, prompt_version=args.prompt,
                  tool_versions=_parse_kv(args.tools), timeout=args.timeout,
                  config=_parse_kv(args.config))
        out = args.out or "run.json"
        write_run(run, out)
        if args.json:
            print(json.dumps(run.to_dict(), ensure_ascii=False))
        else:
            print(f"[OK] 新建 Run: {run.run_id} → {out}")
        return 0

    if not args.run_json:
        print("[ERROR] 须提供 --new 或 --run-json", file=sys.stderr)
        return 2
    run = read_run(args.run_json)
    if args.cancel:
        run.cancel()
    if args.retry:
        run.retry()
    if args.override:
        run.apply_config_override(_parse_kv(args.override))
    if args.replay:
        run.replay()
    write_run(run, args.run_json)
    if args.json:
        print(json.dumps(run.to_dict(), ensure_ascii=False))
    else:
        print(f"[OK] Run {run.run_id} 状态={run.status}（动作已记入 history）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
