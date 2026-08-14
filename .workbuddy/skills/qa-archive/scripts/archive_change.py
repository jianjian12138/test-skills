#!/usr/bin/env python3
"""Archive a change directory into a timestamped zip + manifest markdown.

Usage:
    python scripts/archive_change.py --change changes/登录模块v2 --out ./archives
"""
import argparse
import datetime
import json
import os
import sys
import zipfile


def _slug(name: str) -> str:
    # ascii-safe-ish slug for filename
    s = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name)
    return s or "change"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--change", required=True, help="change directory to archive")
    ap.add_argument("--out", required=True, help="output directory for archives")
    args = ap.parse_args()

    src = args.change
    if not os.path.isdir(src):
        print(f"[ERROR] 变更目录不存在: {src}", file=sys.stderr)
        return 2

    os.makedirs(args.out, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base = os.path.basename(os.path.normpath(src))
    slug = _slug(base)
    zip_path = os.path.join(args.out, f"{slug}_{ts}.zip")

    files = []
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, fnames in os.walk(src):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for fn in fnames:
                if fn.endswith(".pyc"):
                    continue
                full = os.path.join(root, fn)
                arc = os.path.relpath(full, src)
                z.write(full, arc)
                files.append((arc, os.path.getsize(full)))

    # manifest
    manifest = f"# 归档清单：{base}\n\n"
    manifest += f"- 归档时间：{ts}\n"
    manifest += f"- 源目录：`{os.path.abspath(src)}`\n"
    manifest += f"- 文件数：{len(files)}\n"
    manifest += f"- 归档包：`{os.path.basename(zip_path)}`\n\n"
    manifest += "## 文件清单\n\n"
    manifest += "| 路径 | 大小(B) |\n| --- | --- |\n"
    for arc, size in sorted(files):
        manifest += f"| {arc} | {size} |\n"
    manifest += "\n## 关键结论摘要\n\n- （由 qa-report / qa-release-check 结论回填）\n"

    man_path = os.path.join(args.out, f"{slug}_{ts}_manifest.md")
    with open(man_path, "w", encoding="utf-8") as f:
        f.write(manifest)

    print(f"[OK] 归档完成：{zip_path}（{len(files)} 文件）｜ 清单：{man_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
