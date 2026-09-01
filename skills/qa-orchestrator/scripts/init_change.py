#!/usr/bin/env python3
"""qa-orchestrator: 为每个待测「变更」建立标准化产物目录树（闭环版）。

用法:
    python init_change.py --base <工作区根> --change "<变更名或需求ID>" [--author <测试人>]

会在 <base>/changes/<change_slug>/ 下创建统一目录结构、README 状态看板与 ROUTING.md。
阶段定义来自 stages.json（单一事实源，修复 P0-B 三处硬编码漂移）。
"""
import argparse
import os
import re
import datetime

import _stages

STAGES = _stages.load_stages()


def slugify(text: str, max_len: int = 40) -> str:
    s = re.sub(r"[^\w一-鿿-]+", "-", text.strip().lower())
    s = re.sub(r"-+", "-", s).strip("-")
    return s[:max_len] or "change"


def build_readme(change: str, author: str, slug: str) -> str:
    today = datetime.date.today().isoformat()
    rows = []
    for idx, st in enumerate(STAGES, 1):
        sk = " · ".join(st["skills"] + st.get("alternates", []))
        rows.append(f"| {idx} | {st['dir']} | {st['title']} | {sk} | 待开始 | - |")
    row_block = "\n".join(rows)
    return f"""# 测试变更工作区：{change}

- **变更标识**：`{slug}`
- **负责人**：{author or '待定'}
- **创建日期**：{today}
- **状态**：进行中

## 阶段状态看板

| # | 阶段目录 | 阶段名 | 可用技能 | 状态 | 产物 |
|---|---|---|---|---|---|
{row_block}

## 产物索引

（每完成一个阶段，在此追加本次产物文件链接与结论摘要；可用 `route_next.py` 推断下一步）

## 备注

- 需求/用例/接口/执行/报告统一归集于此，禁止散落到临时聊天。
- 路由规则详见 `ROUTING.md` 与本技能说明。
- 一键推进：`python scripts/close_loop.py --change changes/{slug}`
"""


def build_routing() -> str:
    lines = ["# 测试技能路由表（ROUTING）\n",
             "变更目录 → 阶段 → 推荐技能 → 典型产物。\n"]
    lines.append("| 阶段目录 | 阶段名 | 推荐技能 | 典型产物 |")
    lines.append("| --- | --- | --- | --- |")
    for st in STAGES:
        sk = " · ".join(st["skills"] + st.get("alternates", []))
        arts = " / ".join(st.get("artifacts", []))
        lines.append(f"| {st['dir']} | {st['title']} | {sk} | {arts} |")
    lines.append("")
    lines.append("## 自动推断\n")
    lines.append("- `scripts/route_next.py --change <dir> --auto` → 输出下一步技能名。\n")
    lines.append("- `scripts/close_loop.py --change <dir>` → 按序推进到归档（含质量闭合判定）。\n")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="初始化测试变更工作区（闭环版）")
    ap.add_argument("--base", required=True, help="工作区根目录")
    ap.add_argument("--change", required=True, help="变更名或需求ID")
    ap.add_argument("--author", default="", help="测试负责人")
    args = ap.parse_args()

    slug = slugify(args.change)
    root = os.path.join(args.base, "changes", slug)
    os.makedirs(root, exist_ok=True)

    for st in STAGES:
        os.makedirs(os.path.join(root, st["dir"]), exist_ok=True)

    readme_path = os.path.join(root, "README.md")
    if not os.path.exists(readme_path):
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(build_readme(args.change, args.author, slug))

    routing_path = os.path.join(root, "ROUTING.md")
    if not os.path.exists(routing_path):
        with open(routing_path, "w", encoding="utf-8") as f:
            f.write(build_routing())

    print(f"[ok] 变更工作区已创建: {root}")
    for st in STAGES:
        print(f"  - {st['dir']}/  ({st['title']})")
    print(f"[ok] 已生成 README.md 与 ROUTING.md")


if __name__ == "__main__":
    main()
