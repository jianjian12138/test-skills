#!/usr/bin/env python3
"""移动端测试清单先行：从屏幕/流程/风险描述生成 app-test-manifest.json 骨架。

Usage:
    python scripts/scaffold_manifest.py --input spec.json --out app-test-manifest.json [--md manifest.md]

spec.json:
{
  "app": "订单 App",
  "platforms": ["Android","iOS"],
  "screens": [{"name":"登录页","key":"login"}, {"name":"订单列表","key":"order_list"}],
  "flows": [{"name":"登录下单","steps":["login","order_list","pay"]}],
  "risks": [{"area":"支付","desc":"金额计算"}]
}

清单先行（灵魂步骤）：所有 case 的事实来源就是这份 manifest，绝不可跳过。
"""
import argparse
import json
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--md", help="同时输出 Markdown 清单")
    args = ap.parse_args()

    with open(args.input, "r", encoding="utf-8-sig") as f:
        spec = json.load(f)

    manifest = {
        "app": spec.get("app", ""),
        "platforms": spec.get("platforms", []),
        "screens": spec.get("screens", []),
        "flows": spec.get("flows", []),
        "risks": spec.get("risks", []),
        "generated_cases": [],  # 由后续步骤回填
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"[OK] 已生成测试清单: {args.out}")
    print(f"     屏幕 {len(manifest['screens'])} 个 / 流程 {len(manifest['flows'])} 条 / 风险 {len(manifest['risks'])} 项")

    if args.md:
        lines = [f"# 移动端测试清单：{manifest['app']}\n",
                 f"平台：{', '.join(manifest['platforms'])}\n",
                 "## 屏幕\n"]
        for s in manifest["screens"]:
            lines.append(f"- {s.get('name')} (`{s.get('key')}`)")
        lines.append("\n## 流程\n")
        for fl in manifest["flows"]:
            lines.append(f"- {fl.get('name')}: {' → '.join(fl.get('steps', []))}")
        lines.append("\n## 风险\n")
        for r in manifest["risks"]:
            lines.append(f"- [{r.get('area')}] {r.get('desc')}")
        with open(args.md, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print(f"[OK] 已生成 Markdown: {args.md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
