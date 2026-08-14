---

name: qa-a11y
description: |-
  无障碍(WCAG 2.1)静态检查治理门禁：扫描 HTML 源码/标记（不实际渲染、不调用渲染引擎或 axe-core），按 A 级规则（替代文本、表单标签、语言、标题层级、可访问名称、字幕、交互角色）
  识别违规，存在 A 级问题时产出阻断信号，保障 Web 产品可达性。真实渲染级可访问性校验须接 axe-core/pa11y。触发词：
  "无障碍", "WCAG", "a11y", "可达性", "accessibility", or after qa-ui-automation.
  英文触发词（English triggers）：accessibility, WCAG, a11y.
license: MIT
compatibility: "WorkBuddy / Claude / 通用 Agent（零依赖标准库）"

metadata:
  version: "1.0.0"
  category: traditional
  stage: cross_cutting
  tier: 1
---
# qa-a11y — 无障碍（可达性）检查

无障碍不是「锦上添花」，而是 **法律合规与用户基本权利**。WCAG 2.1 的 A 级要求是底线：

> ⚠️ **治理门禁 · 不执行外部工具**：本技能是**静态规则检查治理门禁**，仅扫描源码/标记识别 WCAG 2.1 A 级违规，**不实际在浏览器渲染、不调用 axe-core 等渲染引擎或外部扫描器**；真实渲染级校验须接 axe-core/pa11y。
- 图片无 `alt` → 屏幕阅读器用户完全不知内容（1.1.1）
- 表单控件无 `label` → 不知要填什么（1.3.1/3.3.2）
- 页面无 `lang` → 读音/翻译错误（3.1.1）
- 标题跳级 → 结构导航断裂（1.3.1）
- 链接/按钮无名称 → 无法识别目的（2.4.4/4.1.2）
- 视频无字幕 → 听障用户无法获取（1.2.2）

> 本技能做**静态可检查项**的自动门禁；需要运行态或设计稿颜色的项（如对比度、键盘可达性）属边界，明确标注。

## 输入约定

`--in` 指向单个 HTML 文件或目录（递归扫描 `*.html`）。

```html
<!-- 示例：被检查对象 -->
<html><body>
  <h1>标题</h1>
  <img src="logo.png">            <!-- ❌ 缺 alt -->
  <input type="text">             <!-- ❌ 缺 label -->
</body></html>
```

## 操作流程

```bash
python scripts/a11y_check.py --in page.html --out a11y_report.md --signals-dir signals [--fail-on]
```

- 逐文件扫描下方 7 类 A 级规则，汇总违规。
- 存在 `critical`/`high`（A 级底线）违规 → 产出 `a11y_violation` **阻断信号**。
- 分数 = 1 − (A 级违规数 / 被检查元素数)，用于趋势观察（非门禁唯一依据）。
- `--fail-on` 时同时 `sys.exit(1)`。

## 规则清单（A 级，自动可检查）

| 规则 | 级别 | 说明（对应 WCAG） |
| --- | --- | --- |
| A-IMG-ALT | critical | 图片缺 `alt`（1.1.1） |
| A-INPUT-LABEL | critical | 表单控件缺 `label`/`aria-label`（1.3.1/3.3.2） |
| A-HTML-LANG | high | `<html>` 缺 `lang`（3.1.1） |
| A-HEADING-ORDER | high | 标题层级跳级（1.3.1） |
| A-NAME | high | 链接/按钮无可访问名称（2.4.4/4.1.2） |
| A-VIDEO-CAPTION | medium | 视频缺字幕轨（1.2.2） |
| A-ROLE | medium | 可交互 div/span 缺 `role`（4.1.2） |

## 与上下游衔接

- 输入：UI 组件/页面产物（由 `qa-ui-automation` 渲染或开发直接产出）。
- 输出：无障碍报告 + 信号 → 接入 `qa-release-check` 门禁，作为 UI 质量横切门。

## 能力边界（诚实标注）

- 不计算**颜色对比度**（需设计稿颜色值，建议接 axe / pa11y 或人工评审）。
- 不验证**键盘可达性**（需运行态，建议接 axe-core 或手动）。
- 仅做**静态可检查**项；A 级以上（AA/AAA）与动态项由专业工具补全。

## 参考资料

- 检查项、阈值、CLI 用法与常见坑：见 [`references/guide.md`](references/guide.md)。
