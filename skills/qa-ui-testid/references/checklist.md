# testid 注入检查清单与常见坑（qa-ui-testid）

## 1. 命名规则
- 语义化：`module-action-target`，如 `order-submit-btn`
- 不绑定样式/序号（避免 `btn-1`、`submit-2`）
- 全局唯一，避免重复导致定位歧义

## 2. 注入范围
- [ ] 交互元素（按钮 / 链接 / 输入 / 选择）
- [ ] 动态列表项（带稳定后缀或上下文）
- [ ] 关键展示（结果区 / 错误提示）

## 3. 框架覆盖
- React：`data-testid={...}`
- Vue：`data-testid="..."`（模板属性）
- 原生 HTML：直接属性

## 4. 常见坑
- 只加可见元素漏动态元素 → 关键路径仍 flaky。
- 用索引命名 → 列表增删即错位。
- 重复 testid → 定位到多个，断言失真。
- 扫描工具默认 dry-run，需 `--write` 才改源码（见 scan_testid.py）。
