#!/usr/bin/env python3
"""移动端测试环境体检：检查 Node / Python / Appium / JDK / Android SDK / Xcode 是否就位。

Usage:
    python scripts/check_env.py [--json] [--out env.md]

纯标准库实现（用 shutil.which 探测可执行文件），不引入第三方依赖。
输出一份「通过/缺失」清单，缺失项给出安装提示。
"""
import argparse
import json
import shutil
import sys


def which(name):
    return shutil.which(name) is not None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--out", help="Markdown 输出")
    args = ap.parse_args()

    checks = [
        ("Node.js", "node", "https://nodejs.org"),
        ("Python 3.8+", "python3", "https://python.org"),
        ("Appium", "appium", "npm i -g appium"),
        ("Appium UiAutomator2 驱动", None, "appium driver install uiautomator2 (Android)"),
        ("Appium XCUITest 驱动", None, "appium driver install xcuitest (iOS, 需 macOS)"),
        ("JDK", "java", "安装 JDK 11+"),
        ("Android SDK", "adb", "安装 Android SDK 并配 ANDROID_HOME"),
        ("Xcode (iOS, macOS)", "xcodebuild", "App Store 安装 Xcode"),
    ]

    results = []
    for label, exe, hint in checks:
        ok = bool(exe) and which(exe)
        results.append({"item": label, "ok": ok, "hint": hint if not ok else ""})

    if args.json:
        print(json.dumps({"env": results}, ensure_ascii=False, indent=2))
    else:
        print("# 移动端环境体检\n")
        for r in results:
            mark = "✅" if r["ok"] else "❌ 缺失"
            line = f"- {r['item']}: {mark}"
            if not r["ok"]:
                line += f"  → 安装：{r['hint']}"
            print(line)
        n_ok = sum(1 for r in results if r["ok"])
        print(f"\n通过 {n_ok}/{len(results)}；缺失项补齐后再跑移动端自动化。")

    if args.out:
        lines = ["# 移动端环境体检\n", "| 项目 | 状态 | 安装提示 |",
                 "| --- | --- | --- |"]
        for r in results:
            lines.append(f"| {r['item']} | {'✅' if r['ok'] else '❌缺失'} | {r['hint']} |")
        with open(args.out, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print(f"[OK] 已写出: {args.out}")
    return 0 if all(r["ok"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
