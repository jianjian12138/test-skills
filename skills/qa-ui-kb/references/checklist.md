# UI 自动化知识库检查清单与常见坑（qa-ui-kb）

## 1. 元素描述层
- [ ] 每个关键元素有稳定描述（角色 / 名称 / 文本 / 标签）
- [ ] 动态元素有稳定定位特征（data-testid 优先）
- [ ] 列表 / 表格元素标注行定位策略

## 2. 操作模式层
- [ ] 常见操作（点击 / 输入 / 选择 / 上传 / 滚动）有标准模式
- [ ] 异步操作标注等待点（loading / toast / 路由）

## 3. 选择器规则层
- [ ] 优先级：getByRole > getByText > getByLabel > getByPlaceholder > CSS
- [ ] 避免易碎选择器（绝对 XPath / 含随机 class）

## 4. 组件库适配
- [ ] antd / Element Plus 组件映射稳定定位
- [ ] Shadow DOM：需穿透（pierce / ::part）
- [ ] iframe：需切换 frame 上下文

## 5. 常见坑
- flaky 测试：根因多为等待策略不当 / 动画 / 竞态。
- 过度依赖文本 → 文案一改就碎，优先 testid + role。
- 忽略 Shadow DOM / iframe → 元素找不到。
