#!/usr/bin/env python3
"""追溯矩阵生成器（R-07）：case_id → testpoint_id → req_id 三级推导追溯矩阵。

从工作区抽取三件套并产出机器可读追溯矩阵 + 断链审计：
- `requirement.md`（qa-req-spec 产物）：需求 ID 约定为文本中的 `REQ-<标识>`。
- `testpoints.md`（qa-test-analysis 产物）：测试点 ID 约定为 `TP-<标识>`；
  测试点若在某段内提及 `REQ-<标识>`，视为其溯源需求。
- `cases.json`（qa-test-case-gen 输入）：`cases[].id` 为用例 ID（TC-xxx）；
  `cases[].covers`（或用例正文中提及的 `TP-<标识>`）为其归属测试点。

真实链路依赖上游逐步采纳上述 ID 约定；本工具对缺失链接**如实报告断链**
（fail-closed 可选：--fail-on-gaps 时存在断链即 exit 2），不伪造完整矩阵。
零依赖（纯标准库）。
"""
import argparse
import json
import os
import re
import sys

REQ_RE = re.compile(r"REQ-[A-Za-z0-9_-]+")
TP_RE = re.compile(r"TP-[A-Za-z0-9_-]+")
TC_RE = re.compile(r"TC-[A-Za-z0-9_-]+")


def read_text(path):
    if not path or not os.path.isfile(path):
        return ""
    with open(path, encoding="utf-8") as f:
        return f.read()


def read_cases_json(path):
    if not path or not os.path.isfile(path):
        return []
    try:
        doc = json.load(open(path, encoding="utf-8"))
    except Exception:
        return []
    if isinstance(doc, dict):
        return doc.get("cases", []) or []
    if isinstance(doc, list):
        return doc
    return []


def nearest_req_before(text, pos):
    """在 text[:pos] 中找离 pos 最近的 REQ- ID（段落级溯源）。"""
    seg = text[:pos]
    matches = list(REQ_RE.finditer(seg))
    return matches[-1].group(0) if matches else None


def extract(workdir):
    req_md = read_text(os.path.join(workdir, "requirement.md"))
    tp_md = read_text(os.path.join(workdir, "testpoints.md"))
    cases = read_cases_json(os.path.join(workdir, "cases.json"))

    reqs = set(REQ_RE.findall(req_md))

    # 测试点 → 其溯源需求：优先取该 TP 自身段落内提及的 REQ-（兼容
    # 「TP 段落正文内写明来源需求」的自然写法），回退到该 TP 标记之前
    # 最近的 REQ-（兼容「需求在上、测试点在下」的分组写法）。
    tp_matches = list(TP_RE.finditer(tp_md))
    tps = {}
    for i, m in enumerate(tp_matches):
        tp = m.group(0)
        start = m.start()
        end = tp_matches[i + 1].start() if i + 1 < len(tp_matches) else len(tp_md)
        seg = tp_md[start:end]
        reqs = REQ_RE.findall(seg)
        req = reqs[0] if reqs else nearest_req_before(tp_md, start)
        tps[tp] = req

    # 用例 → 其归属测试点
    cases_links = []
    for c in cases:
        if not isinstance(c, dict):
            continue
        cid = c.get("id") or ""
        covers = c.get("covers")
        if not covers:
            # 退化：用例正文（含 steps/expected/name）中提及的 TP-
            blob = json.dumps(c, ensure_ascii=False)
            mm = TP_RE.search(blob)
            covers = mm.group(0) if mm else None
        cases_links.append((cid, covers))

    # 组装矩阵 + 断链审计
    matrix = []
    gaps = []
    for cid, tp in cases_links:
        if not cid:
            continue
        req = tps.get(tp) if tp else None
        if not tp:
            gaps.append(f"{cid}: 无归属测试点（cases→testpoint 断链）")
        elif not req:
            gaps.append(f"{cid}→{tp}: 测试点无溯源需求（testpoint→req 断链）")
        matrix.append({"case": cid, "testpoint": tp, "req": req})

    # 测试点自身无溯源需求
    for tp, req in tps.items():
        if not req:
            gaps.append(f"{tp}: 测试点无溯源需求（testpoint→req 断链）")

    stats = {
        "req_count": len(reqs),
        "testpoint_count": len(tps),
        "case_count": len([c for c, _ in cases_links if c]),
        "linked_case_count": len(matrix),
        "gap_count": len(gaps),
    }
    return matrix, gaps, stats, sorted(reqs), sorted(tps.keys())


def render_md(matrix, gaps, stats, reqs, tps):
    L = ["# 测试用例追溯矩阵（case → testpoint → req）", ""]
    L.append("## 统计")
    L.append("")
    L.append(f"- 需求（REQ-）：{stats['req_count']}")
    L.append(f"- 测试点（TP-）：{stats['testpoint_count']}")
    L.append(f"- 用例（TC-）：{stats['case_count']}")
    L.append(f"- 已链路用例：{stats['linked_case_count']}")
    L.append(f"- 断链数：{stats['gap_count']}")
    L.append("")
    L.append("## 矩阵")
    L.append("")
    L.append("| 用例 (case) | 测试点 (testpoint) | 需求 (req) |")
    L.append("|---|---|---|")
    for row in matrix:
        L.append(f"| {row['case']} | {row['testpoint'] or '—'} | {row['req'] or '—'} |")
    L.append("")
    if gaps:
        L.append("## 断链审计（须补齐）")
        L.append("")
        for g in gaps:
            L.append(f"- ⚠️ {g}")
        L.append("")
    else:
        L.append("## 断链审计")
        L.append("")
        L.append("- ✅ 无断链，三级推导完整可追溯。")
        L.append("")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description="用例追溯矩阵生成（case→testpoint→req）")
    ap.add_argument("--dir", required=True, help="含 requirement.md/testpoints.md/cases.json 的工作区")
    ap.add_argument("--out", default="trace_matrix.md", help="Markdown 矩阵输出")
    ap.add_argument("--json", default="trace_matrix.json", help="JSON 矩阵输出")
    ap.add_argument("--fail-on-gaps", action="store_true", help="存在断链时 exit 2（fail-closed 可选）")
    args = ap.parse_args()

    matrix, gaps, stats, reqs, tps = extract(args.dir)
    md = render_md(matrix, gaps, stats, reqs, tps)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(md)
    with open(args.json, "w", encoding="utf-8") as f:
        json.dump({"matrix": matrix, "gaps": gaps, "stats": stats}, f, ensure_ascii=False, indent=2)

    print(f"[OK] 追溯矩阵：req={stats['req_count']} tp={stats['testpoint_count']} "
          f"case={stats['case_count']} linked={stats['linked_case_count']} gaps={stats['gap_count']}")
    if gaps:
        for g in gaps:
            print(f"  ⚠️ {g}")
    if args.fail_on_gaps and gaps:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
