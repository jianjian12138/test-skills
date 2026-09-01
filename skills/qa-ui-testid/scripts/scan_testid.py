#!/usr/bin/env python3
"""qa-ui-testid: 扫描前端项目，为缺失 data-testid 的交互元素批量生成唯一标识并写入。

解决痛点：UI 自动化脚本因页面重构大面积失效，根因是依赖 CSS/XPath。统一补 data-testid
后，选择器与结构解耦，重构无需改脚本。

实现：基于正则扫描 JSX/Vue/HTML 的「开标签」，对交互元素（button/a/input/select/textarea
或带事件处理器）且尚无 data-testid 的，按统一命名规则生成唯一 testid 并插入。
为安全起见，默认 --dry-run 只输出清单；确认无误后加 --write 才改文件。

用法:
    # 预览（不改文件）
    python scan_testid.py --project src --dry-run --out testid-manifest.md

    # 确认后写入
    python scan_testid.py --project src --write --out testid-manifest.md

命名规则：
    <语义来源>-<用途>，语义来源取 name/id/aria-label/placeholder/title，否则取标签名；
    同文件内冲突自动加 -2/-3 后缀；可选 --prefix 加模块前缀。
"""
import argparse
import os
import re
import json


INTERACTIVE_TAGS = {"button", "a", "input", "select", "textarea", "link"}
EVENT_HANDLERS = re.compile(r"\b(onClick|onChange|onSubmit|onPress|onTap|@click|v-on:click)\b")
TAG_RE = re.compile(r"<([a-zA-Z][\w.-]*)(\s[^>]*?)?>", re.DOTALL)
ATTR_RE = re.compile(r'([a-zA-Z_:][\w:.-]*)\s*=\s*("([^"]*)"|\'([^\']*)\'|\{[^}]*\})')


def slugify(text, max_len=24):
    text = str(text).strip().lower()
    text = re.sub(r"[^a-z0-9\u4e00-\u9fa5]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:max_len] or "el"


def make_testid(tag, attrs, prefix, used):
    source = ""
    for k, v in attrs.items():
        if k in ("name", "id", "aria-label", "placeholder", "title", "alt") and v:
            source = v
            break
    base = slugify(source) if source else tag.lower()
    cand = f"{prefix}{base}" if prefix else base
    # 唯一化
    final = cand
    i = 2
    while final in used:
        final = f"{cand}-{i}"
        i += 1
    used.add(final)
    return final


def parse_attrs(attr_str):
    attrs = {}
    if not attr_str:
        return attrs
    for m in ATTR_RE.finditer(attr_str):
        key = m.group(1)
        val = m.group(3) if m.group(3) is not None else (m.group(4) if m.group(4) is not None else "")
        attrs[key] = val
    return attrs


def scan_file(path, prefix, used_global):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    insertions = []  # (tag_text_start, tag_text_end, testid)
    # 收集所有开标签位置（逆序插入，避免偏移）
    for m in TAG_RE.finditer(content):
        full = m.group(0)
        tag = m.group(1)
        attr_str = m.group(2) or ""
        attrs = parse_attrs(attr_str)
        is_interactive = tag in INTERACTIVE_TAGS or bool(EVENT_HANDLERS.search(attr_str))
        if not is_interactive:
            continue
        if "data-testid" in attrs:
            continue
        # 排除自闭合纯展示 input type=hidden
        if attrs.get("type") == "hidden":
            continue
        testid = make_testid(tag, attrs, prefix, used_global)
        insertions.append((m.start(), m.end(), testid, tag))
    return content, insertions


def apply_insertions(content, insertions):
    # 逆序替换，避免位置偏移
    out = content
    for start, end, testid, _ in sorted(insertions, key=lambda x: x[0], reverse=True):
        seg = out[start:end]
        # 在最后一个 > 前插入属性（处理自闭合 />）
        if seg.rstrip().endswith("/>"):
            new_seg = seg[: -2].rstrip() + f' data-testid="{testid}" />'
        else:
            new_seg = seg[:-1].rstrip() + f' data-testid="{testid}">'
        out = out[:start] + new_seg + out[end:]
    return out


def main():
    ap = argparse.ArgumentParser(description="扫描前端代码补 data-testid")
    ap.add_argument("--project", required=True, help="前端项目目录")
    ap.add_argument("--ext", default=".tsx,.jsx,.vue,.html,.ts,.js", help="扫描扩展名")
    ap.add_argument("--prefix", default="", help="testid 模块前缀，如 login-")
    ap.add_argument("--dry-run", action="store_true", help="只输出清单，不改文件（默认）")
    ap.add_argument("--write", action="store_true", help="实际写入文件")
    ap.add_argument("--out", default="testid-manifest.md", help="元素清单输出路径")
    args = ap.parse_args()

    exts = [e.strip() for e in args.ext.split(",") if e.strip()]
    files = []
    for root, _, fs in os.walk(args.project):
        for fn in fs:
            if any(fn.endswith(e) for e in exts):
                files.append(os.path.join(root, fn))

    used_global = set()
    manifest = {"project": args.project, "files": []}
    total = 0
    for fp in files:
        content, insertions = scan_file(fp, args.prefix, used_global)
        if not insertions:
            continue
        rel = os.path.relpath(fp, args.project)
        entry = {"file": rel, "elements": [{"tag": t, "testid": tid} for _, _, tid, t in insertions]}
        manifest["files"].append(entry)
        total += len(insertions)
        if args.write and not args.dry_run:
            with open(fp, "w", encoding="utf-8") as f:
                f.write(apply_insertions(content, insertions))
            print(f"[write] {rel}: +{len(insertions)} testid")
        else:
            for _, _, tid, t in insertions:
                print(f"[dry] {rel}  <{t}> -> data-testid=\"{tid}\"")

    # 写清单 md
    lines = [f"# data-testid 元素清单（{'预览' if (args.dry_run or not args.write) else '已写入'}）",
             f"- 项目：{args.project}", f"- 计划/新增 testid 总数：{total}", ""]
    for fe in manifest["files"]:
        lines.append(f"## {fe['file']}")
        lines.append("")
        lines.append("| 元素 | data-testid |")
        lines.append("|---|---|")
        for el in fe["elements"]:
            lines.append(f"| {el['tag']} | {el['testid']} |")
        lines.append("")
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n[ok] 扫描文件 {len(files)} 个，命中 {total} 个待补元素；清单: {args.out}")
    if args.dry_run or not args.write:
        print("[info] 当前为预览模式，确认清单无误后加 --write 写入代码。")


if __name__ == "__main__":
    main()
