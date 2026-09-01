#!/usr/bin/env python3
"""防文档层漂移：校验 stages.json / SKILL.md / REGISTRY.json 三处技能清单一致。

退出码：0=一致；1=存在漂移（用于 CI 卡点）。

校验项：
  1. stages.json 中出现的技能（stages.skills + alternates + cross_cutting）
     必须全部出现在 REGISTRY.json 的 name 集合中。
  2. stages.json 中出现的技能必须全部在 SKILL.md 文本中被引用（避免"只在 json 不在文档"）。
  3. SKILL.md 路由表中出现的 qa-* 技能必须全部在 stages.json 中（避免"文档有 json 无"）。
  4. 【强化 V6】stages 中每个技能必须在磁盘上存在 <skills>/<name>/SKILL.md（避免"清单有目录无"）。
  5. 【强化 V6】同一阶段内 skills[] 与 alternates[] 不得出现同名（当前 qa-env-config 曾命中）。
  6. 【强化 V6】若存在提交态 signals/*.json，校验 schema（source/generated_at/signals 列表）。

注意（R-38 诚实边界）：`--strict-meta` / `--require-verified` 默认关闭。单跑本工具仅做上述
SSOT 三处一致性校验，**不强校验** frontmatter 完整性（version/metadata.tier）/ tier==1 的
verified_by 非空。要在 CI 强卡「未验证=自评」回潮，须显式加 `--require-verified --strict-meta`，
或走 `run_gates.py` 的整体接线（run_gates 已默认开启这两项强校验）。**单跑 check_drift 不等于全量门禁**。
"""
import argparse
import json
import os
import re
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_ROOT = os.path.dirname(SKILL_DIR)


def collect_stage_skills(doc):
    names = set()
    for st in doc.get("stages", []):
        names |= set(st.get("skills", []))
        names |= set(st.get("alternates", []))
    names |= set(doc.get("cross_cutting", []))
    return names


