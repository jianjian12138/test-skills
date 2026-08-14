# 执行矩阵输入 Schema（qa-execution）

```json
{
  "change": "订单v2.0",
  "cases": [
    {
      "module": "下单",
      "type": "api|ui|perf|security",
      "name": "创建订单-正常流程",
      "priority": "P0|P1|P2|P3",
      "status": "passed|failed|blocked|notrun",
      "owner": "张三",
      "result": "可选，失败原因/备注"
    }
  ]
}
```

## 状态语义

| status | 含义 |
| --- | --- |
| passed | 通过 |
| failed | 失败（需提缺陷） |
| blocked | 阻塞（依赖未就绪/环境） |
| notrun | 未执行 |

## 路由规则（脚本自动给出建议）

- `api` / `ui` 的 `failed` → `qa-bug-report`（功能缺陷）
- `perf` 的 `failed` → `qa-perf-analysis` 先归因，再决定是否提缺陷
- `security` 的 `failed`（High/Critical）→ `qa-security-report` → 安全缺陷
- `blocked` → 单独列出，跟进依赖
