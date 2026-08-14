---

name: qa-visual-regression
description: |-
  视觉回归治理门禁：对比已落盘的基线快照与当前快照（DOM 结构 + 关键视觉属性，**不截图、不调浏览器**），识别布局/结构/样式回归，
  存在布局级回归时产出阻断信号，守住「改一处崩一片」的 UI 底线。真实像素级对比须接 Percy/Chromatic。触发词：
  "视觉回归", "visual regression", "UI 回归", "快照对比", "界面走样", or after qa-ui-automation.
  英文触发词（English triggers）：visual regression, snapshot, UI diff.
license: MIT
compatibility: "WorkBuddy / Claude / 通用 Agent（零依赖标准库）"

metadata:
  version: "1.0.0"
  category: traditional
  stage: cross_cutting
  tier: 1
---
# qa-visual-regression — 视觉回归（快照 diff）

功能迭代最怕「**改 A 处、B 处莫名走样**」。视觉回归就是把「当前长相」和「已知正确的基线」对比，

> ⚠️ **治理门禁 · 不执行外部工具**：本技能仅对比已落盘快照做结构/布局断言，**不截图、不调浏览器、不接入 Percy/Chromatic 等外部像素 diff 服务**；真实像素级 diff 须接专业工具。
任何结构性/布局级偏移都拦下来。

> 像素级「长得像不像」是主观且容易误报的，本技能聚焦**可断言的客观差异**（结构、布局属性、关键样式），
> 把噪声交给专业工具（见能力边界）。

## 输入约定

`--baseline` 与 `--current` 各指向一份快照 JSON，描述页面元素及其关键属性：

```json
{
  "url": "https://app/home",
  "elements": [
    {"id": "header", "props": {"display": "flex", "width": "100%", "color": "#222", "text": "首页"}},
    {"id": "logo",   "props": {"width": "120px", "height": "40px"}},
    {"id": "footer", "props": {"display": "block", "text": "© 2026"}}
  ]
}
```

## 操作流程

```bash
python scripts/visual_diff.py --baseline base.json --current cur.json \
       --out visual_report.md --signals-dir signals [--threshold 0] [--fail-on]
```

差异分级：

| 规则 | 级别 | 说明 |
| --- | --- | --- |
| VR-MISSING | high | 基线元素在回归版本中缺失（结构破坏） |
| VR-ADDED | high | 回归版本新增元素（可能挤压布局） |
| VR-PROP（布局类） | high | `display/width/height/position/flex/...` 等布局属性变化 |
| VR-PROP（文本/样式类） | medium | `text/color/font/border/...` 变化 |

- 高危(high)回归数 > `--threshold`（默认 0，即零容忍）→ 产出 `visual_regression` **阻断信号**。
- 趋势分 = 1 − (回归项 / 被检查元素数)。
- `--fail-on` 时同时 `sys.exit(1)`。

## 与上下游衔接

- 输入：UI 自动化/渲染产物派生的快照（由 `qa-ui-automation` 或截图工具生成）。
- 输出：视觉回归报告 + 信号 → 接入 `qa-release-check` 门禁，作为 UI 质量横切门。

## 能力边界（诚实标注）

- **不做像素级比对**（需图像库/截图 + pixelmatch/Playwright，超出零依赖范围）。
- 快照需由上游产出；建议 CI 中接入 Playwright screenshot 生成 `elements` 快照后再交由本技能判定。
- 文本类变化判为 medium（非布局阻断），避免文案微调误伤发布。

## 参考资料

- 检查项、阈值、CLI 用法与常见坑：见 [`references/guide.md`](references/guide.md)。
