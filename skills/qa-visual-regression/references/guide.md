# 视觉回归指南 — qa-visual-regression

## 1. 目的
对比页面 DOM/CSS 快照的基线（baseline）与当前（current），识别结构性/布局级回归，零外部依赖（纯标准库）。

## 2. 阻断规则
- 规则：`VR-MISSING`（基线有、当前无）、`VR-ADDED`（当前新增）、`VR-PROP`（属性差异）。
- `high` 级回归数 `> --threshold` → 写 `signals/qa-visual-regression.json` 的 `visual_regression`，`blocking=true`。
- 默认 `--threshold 0`：即只要出现 1 个 high 级布局回归即阻断。

## 3. CLI 约定
```bash
python qa-visual-regression/scripts/visual_diff.py \
  --baseline snap/baseline.json --current snap/current.json \
  --signals-dir signals --fail-on
```
- `--threshold N`：允许容忍的 high 回归数（默认 0，严格）。

## 4. 差异分级
- `high`：影响布局/可见结构的元素增删或关键属性变更（如尺寸、定位、display）。
- 非 high（如仅文本微调）记 medium/low，默认不直接阻断。

## 5. 常见坑
- 快照基于渲染后 DOM；动态内容（时间/随机 id/轮播）需先冻结或忽略，否则必误报 high。
- 阈值 0 在频繁 UI 迭代期可能过严，可按发布节奏放宽 `--threshold`，但需评审记录。
