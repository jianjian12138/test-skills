# UI 自动化检查清单与常见坑（qa-ui-automation）

## 1. Page Object 分层
- [ ] pages.py：页面元素 + 操作封装
- [ ] test_*.py：用例只调用页面方法，不出现裸选择器
- [ ] 复用：公共组件抽 base page

## 2. 等待策略（降 flaky 关键）
- [ ] 优先显式等待（元素可见 / 可点击 / 文本出现）
- [ ] 禁用硬 sleep；动画结束再断言
- [ ] 网络等待：接口返回 / loading 消失

## 3. 特殊场景
- Shadow DOM：pierce 选择器穿透
- iframe：frame 上下文切换
- 文件上传：setInputFiles
- 多窗口 / 弹窗：上下文管理

## 4. 常见坑
- 选择器裸写在用例里 → 维护地狱。
- 用 sleep 等异步 → 偶发失败。
- 不处理 iframe / Shadow DOM → 找不到元素。
- 一条用例多断言无清理 → 相互影响。
