#!/usr/bin/env python3
"""qa-api-runner 核心引擎（纯逻辑，可被 run.py 或 pytest harness 复用）。

能力：
- 场景化用例（单接口 + 多接口串联）
- 变量提取与 ${var} 上下文替换
- 响应断言（eq/ne/contains/in/gt/lt/ge/le/exists）
- 可选 MySQL 数据库断言（接口 + 数据双校验）
- 轻量运行（无需 pytest）或接入 pytest+allure

设计原则：引擎只负责「执行一个场景文件并产出结果」，编排与报告由上层决定。
"""
import json
import re
import os

# W2/W10 永真断言：strict 模式下，无语义断言的用例直接判失败（env opt-in，默认关以兼容既有场景）。
_STRICT_ASSERT = os.environ.get("QA_API_STRICT_ASSERT") == "1"


def _type_ok(v, t):
    m = {
        "string": isinstance(v, str),
        "number": isinstance(v, (int, float)) and not isinstance(v, bool),
        "integer": isinstance(v, int) and not isinstance(v, bool),
        "boolean": isinstance(v, bool),
        "object": isinstance(v, dict),
        "array": isinstance(v, list),
    }
    return m.get(t, True)


def _schema_ok(obj, schema):
    if not isinstance(schema, dict):
        return False, "schema 非对象"
    if "required" in schema:
        if not isinstance(obj, dict):
            return False, "期望对象但收到非对象"
        for k in schema["required"]:
            if k not in obj:
                return False, f"缺少必填字段 {k}"
    if "properties" in schema:
        for k, spec in schema["properties"].items():
            if k in obj and isinstance(spec, dict) and "type" in spec:
                if not _type_ok(obj[k], spec["type"]):
                    return False, f"字段 {k} 类型非 {spec['type']}"
    return True, "schema 校验通过"


# ---------- JSONPath（极简：支持 $.a.b[0].c） ----------
def json_get(obj, path):
    if not path or path in ("$", ""):
        return obj
    p = path
    if p.startswith("$."):
        p = p[2:]
    elif p.startswith("$"):
        p = p[1:]
    cur = obj
    # 切分并支持 [n]
    tokens = re.split(r"\.|\[|\]", p)
    tokens = [t for t in tokens if t != ""]
    for tok in tokens:
        if tok.isdigit():
            cur = cur[int(tok)]
        else:
            cur = cur[tok]
    return cur


def _resolve(val, ctx):
    """把字符串中的 ${var} 替换为上下文值；非字符串原样返回。"""
    if isinstance(val, str):
        def repl(m):
            return str(ctx.get(m.group(1), m.group(0)))
        return re.sub(r"\$\{(\w+)\}", repl, val)
    if isinstance(val, dict):
        return {k: _resolve(v, ctx) for k, v in val.items()}
    if isinstance(val, list):
        return [_resolve(v, ctx) for v in val]
    return val


# ---------- 断言 ----------
def _coerce(a, b):
    # 尝试数值比较，失败则用原类型
    try:
        if isinstance(a, str) and isinstance(b, (int, float)):
            return float(a), b
    except Exception:
        pass
    return a, b


def check_assert(actual, op, expect):
    a, e = _coerce(actual, expect)
    if op == "eq":
        return a == e, f"{a} == {e}"
    if op == "ne":
        return a != e, f"{a} != {e}"
    if op == "contains":
        return expect in actual, f"{expect} in {actual}"
    if op == "in":
        return actual in expect, f"{actual} in {expect}"
    if op == "gt":
        return a > e, f"{a} > {e}"
    if op == "lt":
        return a < e, f"{a} < {e}"
    if op == "ge":
        return a >= e, f"{a} >= {e}"
    if op == "le":
        return a <= e, f"{a} <= {e}"
    if op == "exists":
        return actual is not None, f"exists {actual is not None}"
    # 正则匹配
    if op == "regex":
        try:
            ok = bool(re.search(str(expect), str(actual)))
            return ok, f"{actual!r} ~= {expect!r}: {ok}"
        except Exception as ex:
            return False, f"regex 错误 {expect!r}: {ex}"
    # 长度校验（len / len_eq / len_gt / len_lt / len_ge / len_le）
    if op in ("len", "len_eq", "len_gt", "len_lt", "len_ge", "len_le"):
        try:
            n = len(actual)
            target = int(expect)
        except Exception:
            return False, f"len 比较失败: actual={actual!r} expect={expect!r}"
        if op == "len" or op == "len_eq":
            return n == target, f"len={n} == {target}"
        if op == "len_gt":
            return n > target, f"len={n} > {target}"
        if op == "len_lt":
            return n < target, f"len={n} < {target}"
        if op == "len_ge":
            return n >= target, f"len={n} >= {target}"
        if op == "len_le":
            return n <= target, f"len={n} <= {target}"
    # JSON Schema 轻量结构校验
    if op == "schema":
        return _schema_ok(actual, expect)
    return False, f"未知操作符 {op}"


