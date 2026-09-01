# 数据规格 Schema（data-spec）

`gen_data.py` 的输入。描述字段与生成策略。

```json
{
  "rows": 3,
  "seed": 7,
  "fields": [
    {"name": "age", "type": "int", "min": 0, "max": 120},
    {"name": "nickname", "type": "string", "min_len": 1, "max_len": 20},
    {"name": "phone", "type": "phone"},
    {"name": "email", "type": "email"},
    {"name": "status", "type": "enum", "values": ["active", "disabled"]}
  ],
  "pii_mask": ["nickname", "phone", "email"]
}
```

## 字段类型
- `int`：产出边界集合 `min/max/min-1/max+1/0`。
- `string`：产出 `空/最小长/最大长/超长`。
- `phone`：生成合法格式手机号（1xx + 11 位）。
- `email`：生成 `xxx@example.com`。
- `enum`：从 `values` 随机取。

## 控制项
- `rows`：随机类字段生成条数（边界类字段按自身候选数，取最大行数对齐）。
- `seed`：随机种子，固定后可复现，利于回归。
- `pii_mask`：需脱敏字段名列表；脱敏规则为「首尾各留 1 字符，中间 `*」。

## 编写纪律
- 边界字段（int/string）优先保证覆盖，随机字段用于铺量。
- 凡涉及真实个人信息（姓名/手机/邮箱/身份证）务必放入 `pii_mask`。
- 业务唯一性约束（如用户名不可重复）由调用方保证，脚本不做跨行去重。
