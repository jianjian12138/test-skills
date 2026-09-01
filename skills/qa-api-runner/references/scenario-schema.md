# 场景用例 JSON Schema（scenario-schema）

`qa-api-runner` 的执行输入。支持单接口与多接口串联（参数传递 + 失败即断），
可选 MySQL 数据库断言实现「接口 + 数据」双校验。

```json
{
  "base_url": "https://api.example.com",
  "env": { "token": "" },
  "global_headers": { "Content-Type": "application/json" },
  "cases": [
    {
      "id": "C01",
      "name": "用户登录",
      "request": {
        "method": "POST",
        "path": "/api/v1/login",
        "json": {"username": "test", "password": "123456"}
      },
      "extract": { "token": "$.data.token" },
      "assert": [
        {"eq": ["$.code", 0]},
        {"contains": ["$.msg", "success"]}
      ]
    },
    {
      "id": "C02",
      "name": "获取当前用户（串联上一步 token）",
      "depends": "C01",
      "request": {
        "method": "GET",
        "path": "/api/v1/user/me",
        "headers": { "Authorization": "Bearer ${token}" }
      },
      "assert": [ {"eq": ["$.code", 0]} ],
      "db_assert": [
        {"eq": ["SELECT status FROM user WHERE username='test'", 1]}
      ]
    }
  ]
}
```

## 字段说明
- `base_url`：接口基地址；也可由 .env 的 `BASE_URL` 覆盖。
- `env`：初始上下文变量。
- `global_headers`：全局请求头（如 Content-Type）。
- `cases[].extract`：从响应 JSON 抽取变量（极简 JSONPath `$.a.b[0]`），供后续 `${var}` 引用。
- `cases[].assert`：响应断言，支持 `eq/ne/contains/in/gt/lt/ge/le/exists`。
  形如 `{ "eq": ["$.code", 0] }`，第一项可为 `${var}` 或字面量。
- `cases[].db_assert`：数据库断言，`{ "eq": ["<SQL>", 期望值] }`，需开启 DB 配置。
- `depends`：声明串联关系（执行按列表顺序，天然保证前后依赖）。

## 变量替换
请求中任意字符串里的 `${token}` 会被上下文值替换；支持 path / headers / json / params / data。
