# 选择器优先级规范（selector-rules）

## 优先级（从高到低）
```
getByRole  >  getByText  >  getByLabel  >  getByPlaceholder  >  CSS selector
```

## 规则
1. **语义化优先**：能用 role / text / label 定位就用，最抗重构。
2. **CSS 仅兜底**：仅当自定义组件无语义化属性（如自绘 div grid）时使用 class 定位。
3. **禁止索引定位**：不允许 `.first()` `.nth(i)` `.last()` 依赖顺序——DOM 顺序一变就崩。
4. **data-testid 最优解**：让前端在交互元素统一加 `data-testid`（见 `qa-ui-testid`），
   与样式/结构解耦，无论前端怎么重构，只要标识不变脚本就无需改。

## 命名约定（data-testid）
- 格式：`<页面>-<组件>-<用途>`，如 `login-btn-submit`、`order-list-row`。
- 全局唯一；重复由 `qa-ui-testid` 扫描保证。
- 存量老项目可用 `qa-ui-testid` 批量补，新项目规范落地后人工维护即可。

## 反模式
- ❌ `div:nth-child(3) > span.btn` —— 顺序/结构耦合，极易失效。
- ❌ 靠文本片段定位又没限定作用域，导致重名元素误命中。
- ❌ 把选择器直接写进用例层，导致重构时散落修改。
