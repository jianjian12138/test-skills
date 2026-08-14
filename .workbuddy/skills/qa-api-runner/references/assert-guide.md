# 接口断言类型指南（qa-api-runner）

`engine.check_assert(actual, op, expect)` 支持以下断言操作符：

| 操作符 | 含义 | 示例（断言定义） |
| --- | --- | --- |
| `eq` / `ne` | 等于 / 不等于 | `{"eq": ["$.code", 0]}` |
| `gt` / `lt` / `ge` / `le` | 数值比较 | `{"gt": ["$.data.id", 0]}` |
| `contains` | 包含 | `{"contains": ["$.msg", "success"]}` |
| `in` | 属于集合 | `{"in": ["$.status", ["PAID","DONE"]]}` |
| `exists` | 字段存在 | `{"exists": ["$.data.token"]}` |
| `regex` | 正则匹配 | `{"regex": ["$.data.orderNo", "^NO\\d{10}$"]}` |
| `len` / `len_eq` | 长度等于 | `{"len": ["$.data.list", 10]}` |
| `len_gt` / `len_lt` / `len_ge` / `len_le` | 长度比较 | `{"len_gt": ["$.data.list", 0]}` |
| `schema` | 轻量结构校验 | `{"schema": ["$.data", {"required":["id"],"properties":{"id":{"type":"integer"}}}]}` |

## 用法注意
- 取响应字段用 JSONPath：`$.a.b[0].c`。
- 字符串里的 `${var}` 会被上下文替换（串联场景）。
- DB 断言走 `db_assert`，在接口返回之外再做落库校验。

## 推荐组合
- 状态码 + 业务码 + 关键字段 + DB 落库，四重校验才稳。
- 列表类接口叠加 `len_gt: 0` 防空。
- 订单号 / 手机号用 `regex` 锁格式。
