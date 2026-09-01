#!/usr/bin/env python3
"""R-24 / S-03（V8）：契约一致性测试——所有 vendored `_common.py` 的 `emit_signal`
对同一输入必须产出逐字节一致的 `signals/<skill>.json`，防止契约漂移。

任一副本漂移 → 测试失败（CI 卡点）。这把「vendored 复制可能漂移」由口头约定
升级为可自动核验的硬门禁。
"""
import importlib.util
import json
import os
import sys
import tempfile

SKILLS_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMMON_CANDIDATES = [
    "qa-a11y", "qa-chaos", "qa-code-review", "qa-synthetic-monitoring", "qa-unit-tdd",
]


def load_common(skill):
    path = os.path.join(SKILLS_ROOT, skill, "scripts", "_common.py")
    if not os.path.isfile(path):
        raise SystemExit(f"[ERR] 找不到 {skill}/scripts/_common.py")
    spec = importlib.util.spec_from_file_location(f"_common_{skill}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    signals = [{"signal": "demo", "severity": "high", "count": 1,
                "blocking": True, "detail_ref": "x.md"}]
    normalized = {}
    for skill in COMMON_CANDIDATES:
        mod = load_common(skill)
        d = tempfile.mkdtemp()
        mod.emit_signal(skill, signals, d)
        p = os.path.join(d, f"{skill}.json")
        with open(p, "r", encoding="utf-8") as f:
            doc = json.load(f)
        # emit 内含 `generated_at`（实时时间戳）与 `source`（入参，即技能名）——
        # 二者均非 vendored 代码逻辑本身，归一化后再比对，仅校验 emit 逻辑与
        # signals/顶层结构是否逐字节一致（防 vendored 逻辑漂移）。
        doc["generated_at"] = "NORMALIZED"
        doc["source"] = "NORMALIZED"
        normalized[skill] = json.dumps(doc, sort_keys=True, ensure_ascii=False)

    ref = normalized[COMMON_CANDIDATES[0]]
    drift = [s for s in COMMON_CANDIDATES if normalized[s] != ref]
    if drift:
        print("[FAIL] vendored _common.py 契约漂移（source/signals/结构不一致）: " + ", ".join(drift))
        for s in drift:
            print(f"  {s} 与 {COMMON_CANDIDATES[0]} 的 emit 契约内容不一致")
        return 1

    check = json.loads(ref)
    expected_keys = {"source", "generated_at", "schema_version", "signals"}
    if set(check.keys()) != expected_keys or check.get("signals") != signals:
        print("[FAIL] emit 结构不符合信号契约 schema（缺 schema_version 或结构漂移）")
        return 1

    # RK-12/13：按 references/signal-schema.json（机器可读契约）真实验证 emit 产物，
    # 确保「文档=代码」（声明 vs 现实）而非仅肉眼比对。轻量校验器（不依赖 jsonschema 第三方）。
    schema_path = os.path.join(SKILLS_ROOT, "references", "signal-schema.json")
    if not os.path.isfile(schema_path):
        print("[FAIL] references/signal-schema.json 缺失，无法按机器可读契约校验")
        return 1
    schema = json.load(open(schema_path, "r", encoding="utf-8"))
    err = _validate_doc(check, schema)
    if err:
        print(f"[FAIL] emit 产物不符合 signal-schema.json: {err}")
        return 1

    print(f"[OK] {len(COMMON_CANDIDATES)} 份 vendored _common.py emit 契约内容（signals/结构/schema_version）"
          f"一致，且经 signal-schema.json 校验通过，无漂移")
    return 0


def _validate_doc(doc, schema):
    """轻量 JSON Schema 校验（仅 required/type/enum），避免引入第三方 jsonschema。"""
    for req in schema.get("required", []):
        if req not in doc:
            return f"缺必需字段 {req}"
    for k, sch in schema.get("properties", {}).items():
        if k in doc:
            v = doc[k]
            if sch.get("type") == "string" and not isinstance(v, str):
                return f"{k} 应为 string"
            if sch.get("type") == "array" and not isinstance(v, list):
                return f"{k} 应为 array"
            if "enum" in sch and v not in sch["enum"]:
                return f"{k}={v} 不在 enum {sch['enum']}"
    defs = schema.get("definitions", {}).get("signal", {})
    for sig in doc.get("signals", []):
        for req in defs.get("required", []):
            if req not in sig:
                return f"signal 缺必需字段 {req}"
        for k, sch in defs.get("properties", {}).items():
            if k in sig:
                v = sig[k]
                if sch.get("type") == "string" and not isinstance(v, str):
                    return f"signal.{k} 应为 string"
                if sch.get("type") == "integer" and not isinstance(v, int):
                    return f"signal.{k} 应为 integer"
                if sch.get("type") == "boolean" and not isinstance(v, bool):
                    return f"signal.{k} 应为 boolean"
                if "enum" in sch and v not in sch["enum"]:
                    return f"signal.{k}={v} 不在 enum {sch['enum']}"
    return None


if __name__ == "__main__":
    sys.exit(main())
