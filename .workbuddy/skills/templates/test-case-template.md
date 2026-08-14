# 测试用例模板（统一格式，纳入版本管理）

| 字段 | 说明 |
|---|---|
| ID | C-xxx（与需求 req_id 关联，便于追溯） |
| 模块 | 所属功能/服务 |
| 标题 | 一句话描述场景 |
| 类型 | positive / boundary / negative / pairwise / exploratory |
| 步骤 | 操作序列 |
| 预期 | 可判定结果（避免 "Success"/"正常" 等模糊词） |
| 优先级 | P0/P1/P2（由 qa-risk-based 风险分反推） |
| req_id | 关联需求（喂 qa-req-spec 追溯矩阵回写） |

> 用例必须与需求关联（req_id），否则追溯矩阵无法回写，发布门禁无法确认「需求测没测」。