def collect_agent_skills(doc):
    """R-20/S-02：agent_testing 维度下声明的独立类目技能（dict 形式）。"""
    dim = doc.get("agent_testing", {})
    skills = dim.get("skills", {}) if isinstance(dim, dict) else {}
    return set(skills.keys())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stages", default=os.path.join(SKILL_DIR, "stages.json"))
    ap.add_argument("--skill-md", default=os.path.join(SKILL_DIR, "SKILL.md"))
    ap.add_argument("--registry", default=os.path.join(SKILLS_ROOT, "REGISTRY.json"))
    ap.add_argument("--strict-meta", action="store_true",
                    help="R-20: 额外校验每个 SKILL.md frontmatter 含 version 与 metadata.tier（默认关，避免历史技能批量告警）")
    ap.add_argument("--require-verified", action="store_true",
                    help="P1-1: 严格校验 tier==1 技能 verified_by 非空（默认关；CI 阶段性开启，防'未验证=自评'回潮）")
    args = ap.parse_args()

    with open(args.stages, "r", encoding="utf-8") as f:
        doc = json.load(f)
    stage_skills = collect_stage_skills(doc)
    agent_skills = collect_agent_skills(doc)

    registry = json.load(open(args.registry, "r", encoding="utf-8"))
    reg_names = {s.get("name") for s in registry.get("skills", [])}

    skill_md = open(args.skill_md, "r", encoding="utf-8").read()
    md_skills = set(re.findall(r"qa-[a-z0-9-]+", skill_md))

    problems = []

    # 1) stages ⊆ registry
    missing_reg = stage_skills - reg_names
    if missing_reg:
        problems.append(f"stages.json 技能未注册到 REGISTRY.json: {sorted(missing_reg)}")

    # 2) stages ⊆ SKILL.md 文本
    missing_md = stage_skills - md_skills
    if missing_md:
        problems.append(f"stages.json 技能未出现在 SKILL.md: {sorted(missing_md)}")

    # 3) SKILL.md 路由表技能 ⊆ stages（仅检查路由表区域内的 qa-*）
    m = re.search(r"## 生命周期路由表.*?(?=## 操作流程)", skill_md, re.S)
    table_region = m.group(0) if m else skill_md
    table_skills = set(re.findall(r"qa-[a-z0-9-]+", table_region))
    orphan_md = table_skills - stage_skills
    if orphan_md:
        problems.append(f"SKILL.md 路由表存在 stages.json 未定义的技能: {sorted(orphan_md)}")

    # 4) 磁盘存在性：每个 stage 技能须有 <skills>/<name>/SKILL.md
    missing_disk = []
    for name in sorted(stage_skills):
        sk = os.path.join(SKILLS_ROOT, name, "SKILL.md")
        if not os.path.isfile(sk):
            missing_disk.append(name)
    if missing_disk:
        problems.append(f"stages 技能缺少磁盘 SKILL.md: {missing_disk}")

    # 5) 同阶段 skills[] ∩ alternates[] 不得同名
    dup_in_stage = []
    for st in doc.get("stages", []):
        inter = set(st.get("skills", [])) & set(st.get("alternates", []))
        if inter:
            dup_in_stage.append(f"{st.get('id','?')}:{sorted(inter)}")
    if dup_in_stage:
        problems.append(f"存在技能同时列入 skills[] 与 alternates[]: {dup_in_stage}")

    # 6) 提交态 signals schema 校验（若存在）
    bad_sig = []
    for root, _, files in os.walk(SKILLS_ROOT):
        if os.path.basename(root) != "signals":
            continue
        for fn in files:
            if not fn.endswith(".json"):
                continue
            p = os.path.join(root, fn)
            try:
                d = json.load(open(p, "r", encoding="utf-8"))
            except Exception as e:
                bad_sig.append(f"{p}: 解析失败 {e}")
                continue
            if not isinstance(d, dict) or "source" not in d or "generated_at" not in d:
                bad_sig.append(f"{p}: 缺 source/generated_at")
            elif not isinstance(d.get("signals"), list):
                bad_sig.append(f"{p}: signals 非列表")
    if bad_sig:
        problems.append("signals schema 校验失败: " + "; ".join(bad_sig))

    # 7) R-20/S-02：agent_testing 维度声明一致性（独立类目技能须注册且存在磁盘）
    if agent_skills:
        missing_reg_a = agent_skills - reg_names
        if missing_reg_a:
            problems.append(f"agent_testing 技能未注册到 REGISTRY.json: {sorted(missing_reg_a)}")
        missing_disk_a = [n for n in sorted(agent_skills)
                          if not os.path.isfile(os.path.join(SKILLS_ROOT, n, "SKILL.md"))]
        if missing_disk_a:
            problems.append(f"agent_testing 技能缺少磁盘 SKILL.md: {missing_disk_a}")

    # 7a) P1-6：agent_testing 声明 emits_signals=true → 各 agent 技能脚本须含 emit_signal
    #     定义（治理孤岛消除：agent 信号须可被 qa-release-check 聚合）。
    agent_dim = doc.get("agent_testing", {}) if isinstance(doc.get("agent_testing"), dict) else {}
    if agent_dim.get("emits_signals"):
        for skill in sorted(agent_dim.get("skills", {}).keys()):
            sdir = os.path.join(SKILLS_ROOT, skill, "scripts")
            has_emit = False
            if os.path.isdir(sdir):
                for fn in os.listdir(sdir):
                    if fn.endswith(".py"):
                        try:
                            if "def emit_signal" in open(os.path.join(sdir, fn),
                                                         "r", encoding="utf-8").read():
                                has_emit = True
                                break
                        except Exception:
                            continue
            if not has_emit:
                problems.append(f"P1-6: agent_testing 声明 emits_signals 但 {skill} 脚本无 emit_signal 定义（信号契约未接入）")

    # 7b) P1-1（可选严格 --require-verified）：tier==1 技能必须已填 verified_by，
    #     否则视为"未验证=自评"观感回潮。
    if args.require_verified:
        unverified_t1 = [s.get("name") for s in registry.get("skills", [])
                         if s.get("tier") == 1 and not s.get("verified_by")]
        if unverified_t1:
            problems.append("P1-1(--require-verified): 以下 T1 技能 verified_by 为空: "
                            + ", ".join(sorted(unverified_t1)))

    # 8) R-20（可选严格）：每个 SKILL.md frontmatter 应含 version 与 metadata.tier
    if args.strict_meta:
        meta_problems = []
        for name in sorted(stage_skills | agent_skills):
            sk = os.path.join(SKILLS_ROOT, name, "SKILL.md")
            if not os.path.isfile(sk):
                continue
            fm = open(sk, "r", encoding="utf-8").read()
            # 取首个 frontmatter 块（--- ... ---）
            m = re.match(r"^---\s*\n(.*?)\n---\s*\n", fm, re.S)
            block = m.group(1) if m else ""
            has_version = bool(re.search(r"(?m)^\s*version\s*:", block))
            has_tier = "tier" in block
            if not has_version or not has_tier:
                meta_problems.append(f"{name}(version={has_version},tier={has_tier})")
        if meta_problems:
            problems.append("SKILL.md 缺 version/tier（strict-meta）: " + "; ".join(meta_problems))

    # 9) P1-4 SSOT：全仓所有 def emit_signal 函数体须字节一致（含 vendored _common.py 与
    #    13 份内联副本），且 vendored _common.py 须含 schema_version。
    #    防「签名漂移」（skill vs source、缺 signals_dir 默认）复发。
    def extract_emit_signal(text):
        """提取文本中首个 def emit_signal 整段（到下一个缩进0非空行或空行止）。"""
        lines = text.split("\n")
        out, cap = [], False
        for ln in lines:
            if ln.startswith("def emit_signal"):
                cap, out = True, [ln]
                continue
            if cap:
                if ln == "" or (ln and not ln[0].isspace()):
                    break
                out.append(ln)
        return "\n".join(out) if out else None

    emit_bodies = {}
    common_files = []
    for root, _, files in os.walk(SKILLS_ROOT):
        if os.path.basename(root) != "scripts":
            continue
        if not os.path.isfile(os.path.join(os.path.dirname(root), "SKILL.md")):
            continue
        for fn in files:
            if not fn.endswith(".py"):
                continue
            p = os.path.join(root, fn)
            try:
                t = open(p, "r", encoding="utf-8").read()
            except Exception as e:
                problems.append(f"脚本读取失败 {p}: {e}")
                continue
            if "def emit_signal" in t:
                body = extract_emit_signal(t)
                if body is not None:
                    emit_bodies.setdefault(body, []).append(os.path.relpath(p, SKILLS_ROOT))
            if fn == "_common.py":
                common_files.append(p)
    if emit_bodies:
        if len(emit_bodies) != 1:
            detail = "; ".join("%d×[%s]" % (len(v), ", ".join(v[:3])
                                            + ("…" if len(v) > 3 else ""))
                               for v in emit_bodies.values())
            problems.append(f"emit_signal 函数体字节不一致（差异份数={len(emit_bodies)}）：{detail}（P1-4 SSOT 防漂移）")
    else:
        problems.append("未找到任何 emit_signal 定义（R-24/S-03 基线缺失）")
    if common_files:
        refs = set()
        for cf in common_files:
            try:
                refs.add(open(cf, "r", encoding="utf-8").read())
            except Exception as e:
                problems.append(f"_common.py 读取失败 {cf}: {e}")
        if len(refs) != 1:
            problems.append(f"vendored _common.py 字节不一致（份数={len(common_files)}，差异={len(refs)}），违反 R-24/S-03 防漂移")
        elif "schema_version" not in next(iter(refs)):
            problems.append("vendored _common.py 缺少 schema_version 字段（与 signal-schema.md 不一致，RK-12）")
    else:
        problems.append("未找到任何 vendored _common.py（R-24/S-03 防漂移基线缺失）")

    # 10) RK-12/13：机器可读 JSON Schema 合法
    schema_json = os.path.join(SKILLS_ROOT, "references", "signal-schema.json")
    if os.path.isfile(schema_json):
        try:
            sj = json.load(open(schema_json, "r", encoding="utf-8"))
            if "$schema" not in sj or sj.get("type") != "object":
                problems.append("signal-schema.json 非合法 JSON Schema（缺 $schema/type）")
        except Exception as e:
            problems.append(f"signal-schema.json 解析失败: {e}")
    else:
        problems.append("references/signal-schema.json 缺失（RK-12 机器可读契约）")

    # 11) RK-14 / S-03：references 引用须存在（防渐进披露沦为死链）。
    #     覆盖：SKILL.md 中的 Markdown 链接、显式文件路径提及（含反引号包裹 `references/xxx.ext`）、
    #     以及 references/*.md 内部对其他 references 文件的引用——统一做「内部存在性」校验。
    #     解析规则：先按技能本地 references/ 解析，再回退到仓库共享 references/（按 basename），
    #     覆盖 ai-false-pass.md / signal-schema.* 这类跨技能共享文档（S-02 反引号盲点修复）。
    REF_RE = re.compile(r"(?:\(|\s|`)(references/[A-Za-z0-9_./\-]+\.[A-Za-z0-9]+)")
    dead_links = set()
    for root, _, files in os.walk(SKILLS_ROOT):
        if "SKILL.md" not in files:
            continue
        sk_md = os.path.join(root, "SKILL.md")
        try:
            md = open(sk_md, "r", encoding="utf-8").read()
        except Exception:
            continue
        # Markdown 链接（原有）+ 显式文件路径提及（扩展）
        for m in re.finditer(r"\]\((references/[^)]+)\)", md):
            rel = m.group(1)
            target = os.path.normpath(os.path.join(root, rel))
            if not os.path.isfile(target):
                dead_links.add("%s -> %s" % (os.path.relpath(sk_md, SKILLS_ROOT), rel))
        for m in REF_RE.finditer(md):
            rel = m.group(1)
            target = os.path.normpath(os.path.join(root, rel))
            shared = os.path.normpath(os.path.join(SKILLS_ROOT, "references", os.path.basename(rel)))
            if not os.path.isfile(target) and not os.path.isfile(shared):
                dead_links.add("%s -> %s" % (os.path.relpath(sk_md, SKILLS_ROOT), rel))
        # references/*.md 内部引用（S-03 扩展：references 内部存在性）
        refdir = os.path.join(root, "references")
        if os.path.isdir(refdir):
            for fn in sorted(os.listdir(refdir)):
                if not fn.endswith(".md"):
                    continue
                rp = os.path.join(refdir, fn)
                try:
                    rmd = open(rp, "r", encoding="utf-8").read()
                except Exception:
                    continue
                for m in re.finditer(r"\]\((references/[^)]+)\)", rmd):
                    rel = m.group(1)
                    target = os.path.normpath(os.path.join(refdir, rel))
                    if not os.path.isfile(target):
                        dead_links.add("%s -> %s" % (os.path.relpath(rp, SKILLS_ROOT), rel))
                for m in REF_RE.finditer(rmd):
                    rel = m.group(1)
                    target = os.path.normpath(os.path.join(root, rel))
                    shared = os.path.normpath(os.path.join(SKILLS_ROOT, "references", os.path.basename(rel)))
                    if not os.path.isfile(target) and not os.path.isfile(shared):
                        dead_links.add("%s -> %s" % (os.path.relpath(rp, SKILLS_ROOT), rel))
    if dead_links:
        problems.append("references 死链（引用不存在）: " + "; ".join(sorted(dead_links)))

    # 12) RK-P3-17：关键入口脚本存在性（路由 / 三道闸 / 安全扫描 / 红队执行器）
    # 防止"REGISTRY / 文档声明了某能力，但其脚本被误删"的漂移。
    entry_scripts = [
        "qa-orchestrator/scripts/route_next.py",
        "qa-orchestrator/scripts/route_agent.py",
        "qa-orchestrator/scripts/close_loop.py",
        "qa-orchestrator/scripts/check_drift.py",
        "tools/validate_portability.py",
        "tests/run_all_tests.py",
        "qa-security-scan/scripts/scan_secrets.py",
        "qa-agent-security/scripts/run_attacks.py",
    ]
    missing_scripts = [s for s in entry_scripts
                       if not os.path.isfile(os.path.join(SKILLS_ROOT, s))]
    if missing_scripts:
        problems.append("关键入口脚本缺失: " + "; ".join(missing_scripts))

    # 13) P0-A：阶段产物契约一致性——stages.json 声明（非可选阶段）的 artifacts
    # 必须在其主技能 SKILL.md 中被声明（作为文件名出现），避免「技能写错产物文件名
    # 却无人察觉」的契约漂移（治黑洞：写错名→阶段永远未完成）。
    contract_problems = []
    for st in doc.get("stages", []):
        if st.get("optional"):
            continue
        primary = st["skills"][0]
        arts = st.get("artifacts") or []
        if not arts:
            continue
        sk_md_path = os.path.join(SKILLS_ROOT, primary, "SKILL.md")
        if not os.path.isfile(sk_md_path):
            continue  # 由规则 4 覆盖
        md_text = open(sk_md_path, "r", encoding="utf-8").read()
        missing = [a for a in arts if a not in md_text]
        if missing:
            contract_problems.append(
                f"阶段 {st['dir']} 主技能 {primary} 的 SKILL.md 未声明产物契约 {missing}"
                f"（stages.json artifacts 须在其 SKILL.md 中出现）")
    if contract_problems:
        problems.append("阶段产物契约不一致: " + "; ".join(contract_problems))

    # 13b) P1-5：契约语义——signal-schema.json 须含 blocking→severity 语义约束，
    #        且若仓库内存在 signals/*.json，其每条 blocking=true 信号必须声明有效 severity。
    SEV_ENUM = {"critical", "high", "medium", "low", "info"}
    if os.path.isfile(schema_json):
        try:
            sj = json.load(open(schema_json, "r", encoding="utf-8"))
        except Exception:
            sj = None
        has_constraint = False
        if isinstance(sj, dict):
            # 约束位于 definitions.signal.allOf（应用在每个 signal 对象上）
            sig_def = sj.get("definitions", {}).get("signal", {})
            for r in sig_def.get("allOf", []):
                cond = (r.get("if") or {}).get("properties", {}).get("blocking")
                if isinstance(cond, dict) and cond.get("const") is True:
                    then = r.get("then", {})
                    if "severity" in (then.get("required", [])):
                        sev_enum = (then.get("properties", {}).get("severity") or {}).get("enum")
                        if sev_enum and SEV_ENUM.issubset(set(sev_enum)):
                            has_constraint = True
                            break
        if not has_constraint:
            problems.append("signal-schema.json 缺少 blocking→severity 语义约束"
                            "（P1-5：blocking 为唯一阻断权威，须约束 blocking=true 时 severity 有效）")
        # 对仓库内已提交的 signals 做语义校验（运行时生成的 signals 不在此目录内）
        for root, _, files in os.walk(SKILLS_ROOT):
            if os.path.basename(root) != "signals":
                continue
            for fn in files:
                if not fn.endswith(".json"):
                    continue
                p = os.path.join(root, fn)
                try:
                    d = json.load(open(p, "r", encoding="utf-8"))
                except Exception:
                    continue
                for sig in d.get("signals", []):
                    if sig.get("blocking") is True and sig.get("severity") not in SEV_ENUM:
                        problems.append(f"{p}: blocking=true 但 severity={sig.get('severity')!r} 无效/缺失（P1-5 语义）")

    # 14) R-02/S-02 SSOT：每个 SKILL.md 的 metadata(category/stage/tier) 必须与 REGISTRY.json
    #     一致。REGISTRY 由 SKILL.md 派生，编辑 metadata 后必须重跑 build_registry，否则此处漂移。
    #     把 golden S-02 的 SSOT 校验下沉为常驻漂移卡点（即便只跑 check_drift 也能卡住）。
    def derive_meta(sk_path):
        try:
            t = open(sk_path, "r", encoding="utf-8").read()
        except Exception:
            return None
        m = re.match(r"^---\s*\n(.*?)\n---\s*\n", t, re.S)
        if not m:
            return None
        fm = m.group(1)
        meta, name, lines = {}, None, fm.splitlines()
        i = 0
        while i < len(lines):
            ln = lines[i]
            if ln.strip() == "metadata:":
                j = i + 1
                while j < len(lines) and (lines[j].startswith(" ") or lines[j].startswith("\t")):
                    sub = lines[j].strip()
                    if ":" in sub:
                        k, _, v = sub.partition(":")
                        meta[k.strip()] = v.strip()
                    j += 1
                break
            if ln.startswith("name:"):
                name = ln[len("name:"):].strip()
            i += 1
        sdir = os.path.join(os.path.dirname(sk_path), "scripts")
        scripts = [f for f in os.listdir(sdir)] if os.path.isdir(sdir) else []
        has_refs = os.path.isdir(os.path.join(os.path.dirname(sk_path), "references"))
        cat = meta.get("category") or ("agent" if name in ("qa-agent-eval", "qa-agent-security") else "traditional")
        stage = meta.get("stage") or ""
        tr = meta.get("tier")
        tier = int(tr) if (tr and str(tr).isdigit()) else (3 if not scripts else (1 if has_refs else 2))
        return {"name": name, "category": cat, "stage": stage, "tier": tier}

    reg_by_name = {s.get("name"): s for s in registry.get("skills", [])}
    meta_problems = []
    for d in sorted(os.listdir(SKILLS_ROOT)):
        sk = os.path.join(SKILLS_ROOT, d, "SKILL.md")
        if not os.path.isfile(sk):
            continue
        dm = derive_meta(sk)
        if dm is None or not dm["name"]:
            continue
        reg = reg_by_name.get(dm["name"])
        if reg is None:
            meta_problems.append(f"{dm['name']}: 磁盘存在但 REGISTRY 未注册（REGISTRY 脱管）")
            continue
        for key in ("category", "stage", "tier"):
            if reg.get(key) != dm[key]:
                meta_problems.append(
                    f"{dm['name']}: metadata.{key}={dm[key]!r} 与 REGISTRY={reg.get(key)!r} 不一致"
                    f"（编辑后须重跑 build_registry.py）")
    if meta_problems:
        problems.append("metadata↔REGISTRY 不一致(S-02 SSOT): " + "; ".join(meta_problems))

    if problems:
        print("[DRIFT] 文档层漂移 detected:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"[OK] 无漂移：stages={len(stage_skills)} 项，REGISTRY={len(reg_names)} 项，SKILL.md 引用一致，磁盘存在性/重复/信号 schema 校验通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
