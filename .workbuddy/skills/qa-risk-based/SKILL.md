---

name: qa-risk-based
description: |-
  基于风险的测试（RBT）量化技能：按 Risk = Impact × Probability 对需求/模块/变更点打分定级，
  输出风险登记册并反推测试密度（用例数量、回归范围、兼容性优先级）。触发词：
  "基于风险的测试", "风险量化", "测试优先级", "RBT", or after qa-test-analysis.
  英文触发词（English triggers）：risk-based testing, RBT, risk register.
license: MIT
compatibility: "WorkBuddy / Claude / 通用 Agent（零依赖标准库）"

metadata:
  version: "1.0.0"
  category: traditional
  stage: cross_cutting
  tier: 1
---
# qa-risk-based — 基于风险的测试（RBT）

测试资源永远有限。**RBT 用「影响 × 概率」把有限用例集中到最可能出事、出了事最贵的地方**，
而不是平均用力。

> 不是「每个功能都测一样多」，而是「风险高的多测、风险低的少测（冒烟即可）」。

## 操作流程

### 步骤 1 — 列出风险项

```json
# risks.json
[
  {"id":"R1","area":"支付","impact":5,"probability":4,"note":"金额计算错误直接资损"},
  {"id":"R2","area":"头像上传","impact":2,"probability":3,"note":"体验问题"}
]
```

impact / probability 均取 1~5。

### 步骤 2 — 量化并反推测试密度

```bash
python scripts/risk_register.py --risks risks.json --out risk_register.md --csv risk_register.csv
```

输出：
- 每项 `risk_score = impact × probability`（1~25）
- 定级：≥20 Critical / 12~19 High / 6~11 Medium / <6 Low
- 测试密度建议：Critical → 穷尽+回归+兼容全测；High → 重点+回归；Medium → 正常；Low → 冒烟

### 步骤 3 — 衔接

- 风险登记册 → 喂给 `qa-test-case-gen` 决定用例密度、`qa-compat-matrix` 决定兼容优先级、
  `qa-release-check` 作为上线风险依据。

## 八大测试维度交叉矩阵（W7 增强）

用例设计应自觉覆盖 8 个维度，避免只在「交互」维度堆用例：

| 维度 | 关注点 | 典型漏测 |
|---|---|---|
| 交互 | UI/UX 正常流程 | 异常态、空态 |
| 服务端 | 接口/逻辑/数据 | 幂等、并发 |
| 安全合规 | 越权/注入/合规 | 横向越权、敏感信息 |
| **资损** | 金额/账务/对账 | 见下方 L1–L4 |
| 性能 | 响应/吞吐/资源 | 慢查询、内存 |
| 国际化 | 多语言/时区/币种 | 时区、RTL |
| 兼容 | 端/版本/浏览器 | 旧版本、移动端 |
| 埋点 | 数据上报/可观测 | 漏报、错报 |

完整交叉模板（维度 × 用例 自检表）见 `references/dimension-matrix.md`。
建议在 `testpoints.md` 每个测试点标注其覆盖的维度组合，避免维度盲区。

### 资损风险分析（代码血缘 L1–L4）
对资损相关需求，按代码血缘定位影响面，定级测试密度：
- **L1 核心账务**：直接改金额/余额/对账（支付、清结算）→ 穷尽 + 回归 + 资金对账。
- **L2 交易链路**：下单/退款/优惠券等强关联账务的流程 → 重点 + 回归。
- **L3 边缘业务**：积分/权益等弱关联 → 正常覆盖。
- **L4 非资金**：纯展示/配置 → 冒烟即可。
资损维度与 `impact`（影响）联动：L1 自动把 impact 拉到 5，L4 不因此抬高分数。

## 参考
- 详见 `references/guide.md`：ISTQB RBT 范式、打分锚定表、与探索性/兼容的联动。
