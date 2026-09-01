#!/usr/bin/env python3
"""Expand a case set with boundary / abnormal variants and de-duplicate.

Usage:
    # 边界/异常扩充（原有能力）
    python scripts/expand_cases.py --input cases.json --out expanded.json --md expanded.md

    # 经典测试设计方法（升级 III-1：等价类 / 判定表 / 状态迁移 / Pairwise 组合）
    python scripts/expand_cases.py --technique pairwise --params params.json --out pairwise.json
    python scripts/expand_cases.py --technique equivalence --params params.json --out eq.json
    python scripts/expand_cases.py --technique decision-table --dt conditions.json --out dt.json
    python scripts/expand_cases.py --technique state-transition --stm states.json --out stm.json

params.json（pairwise / equivalence 共用）:
{
  "fields": [
    {"name":"browser","type":"enum","values":["Chrome","Safari","Edge"]},
    {"name":"os","type":"enum","values":["Windows","macOS","iOS"]},
    {"name":"network","type":"enum","values":["WiFi","4G","弱网"]}
  ]
}

方法论来源：微软 PICT 的成对组合（Pairwise）思想——大部分缺陷由 1~2 个参数交互触发，
两两覆盖即可在不穷举的前提下保留绝大多数组合有效性。本实现为**纯 Python 最小覆盖数组
（贪心 AETG-lite）**，不依赖 PICT 二进制，保持技能零外部依赖的优势。
"""
import argparse
import json
import sys
from itertools import combinations, product


# ----------------------------------------------------------------------------
# 原有：边界 / 异常扩充
# ----------------------------------------------------------------------------
def boundary_variants(f):
    name = f["name"]
    t = f.get("type", "string")
    variants = []
    if t in ("int", "number", "float"):
        lo = f.get("min", 0)
        hi = f.get("max", 100)
        for val, tag in [(lo - 1, "下边界-1"), (lo, "下边界"), (hi, "上边界"), (hi + 1, "上边界+1")]:
            variants.append((f"{name} {tag} ({val})", f"输入 {name}={val}", "符合字段约束的预期行为"))
        # R-17：精度边界（浮点舍入误差 / 极值，避免 0.1+0.2 类误判）
        if t in ("float", "number"):
            variants.append((f"{name} 精度边界(0.1+0.2)", f"输入 {name}=0.1+0.2 求和",
                             "按 decimal 比较，不应误判为 0.30000000000000004"))
            variants.append((f"{name} 极大值(1e308)", f"输入 {name}=1e308", "不溢出 / 正确表示或被拒绝"))
            variants.append((f"{name} 极小值(1e-308)", f"输入 {name}=1e-308", "正确处理或按 0 处理"))
    else:
        lo = f.get("min", 1)
        hi = f.get("max", 20)
        # R-17：长度边界（空 / 下限 / 上限 / 超限）
        variants.append((f"{name} 为空", f"输入 {name}=（空）", "提示必填 / 拒绝提交"))
        variants.append((f"{name} 恰 {max(lo,1)} 字符(下限)", f"输入 {name}={'A' * max(lo, 1)}",
                         "正常处理（长度下限）"))
        variants.append((f"{name} 恰 {hi} 字符(上限)", f"输入 {name}={'A' * hi}",
                         "正常处理（长度上限）"))
        variants.append((f"{name} 超长({hi + 1})", f"输入 {name}={'A' * (hi + 1)}",
                         "被截断 / 提示超长 / 拒绝"))
        # R-17：编码边界（多字节 / 注入 / 控制字符 / 零宽）
        variants.append((f"{name} 多字节(中文/emoji)", f"输入 {name}=测试🔥中文",
                         "正确存储 / 不乱码 / 字节长度与字符长度分别校验"))
        variants.append((f"{name} 含 HTML/注入字符", f"输入 {name}=<script>'\"%&",
                         "被转义 / 拒绝注入"))
        variants.append((f"{name} 含控制字符/NUL", f"输入 {name}=AB\\x00CD",
                         "被过滤 / 拒绝 / 不被 NUL 截断"))
        variants.append((f"{name} 含 BOM/零宽字符", f"输入 {name}=\\ufeff\\u200b隐藏",
                         "不被零宽字符绕过长度 / 校验"))
    return variants


