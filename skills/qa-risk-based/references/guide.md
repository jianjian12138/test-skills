# 基于风险的测试指南 — qa-risk-based

## 1. 目的
测试资源永远有限。RBT 用 **Risk = Impact × Probability**（均 1~5）把有限用例集中到「最可能出事、出了事最贵」的地方，而不是平均用力。

## 2. 信号说明（信息性，不阻断）
- 存在 high/critical 风险项 → 写 `signals/qa-risk-based.json` 的 `high_risk_present`，`severity=high`、`blocking=False`。
- 本技能**不直接阻断发布**，而是驱动「测试密度」：风险高 → 多测（深用例+回归+兼容），风险低 → 冒烟即可。

## 3. CLI 约定
```bash
python qa-risk-based/scripts/risk_rank.py --risks risks.json --signals-dir signals
```
- 或作为 `qa-test-analysis` 之后的人工/自动定级步骤。

## 4. 风险登记册示例
```json
[{"id":"R1","area":"支付","impact":5,"probability":4,"note":"金额错误直接资损"},
 {"id":"R2","area":"头像上传","impact":2,"probability":3,"note":"体验问题"}]
```
- `Risk = 5×4 = 20`（高）需重点；`2×3=6`（低）冒烟即可。

## 5. 常见坑
- impact/probability 拍脑袋：建议用历史故障数据校准概率、用资损/合规等级校准 impact。
- 风险随时间变化（新模块概率高、老模块概率低），每次大变更重评。
