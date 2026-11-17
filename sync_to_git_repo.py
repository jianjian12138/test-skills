#!/usr/bin/env python3
"""一键防错同步脚本：将本完整包安全同步至本地 Git 仓库，自动清理大小写冲突的 skills/REGISTRY.json。"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def sync_to_target(target_repo: Path) -> None:
    src_root = Path(__file__).resolve().parent
    if not (target_repo / ".git").exists():
        print(f"⚠️ 提示: 目标路径 {target_repo} 下未检测到 .git 目录，将继续执行文件同步。")

    # 1. 移除会导致 Windows/macOS 冲突的大写 skills/REGISTRY.json
    upper_reg = target_repo / "skills" / "REGISTRY.json"
    if upper_reg.exists():
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
