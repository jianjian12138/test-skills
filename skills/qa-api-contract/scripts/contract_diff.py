#!/usr/bin/env python3
"""OpenAPI 契约比对：识别破坏性变更（Breaking Change）并卡 CI。

Usage:
    python scripts/contract_diff.py --old old.json --new new.json --out report.md [--fail-on]
    python scripts/contract_diff.py --old old.json --new new.json --out report.md --rules   # 打印规则清单

规则总览见 RULES 常量（当前 35 条：BREAKING 27 / WARN 8），`--rules` 可打印。
支持本地 `$ref`（`#/components/schemas/X`）解析，带循环引用保护。
远程 `$ref`（http:// 或 other-file.yaml#/...）不解析，会记为 WARN «无法解析的外部引用»。

输入为 OpenAPI 3.x 的 JSON 形式（YAML 请先转 JSON，技能保持零外部依赖）。
"""
import argparse
import json
import os
import sys
from datetime import datetime

# ---------------------------------------------------------------- 规则清单
RULES = [
    # (编号, 级别, 说明)
    ("R01", "BREAKING", "端点删除（path 从 old 消失）"),
    ("R02", "BREAKING", "操作删除（path 下的 get/post/... 消失）"),
    ("R03", "BREAKING", "必填参数删除"),
    ("R04", "WARN", "可选参数删除"),
    ("R05", "BREAKING", "参数由可选变必填"),
    ("R06", "BREAKING", "参数位置变更（query→header 等）"),
    ("R07", "BREAKING", "参数类型变更"),
    ("R08", "BREAKING", "参数 format 收窄（int64→int32、double→float）"),
    ("R09", "BREAKING", "参数枚举值删除"),
    ("R10", "BREAKING", "新增必填参数"),
    ("R11", "BREAKING", "参数约束收紧（maxLength↓ / minLength↑ / maximum↓ / minimum↑ / pattern 变更）"),
    ("R12", "BREAKING", "请求体新增必填属性"),
    ("R13", "BREAKING", "请求体属性由可选变必填"),
    ("R14", "BREAKING", "请求体属性类型变更"),
    ("R15", "BREAKING", "请求体 content-type 删除"),
    ("R16", "BREAKING", "请求体整体由可选变必填"),
    ("R17", "BREAKING", "请求体属性约束收紧"),
    ("R18", "BREAKING", "additionalProperties 由 true 收紧为 false"),
    ("R19", "WARN", "请求体属性删除"),
    ("R20", "BREAKING", "响应字段删除"),
    ("R21", "BREAKING", "响应字段类型变更"),
    ("R22", "BREAKING", "响应字段由必填变可选"),
    ("R23", "BREAKING", "成功状态码(2xx)删除"),
    ("R24", "BREAKING", "响应 header 删除"),
    ("R25", "WARN", "响应枚举值新增（老客户端可能未覆盖分支）"),
    ("R26", "BREAKING", "nullable 由 true 收紧为 false"),
    ("R27", "BREAKING", "oneOf / anyOf 分支删除"),
    ("R28", "WARN", "oneOf / anyOf 分支新增"),
    ("R29", "BREAKING", "安全方案新增（原本免鉴权的接口现在要鉴权）"),
    ("R30", "BREAKING", "安全方案类型变更（apiKey→oauth2 等）"),
    ("R31", "BREAKING", "OAuth scope 新增"),
    ("R32", "WARN", "安全方案删除"),
    ("R33", "WARN", "servers 基础 URL 变更"),
    ("R34", "WARN", "操作标记为 deprecated"),
    ("R35", "WARN", "无法解析的外部 $ref（比对存在盲区）"),
]

BREAKING = "BREAKING"
WARN = "WARN"
INFO = "INFO"

MAX_DEPTH = 6  # 递归展开 schema 的最大深度，防深层自引用炸栈

# format 收窄关系：{旧 format: {收窄后的 format}}
NARROWING_FORMATS = {
    "int64": {"int32"},
    "double": {"float"},
    "date-time": {"date"},
}


