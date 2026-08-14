#!/usr/bin/env python3
"""移动端失败诊断决策树：给定症状，输出排查步骤（一次只改一个变量）。

Usage:
    python scripts/fault_diagnosis.py --symptom "元素找不到" [--json]

症状 → 决策路径（节选，覆盖最常见失败）：
  - 元素找不到 / NoSuchElement     → 定位金字塔上移 / 推动加 testID / 查 WebView 是否切回原生
  - 崩溃 / Crash                   → 抓 logcat / 看 ANR / 内存 / 是否新权限
  - 超时 / Timeout                 → 去 sleep 改显式等待 / 查网络 / 查异步
  - 断言失败                       → 先查数据/环境，再查业务；勿先改业务代码
  - 混合 App H5 失效              → 测完 H5 必须回 NATIVE_APP 上下文
"""
import argparse
import json
import sys

TREE = {
    "元素找不到": [
        "1. 用定位金字塔上移：优先 accessibility id，避免在 L5 XPath",
        "2. 推动开发给该元素加 testID（长期解法）",
        "3. 若是混合 App：确认是否已从 WEBVIEW 切回 NATIVE_APP 上下文",
        "4. 一次只改一个定位，重跑验证",
    ],
    "崩溃": [
        "1. 抓 logcat/xcrun 日志，定位崩溃栈顶",
        "2. 判断是否 ANR / OOM / 新权限未声明",
        "3. 二分最近一次变更，定位引入点",
    ],
    "超时": [
        "1. 去掉 Thread.sleep，改用显式等待（waitFor）",
        "2. 检查网络/弱网与后端响应",
        "3. 检查异步回调是否未触发",
    ],
    "断言失败": [
        "1. 先查测试数据与环境，而非直接改业务代码",
        "2. 核对预期是否随版本变更",
        "3. 确认非定位/时序导致的假失败",
    ],
    "H5失效": [
        "1. 混合 App 测完 H5 必须切回 NATIVE_APP",
        "2. 确认 WebView 调试开关已开",
    ],
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symptom", required=True, help="失败症状关键词")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    # 模糊匹配
    matched = None
    for k in TREE:
        if k in args.symptom or args.symptom in k:
            matched = k
            break
    if matched is None:
        # 退化为通用三步
        steps = [
            "1. 复现并截图/录屏",
            "2. 抓日志（logcat / 控制台）定位首因",
            "3. 一次只改一个变量，重跑验证",
        ]
        matched = "通用"
    else:
        steps = TREE[matched]

    out = {"symptom": args.symptom, "matched": matched, "steps": steps}
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(f"症状「{args.symptom}」→ 命中诊断路径：{matched}\n")
        for s in steps:
            print(f"  {s}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
