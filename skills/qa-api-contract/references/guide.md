# 接口契约对比指南 — qa-api-contract

## 1. 目的
在接口新旧版本之间做**破坏性变更（BREAKING）**检测，防止「悄无声息地改坏调用方」。

## 2. 阻断规则
- 存在破坏性变更 → 写 `signals/qa-api-contract.json` 的 `breaking_change`，`severity=critical`、`blocking=true`。
- 非破坏性变更（新增可选字段、新增端点、字段顺序调整）**不阻断**，仅进入报告。

## 3. CLI 约定
```bash
python qa-api-contract/scripts/contract_diff.py \
  --old 05-api/old.json --new 05-api/new.json \
  --out signals/qa-api-contract.json --fail-on
# 也可：--signals-dir signals 统一落盘；--rules 打印规则清单后退出
```

## 4. 破坏性变更判定（典型）
- 删除/重命名字段、改字段类型（string↔number）、改必填→可选反向、删除端点、改 HTTP 语义（GET 变 DELETE）。
- 路径参数/查询参数含义变更、错误码语义变更。

## 5. 常见坑
- **仅对比 openapi/swagger 结构**，不验证运行时行为；字段名同但含义变（语义 breaking）需人工评审。
- 同一字段同时出现在 `request` 与 `response` 时，两者 breaking 判定独立。
- 使用 `--rules` 先核对本工具识别的 breaking 规则集合，避免误判。
