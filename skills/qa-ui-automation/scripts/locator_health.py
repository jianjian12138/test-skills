#!/usr/bin/env python3
"""qa-ui-automation: 定位器健康度（locator-health，W5 增强）。

移动端 / 跨端定位策略遵循「定位金字塔」，从最稳到最脆：
  L1  accessibility-id（data-testid / getByTestId）——跨端首选，强语义、抗重构
  L2  id / name / 稳定语义 css（role/class）
  L3  位置型 css（nth-child / 复杂组合）
  L4  脆弱 css（深层嵌套 / 动态 class）
  L5  XPath——仅兜底，且须注释原因（最易随 DOM 变动而碎）

healthIndex = Σ(层级权重) / 总数 × 100；权重 L1=1.0 L2=0.8 L3=0.5 L4=0.2 L5=0.0。
  healthIndex < 65 → 预警，推动开发补 data-qa 钩子（把 L5/L4 上提到 L1）。

用法:
    python locator_health.py --inventory locators.json --out health.md
    locators.json: [{"name":"登录按钮","strategy":"accessibility_id","value":"login-btn"},
                    {"name":"价签","strategy":"xpath","value":"//div[3]/span"}]
"""
import argparse
import json
import os
import sys

WEIGHT = {"L1": 1.0, "L2": 0.8, "L3": 0.5, "L4": 0.2, "L5": 0.0}
WARN_THRESHOLD = 65.0
# strategy 关键字 → 层级
_STRATEGY_MAP = {
    "accessibility_id": "L1", "accessibility-id": "L1", "testid": "L1",
    "id": "L2", "name": "L2", "css": "L3", "css_semantic": "L2",
    "css_positional": "L3", "css_fragile": "L4", "xpath": "L5",
}


def classify(strategy, value=""):
    """确定定位器层级：优先用显式 strategy，否则从 value 推断。"""
    if strategy and strategy in _STRATEGY_MAP:
        return _STRATEGY_MAP[strategy]
    v = (value or "").lower()
    if "testid" in v or "accessibility" in v or "data-qa" in v:
        return "L1"
    if v.startswith("//") or v.startswith("(//") or "xpath" in v:
        return "L5"
    if v.startswith("#") or v.startswith("[id=") or v.startswith("id="):
        return "L2"
    if "nth-child" in v or "nth-of-type" in v:
        return "L3"
    # 默认：未声明且无法推断 → 视为脆弱（保守，推动显式声明）
    return "L4"


def compute(inventory):
    """返回 {health_index, counts, warn, weak}。"""
    counts = {f"L{i}": 0 for i in range(1, 6)}
    weak = []  # L4/L5 定位器，推动补 data-qa
    total_w = 0.0
    total = 0
    for item in inventory:
        strat = item.get("strategy", "")
        val = item.get("value", "")
        lvl = classify(strat, val)
        counts[lvl] += 1
        total_w += WEIGHT[lvl]
        total += 1
        if lvl in ("L4", "L5"):
            weak.append({"name": item.get("name", "?"), "level": lvl,
                         "value": val, "reason": item.get("reason", "")})
    health = (total_w / total * 100.0) if total else 100.0
    warn = health < WARN_THRESHOLD
    return {"health_index": round(health, 1), "counts": counts,
            "total": total, "warn": warn, "weak": weak}


def render(result, out_path=None):
    lines = ["# 定位器健康度（locator-health）\n"]
    lines.append(f"- **healthIndex**: {result['health_index']} （阈值 {WARN_THRESHOLD}，低于即预警）")
    lines.append(f"- **层级分布**: " + " / ".join(
        f"{k}={result['counts'][k]}" for k in sorted(result['counts'])))
    if result["warn"]:
        lines.append("\n> ⚠️ **locator-health 预警**：healthIndex < 65，定位器过度依赖脆弱策略"
                     "（L4/L5）。推动开发补 `data-testid` / `data-qa` 钩子，把定位上提到 L1。\n")
        lines.append("| 定位器 | 层级 | 当前值 | 备注 |")
        lines.append("| --- | --- | --- | --- |")
        for w in result["weak"]:
            lines.append(f"| {w['name']} | {w['level']} | {w['value']} | {w['reason'] or '建议补 data-qa'} |")
    else:
        lines.append("\n✅ 定位器健康度达标（L1-L3 占比充足）。")
    md = "\n".join(lines) + "\n"
    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(md)
    return md


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory", required=True, help="定位器清单 JSON（list）")
    ap.add_argument("--out", help="Markdown 输出路径")
    ap.add_argument("--json", action="store_true", help="仅输出 JSON 结果")
    args = ap.parse_args()

    try:
        with open(args.inventory, "r", encoding="utf-8") as f:
            inventory = json.load(f)
    except Exception as e:
        print(f"[ERROR] 读取 {args.inventory} 失败: {e}", file=sys.stderr)
        return 2
    if not isinstance(inventory, list):
        print("[ERROR] inventory 须为 list", file=sys.stderr)
        return 2

    result = compute(inventory)
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        md = render(result, args.out)
        if args.out:
            print(f"[OK] 已生成定位器健康度: {args.out}")
        else:
            print(md)
        if result["warn"]:
            print(f"[WARN] locator-health 预警: healthIndex={result['health_index']} < {WARN_THRESHOLD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
