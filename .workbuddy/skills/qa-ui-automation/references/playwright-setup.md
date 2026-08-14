# Playwright 执行环境（playwright-setup）

## 1. 安装
```bash
pip install playwright
playwright install        # 下载 Chromium（一次性）
playwright install-deps   # Linux 可能需要系统依赖
```

## 2. 智能等待
Playwright 默认自动等待元素可操作，无需硬编码 sleep。仅在以下情况显式等待：
- 异步数据加载：`page.wait_for_response(lambda r: ...)`
- 元素出现：`page.get_by_test_id("x").wait_for()`
- 网络空闲：`page.wait_for_load_state("networkidle")`

## 3. 登录态复用
UI 自动化最耗时的往往是登录。建议：
- 用 API 登录拿 token，注入 `localStorage`/`cookie` 后跳转业务页；
- 或用 `browser_context.storage_state()` 保存登录态，后续加载复用。

## 4. 失败排查
- 失败时自动截图 + 页面 HTML（`page.screenshot()` / `page.content()`）。
- 配合 Allure：`allure.attach` 截图，定位更快。

## 5. Allure 报告
```bash
pip install pytest allure-pytest
pytest ui_tests --alluredir=allure-results
allure serve allure-results
```
报告中可看：用例时长、步骤、失败截图、追溯链接。

## 6. 与选择器规范配合
生成的 PO 统一用 `get_by_test_id`（对应 `data-testid`），契合 `qa-ui-kb` 的
selector-rules：语义优先、禁用索引定位，最大化抗重构能力。
