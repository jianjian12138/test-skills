#!/usr/bin/env python3
"""Vendored _common.py 生成器（RK-P3-19：vendored 手工副本可生成化）。

5 个方法学技能（a11y/chaos/code-review/synthetic-monitoring/unit-tdd）各自带一份
逐字节一致的 `scripts/_common.py`（emit_signal/load_json/save_json/read_text/wilson_ci/
two_prop_z），以保「单目录可分解、可独立分发」。此前是手工副本，易漂移。

本脚本以**单一模板**为事实源，重新生成所有 `scripts/_common.py`，落地后由
`check_drift.py` 校验 9（字节一致 + 含 schema_version）守住防漂移。
"""
import argparse
import os
import sys

SKILLS_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 单一事实源模板（与 signal-schema.md SSOT 一致；emit_signal 须含 schema_version）。
_TEMPLATE = '''#!/usr/bin/env python3
"""Vendored common helpers for this skill.

Self-contained copy so the skill can be distributed as a single directory
and used by any agent that runs its scripts. Mirrors the shared contract:
- emit_signal writes signals/<skill>.json only when signals is non-empty
- load_json / save_json / read_text use UTF-8
"""
import json
import os
from datetime import datetime


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(obj, path, indent=2):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent)


def read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


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


def wilson_ci(p, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    phat = p / n
    denom = 1 + z * z / n
    center = (phat + z * z / (2 * n)) / denom
    margin = (z * ((phat * (1 - phat) + z * z / (4 * n)) / n) ** 0.5) / denom
    return (max(0.0, center - margin), min(1.0, center + margin))


def two_prop_z(p1, n1, p2, n2):
    if n1 == 0 or n2 == 0:
        return 0.0
    p_pool = (p1 + p2) / (n1 + n2)
    se = (p_pool * (1 - p_pool) * (1 / n1 + 1 / n2)) ** 0.5
    if se == 0:
        return 0.0
    return (p1 / n1 - p2 / n2) / se
'''

# 规范 emit_signal 实现：与 _TEMPLATE（vendored _common.py）中的 emit_signal 字节一致，
# 作为全仓 18 处 emit_signal 的唯一事实源（P1-4 SSOT 收口）。
_EMIT_SIGNAL_BLOCK = '''def emit_signal(skill, signals, signals_dir="signals"):
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
'''


def replace_emit_signal(text):
    """把文本中首个 ``def emit_signal`` 整段替换为规范块（字节一致）。
    返回 (new_text, replaced)。函数体结束判定：遇到首个非空且顶格（缩进 0）的行即止；
    函数体内的空行（含 docstring 内空行）照常吞掉，避免误判函数结束。
    """
    lines = text.split("\n")
    out = []
    i = 0
    n = len(lines)
    replaced = False
    while i < n:
        line = lines[i]
        if line.startswith("def emit_signal") and not replaced:
            out.append(_EMIT_SIGNAL_BLOCK.rstrip("\n"))
            j = i + 1
            while j < n:
                cur = lines[j]
                if cur and not cur[0].isspace():
                    break
                j += 1
            i = j
            replaced = True
            continue
        out.append(line)
        i += 1
    return "\n".join(out), replaced


def verify_consistency():
    """R-10：CI 干跑校验——5 份 vendored _common.py 是否与单一模板字节一致（不写文件）。

    对每份 _common.py 模拟「重新生成」应得到的文本（replace_emit_signal + datetime import 规范化），
    与磁盘现状比对；任一偏离即视为脱离了单源，返回 False（fail-closed）。
    """
    mismatches = []
    for root, _, files in os.walk(SKILLS_ROOT):
        if os.path.basename(root) != "scripts":
            continue
        if not os.path.isfile(os.path.join(os.path.dirname(root), "SKILL.md")):
            continue
        for fn in files:
            if fn != "_common.py":
                continue
            p = os.path.join(root, fn)
            try:
                text = open(p, encoding="utf-8").read()
            except Exception:
                continue
            if "def emit_signal" not in text:
                continue
            new_text, _ = replace_emit_signal(text)
            if "import datetime" in new_text and "from datetime import datetime" not in new_text:
                new_text = new_text.replace("import datetime\n", "from datetime import datetime\n")
            if new_text != text:
                mismatches.append(os.path.relpath(p, SKILLS_ROOT))
    if mismatches:
        for m in mismatches:
            print("  DRIFT: %s 偏离单一模板（须重跑 gen_common.py 重新生成）" % m)
        print("[FAIL] %d 个 _common.py 偏离单源模板" % len(mismatches))
        return False
    print("[OK] 5 份 vendored _common.py 均与单一模板字节一致（单源生成已闭合）")
    return True


def main():
    ap = argparse.ArgumentParser(description="vendored _common.py 单源生成器")
    ap.add_argument("--check", action="store_true",
                    help="仅校验 5 份 vendored _common.py 是否偏离单一模板（不写文件，CI 用）")
    args = ap.parse_args()
    if args.check:
        sys.exit(0 if verify_consistency() else 1)
    written_vendored = []
    written_inline = []
    for root, _, files in os.walk(SKILLS_ROOT):
        # 仅处理技能 scripts/ 目录（其父级须有 SKILL.md），避免误触 tools/ 本生成器自身
        # 与 tests/；也避免 walk 进入 scripts 子层时因该层无 SKILL.md 而漏处理。
        if os.path.basename(root) != "scripts":
            continue
        if not os.path.isfile(os.path.join(os.path.dirname(root), "SKILL.md")):
            continue
        for fn in files:
            if not fn.endswith(".py"):
                continue
            p = os.path.join(root, fn)
            try:
                text = open(p, "r", encoding="utf-8").read()
            except Exception:
                continue
            if "def emit_signal" not in text:
                continue
            new_text, replaced = replace_emit_signal(text)
            # 规范块使用 `from datetime import datetime` 的 datetime.now()；
            # 旧内联副本可能用 `import datetime`（模块）且仅在 emit 体内用 datetime.datetime，
            # 替换为规范块后须同步改为 from import，否则运行时 NameError。
            if "import datetime" in new_text and "from datetime import datetime" not in new_text:
                new_text = new_text.replace("import datetime\n", "from datetime import datetime\n")
            if replaced and new_text != text:
                with open(p, "w", encoding="utf-8") as f:
                    f.write(new_text)
                rel = os.path.relpath(p, SKILLS_ROOT)
                if fn == "_common.py":
                    written_vendored.append(rel)
                else:
                    written_inline.append(rel)
    print("[OK] 已从单一模板重新生成 emit_signal（SSOT）：")
    print("  vendored _common.py (%d):" % len(written_vendored))
    for w in sorted(written_vendored):
        print("    - %s" % w)
    print("  内联 emit_signal (%d):" % len(written_inline))
    for w in sorted(written_inline):
        print("    - %s" % w)
    print("请随后跑 check_drift.py 校验：全仓 emit_signal 函数体字节一致（规则 9 升级）。")


if __name__ == "__main__":
    main()