def emit_signal(skill, signals, signals_dir="signals"):
    """Write signals/<skill>.json per the quality-signal contract.

    No file is written when signals is empty (clean run).
    """
    if not signals:
        return
    os.makedirs(signals_dir, exist_ok=True)
    doc = {
        "source": skill,
        "generated_at": datetime.now().isoformat(),
        "schema_version": "1.0",
        "signals": signals,
    }
    with open(os.path.join(signals_dir, f"{skill}.json"), "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
def load(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


# ---------------------------------------------------------------- $ref 解析
class Resolver:
    """解析本地 $ref（#/components/...），带循环引用保护。"""

    def __init__(self, spec, findings):
        self.spec = spec
        self.findings = findings
        self.unresolved = set()

    def resolve(self, schema, seen=None):
        if not isinstance(schema, dict):
            return {}
        ref = schema.get("$ref")
        if not ref:
            return schema
        seen = seen or set()
        if ref in seen:
            return {}  # 循环引用，停止展开
        seen = seen | {ref}
        if not ref.startswith("#/"):
            if ref not in self.unresolved:
                self.unresolved.add(ref)
                self.findings.append((WARN, "R35", f"无法解析的外部引用: {ref}（该处比对存在盲区）"))
            return {}
        node = self.spec
        for part in ref[2:].split("/"):
            part = part.replace("~1", "/").replace("~0", "~")
            if not isinstance(node, dict) or part not in node:
                self.findings.append((WARN, "R35", f"$ref 指向不存在的节点: {ref}"))
                return {}
            node = node[part]
        return self.resolve(node, seen) if isinstance(node, dict) else {}


CONSTRAINT_KEYS = ("maxLength", "minLength", "maximum", "minimum",
                   "maxItems", "minItems", "pattern")


def _leaf(schema):
    """抽取单个 schema 节点的可比对特征。"""
    return {
        "type": schema.get("type", "object"),
        "format": schema.get("format", ""),
        "enum": schema.get("enum"),
        "nullable": bool(schema.get("nullable", False)),
        "additionalProperties": schema.get("additionalProperties", True),
        **{k: schema.get(k) for k in CONSTRAINT_KEYS},
    }


def flatten(schema, resolver, prefix="", out=None, required=False, depth=0, seen_refs=None):
    """把 schema 递归摊平成 {属性路径: 特征}。支持 allOf 合并、oneOf/anyOf 计数。"""
    out = {} if out is None else out
    if depth > MAX_DEPTH or not isinstance(schema, dict):
        return out
    schema = resolver.resolve(schema)
    if not schema:
        return out

    # allOf：合并所有分支的 properties / required
    if "allOf" in schema:
        merged = {"type": "object", "properties": {}, "required": []}
        for sub in schema["allOf"]:
            sub = resolver.resolve(sub)
            merged["properties"].update(sub.get("properties", {}) or {})
            merged["required"] += list(sub.get("required", []) or [])
            for k in ("nullable", "additionalProperties") + CONSTRAINT_KEYS:
                if k in sub:
                    merged[k] = sub[k]
        schema = merged

    # oneOf / anyOf：记录分支数量，便于检测分支增删
    for combinator in ("oneOf", "anyOf"):
        if combinator in schema:
            branches = schema[combinator] or []
            key = (prefix or "$") + f".__{combinator}"
            out[key] = {"branches": len(branches)}
            for i, sub in enumerate(branches):
                flatten(sub, resolver, f"{prefix}[{combinator}{i}]", out,
                        False, depth + 1, seen_refs)
            return out

    # 根 schema 也要记录（key="$"），否则根级 nullable / additionalProperties 收紧检测不到
    info = _leaf(schema)
    info["required"] = required
    out[prefix or "$"] = info

    if schema.get("type") == "array" or "items" in schema:
        flatten(schema.get("items", {}), resolver, f"{prefix}[]", out,
                False, depth + 1, seen_refs)

    req_set = set(schema.get("required", []) or [])
    for pname, pv in (schema.get("properties", {}) or {}).items():
        child = f"{prefix}.{pname}" if prefix else pname
        flatten(pv, resolver, child, out, pname in req_set, depth + 1, seen_refs)
    return out


# ---------------------------------------------------------------- 提取器
def params_of(op, resolver):
    """返回 {name: {required, in, type, format, enum, 约束...}}。"""
    params = {}
    for p in op.get("parameters", []) or []:
        p = resolver.resolve(p)
        name = p.get("name")
        if not name:
            continue
        sch = resolver.resolve(p.get("schema", {}) or {})
        entry = _leaf(sch)
        entry["required"] = bool(p.get("required", False))
        entry["in"] = p.get("in", "")
        params[name] = entry
    return params


def body_of(op, resolver):
    """返回 (content-type 集合, 属性摊平表, 请求体是否必填)。"""
    rb = resolver.resolve(op.get("requestBody") or {})
    content = rb.get("content", {}) or {}
    props = {}
    for ct, cv in content.items():
        flatten(cv.get("schema", {}) or {}, resolver, "", props)
    return set(content.keys()), props, bool(rb.get("required", False))


def responses_of(op, resolver):
    """返回 (2xx 状态码集合, 属性摊平表, header 集合)。"""
    codes, props, headers = set(), {}, set()
    for status, sv in (op.get("responses", {}) or {}).items():
        sv = resolver.resolve(sv)
        if not str(status).startswith("2"):
            continue
        codes.add(str(status))
        for hname in (sv.get("headers", {}) or {}):
            headers.add(hname)
        for ct, cv in (sv.get("content", {}) or {}).items():
            flatten(cv.get("schema", {}) or {}, resolver, "", props)
    return codes, props, headers


def sec_of(op, spec):
    """返回该操作生效的安全需求 [{scheme: [scopes]}]（操作级覆盖全局级）。"""
    sec = op.get("security")
    if sec is None:
        sec = spec.get("security", []) or []
    flat = {}
    for item in sec:
        for scheme, scopes in (item or {}).items():
            flat.setdefault(scheme, set()).update(scopes or [])
    return flat


# ---------------------------------------------------------------- 比较器
def cmp_constraints(old, new, where, findings, rule):
    """约束收紧检测：上界变小 / 下界变大 / pattern 变更。"""
    def num(v):
        return v if isinstance(v, (int, float)) else None

    for key, tighter in (("maxLength", "lt"), ("maxItems", "lt"), ("maximum", "lt"),
                         ("minLength", "gt"), ("minItems", "gt"), ("minimum", "gt")):
        o, n = num(old.get(key)), num(new.get(key))
        if n is None:
            continue
        if o is None:  # 新增了约束 → 收紧
            findings.append((BREAKING, rule, f"约束收紧: {where} 新增 {key}={n}"))
        elif (tighter == "lt" and n < o) or (tighter == "gt" and n > o):
            findings.append((BREAKING, rule, f"约束收紧: {where} {key} {o}->{n}"))
    o_pat, n_pat = old.get("pattern"), new.get("pattern")
    if n_pat and n_pat != o_pat:
        findings.append((BREAKING, rule, f"约束收紧: {where} pattern {o_pat or '无'}->{n_pat}"))


def cmp_schema_maps(old_props, new_props, where, findings, side):
    """比较两份摊平后的属性表。side ∈ {'request','response'}。"""
    for pname, oinfo in old_props.items():
        if pname.startswith("$.__") or ".__" in pname:
            continue  # 组合器条目单独处理
        loc = f"{where} {side} 根schema" if pname == "$" else f"{where} {side}.{pname}"
        if pname not in new_props:
            # oneOf/anyOf 分支内的子项消失是「分支删除」的副产物，由 R27/R28 统一报告，避免重复噪声
            if "[oneOf" in pname or "[anyOf" in pname:
                continue
            if side == "response":
                findings.append((BREAKING, "R20", f"响应字段删除: {loc}"))
            else:
                findings.append((WARN, "R19", f"请求体属性删除: {loc}"))
            continue
        ninfo = new_props[pname]
        # 类型变更
        if oinfo["type"] != ninfo["type"]:
            rule = "R21" if side == "response" else "R14"
            findings.append((BREAKING, rule,
                             f"{'响应' if side == 'response' else '请求体'}字段类型变更: "
                             f"{loc} {oinfo['type']}->{ninfo['type']}"))
        # format 收窄
        if oinfo["format"] and ninfo["format"] != oinfo["format"]:
            if ninfo["format"] in NARROWING_FORMATS.get(oinfo["format"], set()):
                findings.append((BREAKING, "R08",
                                 f"format 收窄: {loc} {oinfo['format']}->{ninfo['format']}"))
        # 必填性
        if side == "request" and not oinfo.get("required") and ninfo.get("required"):
            findings.append((BREAKING, "R13", f"请求体属性由可选变必填: {loc}"))
        if side == "response" and oinfo.get("required") and not ninfo.get("required"):
            findings.append((BREAKING, "R22", f"响应字段由必填变可选: {loc}"))
        # nullable 收紧
        if oinfo["nullable"] and not ninfo["nullable"]:
            findings.append((BREAKING, "R26", f"nullable 由 true 收紧为 false: {loc}"))
        # additionalProperties 收紧
        if oinfo["additionalProperties"] is True and ninfo["additionalProperties"] is False:
            findings.append((BREAKING, "R18", f"additionalProperties 收紧为 false: {loc}"))
        # 枚举
        o_enum, n_enum = oinfo.get("enum"), ninfo.get("enum")
        if o_enum and n_enum:
            removed = [str(v) for v in o_enum if str(v) not in set(map(str, n_enum))]
            added = [str(v) for v in n_enum if str(v) not in set(map(str, o_enum))]
            for rv in removed:
                findings.append((BREAKING, "R09", f"枚举值删除: {loc}={rv}"))
            if added and side == "response":
                findings.append((WARN, "R25",
                                 f"响应枚举值新增: {loc} +{','.join(added)}（老客户端可能未覆盖）"))
        elif o_enum and not n_enum:
            pass  # 放宽，安全
        # 约束收紧（请求侧收紧才会拒绝老调用；响应侧收紧同样会破坏老客户端假设）
        cmp_constraints(oinfo, ninfo, loc, findings, "R17" if side == "request" else "R11")

    # 组合器分支增删
    for key, oinfo in old_props.items():
        if ".__oneOf" not in key and ".__anyOf" not in key:
            continue
        ninfo = new_props.get(key)
        if not ninfo:
            findings.append((BREAKING, "R27", f"组合器移除: {where} {key}"))
            continue
        if ninfo["branches"] < oinfo["branches"]:
            findings.append((BREAKING, "R27",
                             f"oneOf/anyOf 分支删除: {where} {key} "
                             f"{oinfo['branches']}->{ninfo['branches']}"))
        elif ninfo["branches"] > oinfo["branches"]:
            findings.append((WARN, "R28",
                             f"oneOf/anyOf 分支新增: {where} {key} "
                             f"{oinfo['branches']}->{ninfo['branches']}"))


def diff(old_spec, new_spec, findings):
    r_old = Resolver(old_spec, findings)
    r_new = Resolver(new_spec, findings)

    # R33 servers 变更
    def urls(spec):
        return [s.get("url", "") for s in (spec.get("servers", []) or [])]
    if urls(old_spec) and urls(old_spec) != urls(new_spec):
        findings.append((WARN, "R33", f"servers 变更: {urls(old_spec)} -> {urls(new_spec)}"))

    old_paths = old_spec.get("paths", {}) or {}
    new_paths = new_spec.get("paths", {}) or {}
    http_methods = {"get", "put", "post", "delete", "options", "head", "patch", "trace"}

    for path, old_ops in old_paths.items():
        if path not in new_paths:
            findings.append((BREAKING, "R01", f"端点删除: {path}"))
            continue
        new_ops = new_paths[path] or {}
        for method, old_op in (old_ops or {}).items():
            if method.lower() not in http_methods:
                continue
            if method not in new_ops:
                findings.append((BREAKING, "R02", f"操作删除: {path} {method.upper()}"))
                continue
            new_op = new_ops[method] or {}
            where = f"{path} {method.upper()}"

            # R34 deprecated
            if new_op.get("deprecated") and not old_op.get("deprecated"):
                findings.append((WARN, "R34", f"操作标记为 deprecated: {where}"))

            # ---- 参数层 ----
            op_old = params_of(old_op, r_old)
            op_new = params_of(new_op, r_new)
            for pname, oinfo in op_old.items():
                if pname not in op_new:
                    if oinfo["required"]:
                        findings.append((BREAKING, "R03", f"必填参数删除: {where} ?{pname}"))
                    else:
                        findings.append((WARN, "R04", f"可选参数删除: {where} ?{pname}"))
                    continue
                ninfo = op_new[pname]
                loc = f"{where} ?{pname}"
                if not oinfo["required"] and ninfo["required"]:
                    findings.append((BREAKING, "R05", f"参数由可选变必填: {loc}"))
                if oinfo["in"] != ninfo["in"]:
                    findings.append((BREAKING, "R06",
                                     f"参数位置变更: {loc} {oinfo['in']}->{ninfo['in']}"))
                if oinfo["type"] != ninfo["type"]:
                    findings.append((BREAKING, "R07",
                                     f"参数类型变更: {loc} {oinfo['type']}->{ninfo['type']}"))
                if oinfo["format"] and ninfo["format"] in NARROWING_FORMATS.get(oinfo["format"], set()):
                    findings.append((BREAKING, "R08",
                                     f"参数 format 收窄: {loc} {oinfo['format']}->{ninfo['format']}"))
                if oinfo.get("enum") and ninfo.get("enum"):
                    removed = [str(v) for v in oinfo["enum"]
                               if str(v) not in set(map(str, ninfo["enum"]))]
                    for rv in removed:
                        findings.append((BREAKING, "R09", f"参数枚举值删除: {loc}={rv}"))
                cmp_constraints(oinfo, ninfo, loc, findings, "R11")
            for pname, ninfo in op_new.items():
                if pname not in op_old and ninfo["required"]:
                    findings.append((BREAKING, "R10", f"新增必填参数: {where} ?{pname}"))

            # ---- 请求体层 ----
            o_cts, o_body, o_req = body_of(old_op, r_old)
            n_cts, n_body, n_req = body_of(new_op, r_new)
            for ct in o_cts - n_cts:
                findings.append((BREAKING, "R15", f"请求体 content-type 删除: {where} {ct}"))
            if not o_req and n_req and n_cts:
                findings.append((BREAKING, "R16", f"请求体由可选变必填: {where}"))
            new_required = {k for k, v in n_body.items() if v.get("required")}
            old_required = {k for k, v in o_body.items() if v.get("required")}
            for ar in sorted(new_required - old_required - set(o_body.keys())):
                findings.append((BREAKING, "R12", f"请求体新增必填属性: {where} body.{ar}"))
            cmp_schema_maps(o_body, n_body, where, findings, "request")

            # ---- 响应层 ----
            o_codes, o_props, o_heads = responses_of(old_op, r_old)
            n_codes, n_props, n_heads = responses_of(new_op, r_new)
            for code in sorted(o_codes - n_codes):
                findings.append((BREAKING, "R23", f"成功状态码删除: {where} {code}"))
            for h in sorted(o_heads - n_heads):
                findings.append((BREAKING, "R24", f"响应 header 删除: {where} {h}"))
            cmp_schema_maps(o_props, n_props, where, findings, "response")

            # ---- 安全层 ----
            o_sec = sec_of(old_op, old_spec)
            n_sec = sec_of(new_op, new_spec)
            for scheme in sorted(set(n_sec) - set(o_sec)):
                findings.append((BREAKING, "R29", f"安全方案新增: {where} 需要 {scheme}"))
            for scheme in sorted(set(o_sec) - set(n_sec)):
                findings.append((WARN, "R32", f"安全方案删除: {where} 原需 {scheme}"))
            for scheme in sorted(set(o_sec) & set(n_sec)):
                added_scope = n_sec[scheme] - o_sec[scheme]
                if added_scope:
                    findings.append((BREAKING, "R31",
                                     f"OAuth scope 新增: {where} {scheme} +{','.join(sorted(added_scope))}"))
            o_schemes = (old_spec.get("components", {}) or {}).get("securitySchemes", {}) or {}
            n_schemes = (new_spec.get("components", {}) or {}).get("securitySchemes", {}) or {}
            for name in set(o_sec) & set(n_sec):
                ot = (o_schemes.get(name) or {}).get("type")
                nt = (n_schemes.get(name) or {}).get("type")
                if ot and nt and ot != nt:
                    findings.append((BREAKING, "R30",
                                     f"安全方案类型变更: {where} {name} {ot}->{nt}"))

    # 去重（同一变更可能被多路径命中）
    seen, uniq = set(), []
    for item in findings:
        if item not in seen:
            seen.add(item)
            uniq.append(item)
    findings[:] = uniq


def render(findings):
    n_break = sum(1 for sev, _, _ in findings if sev == BREAKING)
    n_warn = sum(1 for sev, _, _ in findings if sev == WARN)
    lines = ["# 接口契约比对报告（OpenAPI Contract Diff）\n"]
    lines.append(f"**结论：{'❌ 存在破坏性变更，禁止合入/发布' if n_break else '✅ 无破坏性变更，可放行'}**\n")
    lines.append(f"- 破坏性变更(BREAKING)：{n_break}")
    lines.append(f"- 告警(WARN)：{n_warn}")
    lines.append(f"- 规则库：{len(RULES)} 条\n")
    lines.append(
        "> **能力边界（R-23）**：本技能为**生产者侧（provider-side）OpenAPI 契约 diff**，"
        "比对规格破坏性变更；**不做 consumer-driven contract testing（消费者侧契约由 Pact 等工具承担）**。"
        "破坏性变更按生产者视角判定；消费者兼容性风险仍建议结合 Pact 做 consumer 侧校验，避免「生产者无变更但消费者契约破坏」的盲区。\n")
    lines.append("| 级别 | 规则 | 变更 |")
    lines.append("| --- | --- | --- |")
    order = {BREAKING: 0, WARN: 1, INFO: 2}
    for sev, rule, msg in sorted(findings, key=lambda x: (order.get(x[0], 9), x[1])):
        lines.append(f"| {sev} | {rule} | {msg} |")
    if not findings:
        lines.append("| — | — | 未检出任何差异 |")
    lines.append("\n## 规则清单")
    lines.append("| 编号 | 默认级别 | 说明 |")
    lines.append("| --- | --- | --- |")
    for rid, sev, desc in RULES:
        lines.append(f"| {rid} | {sev} | {desc} |")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--old")
    ap.add_argument("--new")
    ap.add_argument("--out")
    ap.add_argument("--fail-on", action="store_true", help="存在 BREAKING 时 sys.exit(1)")
    ap.add_argument("--signals-dir", default="signals", help="质量信号输出目录（默认 ./signals）")
    ap.add_argument("--rules", action="store_true", help="打印规则清单后退出")
    args = ap.parse_args()

    if args.rules:
        print(f"契约破坏性变更规则库（{len(RULES)} 条）")
        for rid, sev, desc in RULES:
            print(f"  {rid}  [{sev:8s}] {desc}")
        return 0
    if not (args.old and args.new and args.out):
        ap.error("--old / --new / --out 为必填（除非使用 --rules）")

    old_spec = load(args.old)
    new_spec = load(args.new)
    findings = []
    diff(old_spec, new_spec, findings)

    md = render(findings)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(md)
    n_break = sum(1 for sev, _, _ in findings if sev == BREAKING)
    n_warn = sum(1 for sev, _, _ in findings if sev == WARN)
    # 质量信号契约：存在破坏性变更 → blocking 信号，门禁据此禁止发布
    if n_break:
        emit_signal("qa-api-contract", [{
            "signal": "breaking_change", "severity": "critical", "count": n_break,
            "blocking": True, "detail_ref": args.out,
        }], args.signals_dir)
    print(f"[OK] 契约比对完成: {args.out}")
    print(f"[RESULT] BREAKING={n_break}  WARN={n_warn}  RULES={len(RULES)}")
    if args.fail_on and n_break:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