def expand_boundary(data):
    cases = data.get("cases", [])
    fields = data.get("fields", [])
    orig = len(cases)
    existing = {c.get("title") for c in cases}
    n = len(cases)
    added = 0
    for f in fields:
        for title, steps, expected in boundary_variants(f):
            if title in existing:
                continue
            n += 1
            added += 1
            existing.add(title)
            cases.append({
                "id": f"C{n:03d}", "module": f.get("module", "通用"),
                "title": title, "steps": steps, "expected": expected, "type": "boundary",
            })
    return cases, orig, added


# ----------------------------------------------------------------------------
# 新增 III-1：经典测试设计方法
# ----------------------------------------------------------------------------
def all_pairs(params):
    """返回所有 (param_i, value) × (param_j, value) 的待覆盖对集合。"""
    pairs = set()
    names = list(params.keys())
    for a, b in combinations(range(len(names)), 2):
        for va in params[names[a]]:
            for vb in params[names[b]]:
                pairs.add((a, va, b, vb))
    return names, pairs


def pairwise_cover(params):
    """贪心最小覆盖数组（AETG-lite）：逐步加入能覆盖最多新参数对的用例。"""
    names, uncovered = all_pairs(params)
    if not names:
        return []
    # 种子用例：每个参数取第一个值
    seed = {names[i]: params[names[i]][0] for i in range(len(names))}
    cases = [dict(seed)]
    covered = set()
    for case in cases:
        for a, b in combinations(range(len(names)), 2):
            na, nb = names[a], names[b]
            if na in case and nb in case:
                covered.add((a, case[na], b, case[nb]))

    def gain(candidate):
        g = 0
        for a, b in combinations(range(len(names)), 2):
            na, nb = names[a], names[b]
            if na in candidate and nb in candidate:
                if (a, candidate[na], b, candidate[nb]) in uncovered and \
                   (a, candidate[na], b, candidate[nb]) not in covered:
                    g += 1
        return g

    # 候选：每个参数轮流取非首值，其余保持种子
    while uncovered - covered:
        best = None
        best_gain = 0
        for i in range(len(names)):
            for v in params[names[i]][1:]:
                cand = dict(seed)
                cand[names[i]] = v
                g = gain(cand)
                if g > best_gain:
                    best_gain = g
                    best = cand
        if best is None or best_gain == 0:
            # 无法再增加覆盖（理论上不会发生），停止
            break
        cases.append(best)
        for a, b in combinations(range(len(names)), 2):
            na, nb = names[a], names[b]
            if na in best and nb in best:
                covered.add((a, best[na], b, best[nb]))
    return cases


def equivalence_cases(params):
    """等价类划分：每个参数生成「有效等价类」与「无效等价类」用例。"""
    cases = []
    n = 0
    for name, vals in params.items():
        n += 1
        cases.append({"id": f"EQ{n:03d}", "type": "等价类-有效", "title": f"{name} 有效等价类",
                      "steps": f"取 {name} 的典型有效值（如 {vals[0]}）", "expected": "正常处理"})
        n += 1
        cases.append({"id": f"EQ{n:03d}", "type": "等价类-无效", "title": f"{name} 无效等价类",
                      "steps": f"取 {name} 的越界/非法值", "expected": "被拒绝并提示"})
    return cases


def decision_table(conditions, actions):
    """判定表：条件全组合 × 动作预期。conditions: [{"name":..,"values":[..]}]。"""
    cond_names = [c["name"] for c in conditions]
    cond_vals = [c["values"] for c in conditions]
    cases = []
    n = 0
    for combo in product(*cond_vals):
        n += 1
        cond_str = ", ".join(f"{cond_names[i]}={combo[i]}" for i in range(len(cond_names)))
        cases.append({"id": f"DT{n:03d}", "type": "判定表", "title": f"条件组合：{cond_str}",
                      "steps": f"构造场景：{cond_str}", "expected": "触发对应动作（见判定表规则）"})
    return cases


def state_transition(states, events):
    """状态迁移：每个 (状态 × 事件) 生成一条迁移用例。"""
    cases = []
    n = 0
    for st in states:
        for ev in events:
            n += 1
            cases.append({"id": f"STM{n:03d}", "type": "状态迁移",
                          "title": f"状态[{st}] 收到事件[{ev}]",
                          "steps": f"系统处于 {st}，触发 {ev}",
                          "expected": "按状态机定义迁移到目标状态 / 或保持 / 或拒绝"})
    return cases


