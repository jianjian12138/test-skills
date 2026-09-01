# 页面描述 JSON Schema（po-schema）

`page_object_gen.py` 的输入。建议由 AI 基于 `qa-ui-kb` 知识库或元素清单整理。

```json
{
  "base_url": "https://app.example.com",
  "pages": [
    {
      "name": "LoginPage",
      "route": "/login",
      "elements": [
        {"name": "username", "type": "input", "testid": "login-username"},
        {"name": "password", "type": "input", "testid": "login-password"},
        {"name": "submit",   "type": "button", "testid": "login-submit"}
      ]
    }
  ]
}
```

## 字段
- `pages[].name`：PO 类名（PascalCase）。
- `pages[].route`：页面路由（PO.goto 使用）。
- `pages[].elements[].name`：元素变量名 → 生成 `fill_<name>` / `click_<name>` 方法。
- `pages[].elements[].type`：`input`/`textarea` → fill；`select` → select_option；`button`/`a`/其他 → click。
- `pages[].elements[].testid`：`data-testid` 值，由 `qa-ui-testid` 保证唯一。

## 编写纪律
- 每个元素必须有可靠 testid（先跑 `qa-ui-testid`）。
- 元素粒度到「可操作单元」，不要把一个表单拆成十个字段又混用。
- 业务流（多页面串联）写在用例层，不写进 PO。