def evaluate_asserts(resp_json, asserts, ctx):
    results = []
    for a in asserts or []:
        op = next(iter(a.keys()))
        payload = a[op]
        # payload 形式: [path_or_literal, expected]；exists 等单参数操作符可只有一项
        src = payload[0]
        expect = payload[1] if len(payload) > 1 else None
        if isinstance(src, str) and src.startswith("$"):
            actual = json_get(resp_json, src)
        else:
            actual = _resolve(src, ctx)
        expect = _resolve(expect, ctx) if isinstance(expect, str) else expect
        ok, detail = check_assert(actual, op, expect)
        results.append({"op": op, "ok": ok, "detail": detail})
    return results


# ---------- DB 断言（可选） ----------
def run_db_asserts(db_cfg, db_asserts, ctx):
    results = []
    try:
        import mysql.connector
    except ImportError:
        return [{"ok": False, "detail": "未安装 mysql.connector，跳过 DB 断言"} for _ in db_asserts or []]
    if not db_cfg:
        return [{"ok": False, "detail": "未配置 DB，跳过 DB 断言"} for _ in db_asserts or []]
    conn = mysql.connector.connect(**db_cfg)
    try:
        cur = conn.cursor()
        for d in db_asserts or []:
            op = next(iter(d.keys()))
            sql, expect = d[op][0], d[op][1]
            sql = _resolve(sql, ctx)
            cur.execute(sql)
            row = cur.fetchone()
            actual = row[0] if row else None
            ok, detail = check_assert(actual, op, _resolve(expect, ctx) if isinstance(expect, str) else expect)
            results.append({"op": op, "sql": sql, "ok": ok, "detail": detail})
    finally:
        conn.close()
    return results


# ---------- 单用例执行 ----------
def run_case(case, ctx, base_url, session, db_cfg):
    req = case.get("request", {})
    method = req.get("method", "GET").upper()
    path = _resolve(req.get("path", ""), ctx)
    url = base_url.rstrip("/") + "/" + path.lstrip("/") if not path.startswith("http") else path
    headers = _resolve(req.get("headers", {}), ctx)
    kwargs = {}
    if "json" in req:
        kwargs["json"] = _resolve(req["json"], ctx)
    if "params" in req:
        kwargs["params"] = _resolve(req["params"], ctx)
    if "data" in req:
        kwargs["data"] = _resolve(req["data"], ctx)

    log = {"id": case.get("id"), "name": case.get("name"), "url": url, "method": method}
    try:
        resp = session.request(method, url, headers=headers, timeout=30, **kwargs)
        try:
            resp_json = resp.json()
        except Exception:
            resp_json = {"_text": resp.text}
        log["status_code"] = resp.status_code

        # 提取变量
        extract = case.get("extract", {})
        for var, p in extract.items():
            ctx[var] = json_get(resp_json, p)
        log["extract"] = {k: ctx.get(k) for k in extract}

        ares = evaluate_asserts(resp_json, case.get("assert"), ctx)
        log["asserts"] = ares

        dbres = []
        if case.get("db_assert"):
            dbres = run_db_asserts(db_cfg, case.get("db_assert"), ctx)
        log["db_asserts"] = dbres

        # ---- W9 假通过治理：状态判定不再「强制 <400」闷杀负向测试 ----
        # 旧逻辑：passed 恒含 status_code<400，导致无法写 4xx/5xx 负向用例（误判失败）。
        # 新逻辑：
        #  - 显式 expect_status：以「等于期望码」为准（支持负向路径，如断言 403）。
        #  - allow_error_status=True：显式声明允许错误态（负向测试 opt-in）。
        #  - 其余（默认）：保留 fail-closed 守卫——5xx 始终失败、4xx 默认失败（除非 opt-in）。
        has_asserts = bool(case.get("assert"))
        if "expect_status" in case:
            status_ok = (resp.status_code == int(case["expect_status"]))
            log["status_check"] = "expect_status=%s" % case["expect_status"]
        elif case.get("allow_error_status"):
            status_ok = True
            log["status_check"] = "allow_error_status"
        else:
            status_ok = resp.status_code < 400
            log["status_check"] = "default<400"
        if not has_asserts and not case.get("allow_no_assert"):
            # W2/W10 永真断言：无语义断言即 pass 属假绿。默认告警（不硬拦，避免破坏既有场景），
            # strict 模式下置 passed=False。run.py 可传 strict。
            log["no_assert_warn"] = True
            if _STRICT_ASSERT:
                status_ok = False
                log["passed"] = False
                log["blocked_reason"] = "no_assert_trivial"
                return log

        passed = status_ok and all(a["ok"] for a in ares) and all(d["ok"] for d in dbres)
        log["passed"] = passed
    except Exception as e:
        log["passed"] = False
        log["error"] = str(e)
    return log


def run_scenario(scenario, db_cfg=None):
    """执行整个场景，返回结果列表与上下文。"""
    import requests
    base_url = scenario.get("base_url", "")
    ctx = dict(scenario.get("env", {}))
    session = requests.Session()
    if scenario.get("global_headers"):
        session.headers.update(_resolve(scenario["global_headers"], ctx))
    results = []
    for case in scenario.get("cases", []):
        results.append(run_case(case, ctx, base_url, session, db_cfg))
    summary = {
        "total": len(results),
        "passed": sum(1 for r in results if r.get("passed")),
        "failed": sum(1 for r in results if not r.get("passed")),
    }
    return results, summary, ctx
