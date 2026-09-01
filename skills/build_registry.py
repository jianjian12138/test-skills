#!/usr/bin/env python3
"""扫描 skills/ 下所有技能，生成单一注册中心 REGISTRY.json（避免硬编码漂移）。

Usage:
    python build_registry.py
输出：<skills根>/REGISTRY.json
"""
import argparse
import datetime
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))


def parse_frontmatter(path):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        return None, None, {}
    fm = m.group(1)
    name = None
    desc = None
    metadata = {}
    runtime_deps = []
    lines = fm.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("name:"):
            name = line[len("name:"):].strip()
        elif line.startswith("description:"):
            if "|-" in line:
                buf = []
                j = i + 1
                while j < len(lines) and (lines[j].startswith(("  ", "\t"))
                                          and not lines[j].strip().startswith("agent_created")):
                    buf.append(lines[j].strip())
                    j += 1
                desc = " ".join(buf).strip()
                i = j
                continue
            else:
                desc = line[len("description:"):].strip().strip('"')
        elif line.startswith("metadata:"):
            # S-02：读取归一化元数据（category/stage/tier）→ SKILL.md 为 SSOT
            j = i + 1
            while j < len(lines) and lines[j].startswith(("  ", "\t")):
                sub = lines[j].strip()
                if ":" in sub:
                    k, _, v = sub.partition(":")
                    metadata[k.strip()] = v.strip()
                j += 1
            i = j
            continue
        elif line.startswith("runtime_dependencies:"):
            # S-08：派生运行时依赖，使 REGISTRY.json 与 SKILL.md frontmatter / 手册口径一致（SSOT）
            raw = line[len("runtime_dependencies:"):].strip().strip('"').strip("'")
            if raw and raw.lower() != "none":
                runtime_deps = [x.strip() for x in raw.split(",") if x.strip()]
        i += 1
    return name, desc, metadata, runtime_deps


def collect_orchestrated():
    """从 stages.json 收集所有被编排的技能名（stages + alternates + cross_cutting）。"""
    p = os.path.join(ROOT, "qa-orchestrator", "stages.json")
    if not os.path.isfile(p):
        return set()
    with open(p, "r", encoding="utf-8") as f:
        doc = json.load(f)
    names = set()
    for st in doc.get("stages", []):
        names |= set(st.get("skills", []))
        names |= set(st.get("alternates", []))
    names |= set(doc.get("cross_cutting", []))
    return names


def tier_of(scripts, has_refs):
    """trust-tier 初判（可后续人工覆写 verified_by/last_verified）：
    - 3：纯文档（无脚本）
    - 2：有脚本但无 references（未充分文档化/验证）
    - 1：有脚本且有 references（成熟、可验证）
    """
    if not scripts:
        return 3
    return 1 if has_refs else 2


def load_evidence(path):
    """可选 CI 证据文件：{skill: {"pass": bool, "date": "YYYY-MM-DD"}}。
    由 tests/run_all_tests.py 末段写出，供 build_registry 回填 verified_by/last_verified。
    """
    if not path or not os.path.isfile(path):
        return {}
    try:
        d = json.load(open(path, "r", encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence", default=None,
                    help="可选 CI 证据文件（tests/run_all_tests.py 末段产出），"
                         "映射 skill→{pass,date}；T1 技能据此回填 last_verified")
    args = ap.parse_args()
    orchestrated = collect_orchestrated()
    evidence = load_evidence(args.evidence)
    today = datetime.date.today().isoformat()
    skills = []
    for d in sorted(os.listdir(ROOT)):
        sdir = os.path.join(ROOT, d)
        sk = os.path.join(sdir, "SKILL.md")
        if not os.path.isdir(sdir) or not os.path.isfile(sk):
            continue
        name, desc, metadata, runtime_deps = parse_frontmatter(sk)
        if not name:
            continue
        scripts = []
        sdir_scripts = os.path.join(sdir, "scripts")
        if os.path.isdir(sdir_scripts):
            scripts = sorted(f for f in os.listdir(sdir_scripts) if f.endswith(".py"))
        has_refs = os.path.isdir(os.path.join(sdir, "references"))
        # S-02：SKILL.md frontmatter 为 SSOT（metadata 优先，缺失回退派生）
        category = metadata.get("category") or (
            "agent" if name in ("qa-agent-eval", "qa-agent-security") else "traditional")
        stage = metadata.get("stage") or ""  # 8 阶段 dir / cross_cutting / agent_testing / orchestrator
        tier_raw = metadata.get("tier")
        tier = int(tier_raw) if (tier_raw and str(tier_raw).isdigit()) else tier_of(scripts, has_refs)
        # ---- P1-1 / T-02：verified_by / last_verified 策略回填 ----
        # T-02：tier-1 交付门禁升级为 manual:smoke（甲方验收前须人工冒烟）+ CI 自动化
        if tier == 1:
            ev = evidence.get(name)
            if isinstance(ev, dict) and ev.get("pass") is False:
                verified_by = "manual:smoke+ci:run_all_tests:fail"
            else:
                verified_by = "manual:smoke+ci:run_all_tests"
            last_verified = (ev.get("date") if isinstance(ev, dict) and ev.get("date")
                             else today)
        else:
            verified_by = "pending:see-§7"
            last_verified = ""
        skills.append({
            "name": name,
            "category": category,
            "stage": stage,
            "description": desc,
            "scripts": scripts,
            "has_references": has_refs,
            "tier": tier,
            "runtime_dependencies": runtime_deps,
            "verified_by": verified_by,
            "last_verified": last_verified,
            "orchestrated": name in orchestrated,
        })
    reg = {
        "version": 2,
        "generated_by": "build_registry.py",
        "count": len(skills),
        "skills": skills,
    }
    out = os.path.join(ROOT, "REGISTRY.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(reg, f, ensure_ascii=False, indent=2)
    print(f"[OK] 已生成注册中心: {out}（共 {len(skills)} 个技能）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
