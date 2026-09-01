#!/usr/bin/env python3
"""
traffic_shadow.py: 工业级流量镜像与智能重放引擎 (Traffic Shadow & Replay Engine)
吸收 Keploy 核心思想，支持从网关日志或抓包流量中录制真实请求/响应基准快照 (Golden Snapshot)，
并在测试/隔离环境中执行零代码智能重放与 Diff 断言。

零外部重依赖，纯 Python 3.9+ 标准库实现。
"""
import os
import sys
import json
import urllib.request
import urllib.error
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple

if sys.platform == "win32":
    import io
    if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "buffer") and getattr(sys.stderr, "encoding", "").lower() != "utf-8":
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

class TrafficSnapshot:
    """流量基准快照数据结构"""
    def __init__(self, trace_id: str, method: str, url: str, headers: dict, body: any, resp_status: int, resp_body: any):
        self.trace_id = trace_id
        self.method = method.upper()
        self.url = url
        self.headers = headers or {}
        self.body = body
        self.resp_status = resp_status
        self.resp_body = resp_body

    def to_dict(self) -> dict:
        return {
            "trace_id": self.trace_id,
            "method": self.method,
            "url": self.url,
            "headers": self.headers,
            "body": self.body,
            "expected_response": {
                "status_code": self.resp_status,
                "body": self.resp_body
            }
        }

class TrafficRecorder:
    """流量录制与解析器"""
    @staticmethod
    def record_from_har(har_path: str) -> List[TrafficSnapshot]:
        har_data = json.loads(Path(har_path).read_text(encoding="utf-8"))
        entries = har_data.get("log", {}).get("entries", [])
        snapshots = []
        for i, e in enumerate(entries):
            req = e.get("request", {})
            resp = e.get("response", {})
            
            body_content = req.get("postData", {}).get("text", "")
            try:
                body_parsed = json.loads(body_content) if body_content else None
            except Exception:
                body_parsed = body_content

            resp_text = resp.get("content", {}).get("text", "")
            try:
                resp_parsed = json.loads(resp_text) if resp_text else None
            except Exception:
                resp_parsed = resp_text

            snapshots.append(TrafficSnapshot(
                trace_id=f"SNAP-{i+1:04d}",
                method=req.get("method", "GET"),
                url=req.get("url", ""),
                headers={h["name"]: h["value"] for h in req.get("headers", []) if h["name"].lower() not in ("cookie", "host")},
                body=body_parsed,
                resp_status=resp.get("status", 200),
                resp_body=resp_parsed
            ))
        return snapshots

class TrafficReplayer:
    """流量重放与断言引擎"""
    @staticmethod
    def diff_json(expected: any, actual: any, path: str = "$") -> List[str]:
        """递归对比 JSON 结构差异，忽略易变字段 (如 timestamp, token)"""
        diffs = []
        if isinstance(expected, dict) and isinstance(actual, dict):
            for k, v in expected.items():
                if k.lower() in ("timestamp", "created_at", "updated_at", "trace_id", "req_id", "token"):
                    continue
                if k not in actual:
                    diffs.append(f"字段缺失: {path}.{k}")
                else:
                    diffs.extend(TrafficReplayer.diff_json(v, actual[k], f"{path}.{k}"))
        elif isinstance(expected, list) and isinstance(actual, list):
            if len(expected) != len(actual):
                diffs.append(f"列表长度不一致: {path} (期望 {len(expected)}, 实际 {len(actual)})")
            for i, (ev, av) in enumerate(zip(expected[:5], actual[:5])):
                diffs.extend(TrafficReplayer.diff_json(ev, av, f"{path}[{i}]"))
        else:
            if expected != actual:
                diffs.append(f"值不匹配: {path} (期望 {expected}, 实际 {actual})")
        return diffs

    @staticmethod
    def replay_single(snapshot: TrafficSnapshot, target_base_url: str = None) -> Tuple[bool, List[str]]:
        url = snapshot.url
        if target_base_url:
            from urllib.parse import urlparse
            p = urlparse(url)
            endpoint = p.path + (f"?{p.query}" if p.query else "")
            url = target_base_url.rstrip("/") + "/" + endpoint.lstrip("/")

        req_headers = dict(snapshot.headers)
        data_bytes = None
        if snapshot.body is not None:
            if isinstance(snapshot.body, (dict, list)):
                data_bytes = json.dumps(snapshot.body).encode("utf-8")
                req_headers["Content-Type"] = "application/json"
            else:
                data_bytes = str(snapshot.body).encode("utf-8")

        req = urllib.request.Request(url, data=data_bytes, headers=req_headers, method=snapshot.method)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                status = resp.status
                content = resp.read().decode("utf-8", errors="replace")
                try:
                    actual_json = json.loads(content)
                except Exception:
                    actual_json = content
        except urllib.error.HTTPError as e:
            status = e.code
            try:
                actual_json = json.loads(e.read().decode("utf-8", errors="replace"))
            except Exception:
                actual_json = None
        except Exception as e:
            return False, [f"网络请求失败: {e}"]

        diffs = []
        if status != snapshot.resp_status:
            diffs.append(f"HTTP 状态码不匹配: 期望 {snapshot.resp_status}, 实际 {status}")
        
        if snapshot.resp_body is not None and actual_json is not None:
            body_diffs = TrafficReplayer.diff_json(snapshot.resp_body, actual_json)
            diffs.extend(body_diffs)

        return len(diffs) == 0, diffs

def main():
    parser = argparse.ArgumentParser(description="Traffic Shadow - 流量录制与智能重放引擎")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    p_rec = subparsers.add_parser("record", help="从 HAR 文件录制快照")
    p_rec.add_argument("--input", "-i", required=True, help="HAR 文件路径")
    p_rec.add_argument("--output", "-o", required=True, help="保存的基准快照 JSON 路径")

    p_rep = subparsers.add_parser("replay", help="重放基准快照并执行断言")
    p_rep.add_argument("--snapshots", "-s", required=True, help="基准快照 JSON 路径")
    p_rep.add_argument("--target", "-t", help="目标被测服务 Base URL (如 http://localhost:8000)")

    args = parser.parse_args()

    if args.command == "record":
        snaps = TrafficRecorder.record_from_har(args.input)
        out_p = Path(args.output)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(json.dumps([s.to_dict() for s in snaps], ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✅ 成功从 {args.input} 录制 {len(snaps)} 条流量基准快照 -> {args.output}")

    elif args.command == "replay":
        data = json.loads(Path(args.snapshots).read_text(encoding="utf-8"))
        print(f"🚀 开始重放 {len(data)} 条流量基准快照至目标: {args.target or '原始URL'}...\n")
        passed_cnt = 0
        for item in data:
            snap = TrafficSnapshot(
                trace_id=item["trace_id"],
                method=item["method"],
                url=item["url"],
                headers=item.get("headers", {}),
                body=item.get("body"),
                resp_status=item.get("expected_response", {}).get("status_code", 200),
                resp_body=item.get("expected_response", {}).get("body")
            )
            ok, diffs = TrafficReplayer.replay_single(snap, args.target)
            status_text = "✅ PASS" if ok else "❌ FAIL"
            print(f"[{snap.trace_id}] {snap.method} {snap.url} -> {status_text}")
            if not ok:
                for d in diffs:
                    print(f"  ⚠️ {d}")
            else:
                passed_cnt += 1

        print(f"\n📊 重放结果: {passed_cnt}/{len(data)} 条通过 (通过率: {passed_cnt/len(data)*100:.1f}%)")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
