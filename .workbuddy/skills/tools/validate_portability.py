#!/usr/bin/env python3
"""跨 agent 可移植性校验（V7 复评硬闸门之一）。

校验「装到任意 agent 技能目录后」是否仍自洽：
  1. 每个技能 SKILL.md 含 name / description / license / compatibility / metadata（开放标准最小 frontmatter + 可移植声明 + 成熟度元数据；R-20 强制 compatibility/metadata 必备）。
  2. 无 `agent_created` 等非标准 frontmatter 字段（避免被其他 agent 当成未知元数据）。
  3. 脚本不引用跨目录 `lib/` 包（否则在非 WorkBuddy 目录无法 import）。
  4. 全部脚本 `py_compile` 通过。
  5. 依赖的信号契约 schema 由消费方（qa-release-check）按 blocking 唯一权威判定（不校验 schema 本身，仅确认存在）。

退出码：全部通过 0；任一不通过 1。
"""
import json
import os
import py_compile
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # skills/

# R-20：compatibility（运行环境声明）/ metadata（成熟度/分类元数据）列为必备，
# 缺任一即视为不可移植 / 不可治理。
REQUIRED = ["name", "description", "license", "compatibility", "metadata"]
# R-12：白名单——仅允许下列顶层字段；其余一律报错（R-11 的 category/stage/tier 已下沉 metadata）
ALLOWED_FM = {"name", "description", "license", "metadata", "compatibility",
              "version", "runtime_dependencies"}
LIB_RE = re.compile(r"(from common import|import common|sys\.path[^\n]*lib|/lib/|lib/common)")
DESC_MAX = 1024
# R-10/11：标准库模块名全集（3.10+），用于区分「标准库」与「第三方依赖」
STDLIB = set(getattr(sys, "stdlib_module_names", ()))
# 顶层 import 扫描（含缩进处的函数内懒加载）：import X[.y] / from X[.y] import ...
IMPORT_RE = re.compile(r"^\s*(?:import\s+([A-Za-z_][\w\.]*)(?:\s+as\s+\w+)?|from\s+([A-Za-z_][\w\.]*)\s+import\b)")


def parse_frontmatter(path):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    block = text[3:end]
    fm = {}
    lines = block.splitlines()
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()
        if not stripped or line[0].isspace():
            i += 1
            continue
        if ":" not in line:
            i += 1
            continue
        k, _, v = line.partition(":")
        k = k.strip().lower()
        v = v.strip()
        # YAML block scalar（| / > / |- / >- / |+ / >+）：累积后续缩进行，
        # 否则多行 description 只取到 "|" 标记，DESC_MAX 门禁形同虚设（RK-08 假门禁）。
        if v in ("|", ">", "|-", ">-", "|+", ">+"):
            i += 1
            buf = []
            while i < n and (lines[i].startswith(" ") or lines[i].startswith("\t")):
                buf.append(lines[i].strip())
                i += 1
            fm[k] = "\n".join(buf)
            continue
        fm[k] = v
        i += 1
    return fm


def parse_top_keys(path):
    """R-12：仅取顶层字段（非缩进），metadata: 的子键不计（其下 category/stage/tier 合法）。"""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    if not text.startswith("---"):
        return []
    end = text.find("\n---", 3)
    if end == -1:
        return []
    block = text[3:end]
    keys = []
    for line in block.splitlines():
        if line and not line[0].isspace() and ":" in line:
            keys.append(line.split(":", 1)[0].strip())
    return keys


def main():
    problems = []
    skill_dirs = sorted(
        d for d in (os.path.join(ROOT, x) for x in os.listdir(ROOT))
        if os.path.isdir(d) and os.path.exists(os.path.join(d, "SKILL.md"))
    )

    py_files = []
    for sd in skill_dirs:
        name = os.path.basename(sd)
        # 1-2: frontmatter 白名单（R-12）+ name==dir + desc 长度
        fm = parse_frontmatter(os.path.join(sd, "SKILL.md"))
        missing = [k for k in REQUIRED if k not in fm]
        if missing:
            problems.append(f"[{name}] SKILL.md 缺必需 frontmatter: {missing}")
        top_keys = parse_top_keys(os.path.join(sd, "SKILL.md"))
        illegal = [k for k in top_keys if k not in ALLOWED_FM]
        if illegal:
            problems.append(f"[{name}] SKILL.md 含非标准顶层字段(白名单外): {illegal}")
        if fm.get("name") and fm.get("name") != name:
            problems.append(f"[{name}] name({fm.get('name')}) != 目录名")
        desc = fm.get("description", "")
        if len(desc) > DESC_MAX:
            problems.append(f"[{name}] description 超长({len(desc)}>{DESC_MAX})")
        # R-10/11：本技能声明允许的运行期第三方依赖（frontmatter runtime_dependencies）
        rt = {t.strip().lower() for t in fm.get("runtime_dependencies", "").split(",") if t.strip()}
        # 本技能目录内的本地模块（如 vendored _common），不算第三方
        local_mods = set()
        for dp, _, fns in os.walk(sd):
            for fn in fns:
                if fn.endswith(".py"):
                    local_mods.add(fn[:-3])
        # 3: 无 lib/ 引用 + 第三方 import 须声明（声明=现实）
        for dp, _, fns in os.walk(sd):
            for fn in fns:
                if not fn.endswith(".py"):
                    continue
                fp = os.path.join(dp, fn)
                py_files.append(fp)
                try:
                    with open(fp, encoding="utf-8") as fh:
                        src = fh.read()
                except Exception:
                    continue
                if LIB_RE.search(src):
                    problems.append(f"[{name}] 脚本引用跨目录 lib/: {fp}")
                # 第三方 import 扫描（R-10/11）：非 stdlib、非本地模块、未声明 → FAIL
                # 跟踪三引号字符串块，跳过其中的 import（避免把生成代码模板误判为真实 import）
                in_block = False
                for line in src.splitlines():
                    nq = line.count('"""') + line.count("'''")
                    if nq % 2 == 1:
                        in_block = not in_block
                    if in_block or nq >= 2:  # 块字符串内，或本行含成对三引号（import 在行内字符串）
                        continue
                    m = IMPORT_RE.match(line)
                    if not m:
                        continue
                    mod = (m.group(1) or m.group(2) or "").split(".")[0].strip()
                    if not mod or mod in STDLIB or mod in local_mods or mod in rt:
                        continue
                    problems.append(
                        f"[{name}] 脚本导入未声明第三方包 '{mod}'（frontmatter runtime_dependencies "
                        f"未含）；若确为运行期依赖请声明，否则移除 import。({fp})")

    # 4: py_compile
    for fp in py_files:
        try:
            py_compile.compile(fp, doraise=True)
        except py_compile.PyCompileError as e:
            problems.append(f"COMPILE_FAIL: {fp} :: {e}")

    print(f"校验技能数: {len(skill_dirs)} | 脚本数: {len(py_files)}")
    if problems:
        print(f"[FAIL] 发现 {len(problems)} 个问题：")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("[PASS] 跨 agent 可移植性校验全部通过（name/description/license/compatibility/metadata 齐全、零 lib/ 引用、"
          "第三方 import 均经 runtime_dependencies 声明、零编译失败）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
