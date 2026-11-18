#!/usr/bin/env python3
"""一键防错同步脚本：将本完整包安全同步至本地 Git 仓库，自动清理大小写冲突的 skills/REGISTRY.json。"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def sync_to_target(target_repo: Path) -> None:
    # 本脚本位于 <包根>/skills/tools/，包根需上溯三级（parent^3）。
    # 原实现误用 parent（= skills/tools/），导致只同步 tools 子目录并把文件散落到目标根。
    src_root = Path(__file__).resolve().parents[2]
    if not (src_root / "skills" / "registry.json").exists():
        raise SystemExit(f"❌ 无法定位包根: {src_root}（缺少 skills/registry.json），请检查脚本位置")
    if not (target_repo / ".git").exists():
        print(f"⚠️ 提示: 目标路径 {target_repo} 下未检测到 .git 目录，将继续执行文件同步。")

    # 1. 移除会导致 Windows/macOS 冲突的大写 skills/REGISTRY.json。
    # 注意：大小写不敏感文件系统（Windows/macOS 默认）上 upper_reg.exists() 会命中小写
    # registry.json，必须比对 resolved 路径，避免误删正被使用的小写 registry.json。
    upper_reg = target_repo / "skills" / "REGISTRY.json"
    lower_reg = target_repo / "skills" / "registry.json"
    if upper_reg.exists():
        same_file = lower_reg.exists() and upper_reg.resolve() == lower_reg.resolve()
        if same_file:
            print("ℹ️ 当前为大小写不敏感文件系统，REGISTRY.json 即 registry.json，跳过删除")
        else:
            subprocess.run(["git", "rm", "-f", "skills/REGISTRY.json"], cwd=str(target_repo), check=False)
            if upper_reg.exists():
                upper_reg.unlink()
            print("✅ 已移除大小写冲突的 skills/REGISTRY.json")

    # 2. 同步全部文件（只增与更新，不删任何额外自定义文件）
    copied = 0
    for item in sorted(src_root.rglob("*")):
        if item.is_dir() or "__pycache__" in item.parts or item.suffix == ".pyc":
            continue
        rel = item.relative_to(src_root)
        dst = target_repo / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, dst)
        copied += 1

    print(f"✅ 已成功同步 {copied} 个完整文件至 {target_repo.resolve()}")
    print("👉 请执行: python3 -m unittest discover -s tests -p 'test_*.py' -v && python3 qaskills.py eval")


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    sync_to_target(target)