def load_params(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    params = {}
    for fdef in data.get("fields", []):
        name = fdef["name"]
        if fdef.get("values"):
            params[name] = fdef["values"]
        elif fdef.get("type") == "enum" and fdef.get("values"):
            params[name] = fdef["values"]
        elif "min" in fdef and "max" in fdef:
            params[name] = [fdef["min"], (fdef["min"] + fdef["max"]) // 2, fdef["max"]]
        else:
            params[name] = ["有效", "无效"]
    return params


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", help="边界扩充输入 cases.json")
    ap.add_argument("--out", required=True, help="输出 JSON")
    ap.add_argument("--md", help="同时输出 Markdown")
    ap.add_argument("--technique", choices=["pairwise", "equivalence", "decision-table", "state-transition"],
                    help="经典测试设计方法")
    ap.add_argument("--params", help="参数定义 JSON（pairwise/equivalence 用）")
    ap.add_argument("--dt", help="判定表条件 JSON（decision-table 用）")
    ap.add_argument("--stm", help="状态机 JSON {states:[],events:[]}（state-transition 用）")
    args = ap.parse_args()

    cases = []

    if args.technique:
        tech = args.technique
        if tech == "pairwise":
            if not args.params:
                print("[ERROR] pairwise 需要 --params", file=sys.stderr)
                return 2
            params = load_params(args.params)
            rows = pairwise_cover(params)
            for i, row in enumerate(rows, 1):
                cases.append({"id": f"PW{i:03d}", "type": "pairwise",
                              "title": "组合-" + "/".join(f"{k}={v}" for k, v in row.items()),
                              "params": row,
                              "expected": "覆盖该参数两两组合，验证交互正确性"})
            print(f"[OK] Pairwise 最小覆盖：{len(params)} 个参数 → {len(cases)} 条用例"
                  f"（全组合为 {combinations_count(params)}）")
        elif tech == "equivalence":
            if not args.params:
                print("[ERROR] equivalence 需要 --params", file=sys.stderr)
                return 2
            params = load_params(args.params)
            cases = equivalence_cases(params)
            print(f"[OK] 等价类划分：{len(cases)} 条用例")
        elif tech == "decision-table":
            if not args.dt:
                print("[ERROR] decision-table 需要 --dt", file=sys.stderr)
                return 2
            with open(args.dt, "r", encoding="utf-8-sig") as f:
                dt = json.load(f)
            cases = decision_table(dt.get("conditions", []), dt.get("actions", []))
            print(f"[OK] 判定表：{len(cases)} 条用例")
        elif tech == "state-transition":
            if not args.stm:
                print("[ERROR] state-transition 需要 --stm", file=sys.stderr)
                return 2
            with open(args.stm, "r", encoding="utf-8-sig") as f:
                stm = json.load(f)
            cases = state_transition(stm.get("states", []), stm.get("events", []))
            print(f"[OK] 状态迁移：{len(cases)} 条用例")
    else:
        if not args.input:
            print("[ERROR] 未指定 --technique 时需提供 --input 边界扩充", file=sys.stderr)
            return 2
        with open(args.input, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        cases, orig, added = expand_boundary(data)
        print(f"[OK] 边界扩充完成：原始 {orig} → 现 {len(cases)}（新增 {added}）")

    out = {"cases": cases, "technique": args.technique or "boundary"}
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"[OK] 已写出: {args.out}")

    if args.md:
        lines = ["# 测试用例\n", "| ID | 类型 | 标题 | 步骤 | 预期 |",
                 "| --- | --- | --- | --- | --- |"]
        for c in cases:
            lines.append(f"| {c.get('id')} | {c.get('type')} | {c.get('title')} | "
                         f"{c.get('steps','')} | {c.get('expected','')} |")
        with open(args.md, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print(f"[OK] 已生成 Markdown: {args.md}")
    return 0


def combinations_count(params):
    try:
        from functools import reduce
        import operator
        return reduce(operator.mul, (len(v) for v in params.values()), 1)
    except Exception:
        return "?"


if __name__ == "__main__":
    sys.exit(main())
