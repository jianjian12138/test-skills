# 单元测试 / TDD 健康指南 — qa-unit-tdd

## 1. 目的
用一组规则给单元测试健康度打分，拦下「测试本身不可信 / 结构失衡」的情况，支撑 TDD 落地。

## 2. 规则与阻断
| 规则 | 含义 | severity | blocking |
|---|---|---|---|
| UT-FAIL | 存在失败用例 | critical | ✅ |
| UT-PYRAMID | 测试金字塔失衡（E2E 占比过高） | high | ✅ |
| UT-COVERAGE | 覆盖率低于阈值 | high | ✅ |
| UT-TCR | 测试代码比（TCR）异常 | medium | ❌ |

- `BLOCKING = {critical, high}`：UT-FAIL / UT-PYRAMID / UT-COVERAGE 命中即 `blocking=true`。

## 3. CLI 约定
```bash
python qa-unit-tdd/scripts/unit_health.py --metrics metrics.json --signals-dir signals --fail-on
```
- `--metrics` 为测试执行产出的指标 JSON（覆盖率、各层用例数、失败数等）。

## 4. 输入指标示例
```json
{"coverage":0.78,"failed":0,"e2e":120,"integration":200,"unit":600,"tcr":1.2}
```

## 5. 常见坑
- 覆盖率只看行覆盖会漏分支/路径，建议配合变异测试（qa-mutation）交叉验证。
- 金字塔失衡是趋势信号，单次波动不必阻断，结合阈值区间判定。
