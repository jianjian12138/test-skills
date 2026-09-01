# 无障碍（可达性）检查指南 — qa-a11y

## 1. 检查范围（WCAG 2.1 A 级静态项）
- 图片/图标缺 `alt`（规则 1.1.1）
- 表单控件缺 `<label for>` 关联（1.3.1 / 3.3.2）
- 页面/区块缺 `lang`（3.1.1）
- 标题跳级（h1→h3）（1.3.1）
- 链接/按钮无可访问名称（2.4.4 / 4.1.2）
- 视频缺字幕（1.2.2）
- 重复的 `id`（破坏可访问名称解析）
- `<iframe>` 缺 `title`、`table` 缺 `th`、非负 `tabindex`

> 自动跳过：隐藏元素（`display:none`/`hidden`）、`type=submit|button`、纯图片按钮（已有 `aria-label` 时）、纯装饰图。

## 2. 阻断规则
- `BLOCKING_SEVERITIES = {critical, high}`，命中即写 `signals/qa-a11y.json` 的 `a11y_violation`，`blocking=true`。
- 仅 medium/low（如装饰性建议）不阻断。

## 3. CLI 约定
```bash
python qa-a11y/scripts/a11y_check.py --in web/ --signals-dir signals
# 可选：--fail-on 命中阻断项时 sys.exit(1)
```
- `--in` 接受单个 `.html` 或目录（递归 `*.html`）。
- 信号写入 `--signals-dir/qa-a11y.json`，交由 `qa-release-check` 聚合门禁。

## 4. 常见坑（诚实边界）
- **不检运行态项**：颜色对比度、键盘可达性、屏幕阅读器实测 → 超出静态范围，需人工/专项工具。
- 单页应用路由切换后动态注入的 DOM 需在渲染后落盘 HTML 再扫。
- `aria-hidden` 与 `focusable` 冲突（如 `aria-hidden=true` 内仍有可聚焦元素）本技能不判定，需人工核查。
