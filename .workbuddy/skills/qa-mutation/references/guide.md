# 变异测试指南 — qa-mutation

## 1. 目的
用变异分数衡量测试用例集「抓住 bug 的能力」：分数低说明很多变异体没被杀掉，测试存在盲区。

## 2. 阻断规则
- `score = killed / (total - equivalent)`（等价变异体不计入分母）
- `score < --threshold` → 写 `signals/qa-mutation.json` 的 `mutation_score_low`，`blocking=true`。
- 默认阈值 `--threshold 0.8`（80%）。

## 3. CLI 约定
```bash
python qa-mutation/scripts/mutation_score.py \
  --mutants mutation/mutants.json --signals-dir signals --fail-on
```

## 4. 输入格式（`--mutants`）
```json
{"total": 100, "killed": 82, "equivalent": 4}
```
- `equivalent` = 被人工/工具判定为等价的变异体（不应被杀死，剔除分母）。

## 5. 常见坑
- 阈值 0.8 是通用起点，安全/支付等高危模块应提高到 0.9+。
- 等价变异体若误判为 non-equivalent 会虚低分数；反之会虚高，需核对 `equivalent` 标注。
- 本技能只算分，不生成/执行变异体（由外部变异工具产出 `--mutants`）。
