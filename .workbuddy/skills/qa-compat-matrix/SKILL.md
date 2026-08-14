---

name: qa-compat-matrix
description: |-
  兼容性测试矩阵生成技能：根据 OS × 浏览器 × 设备 × 分辨率 × 网络 维度配置，生成带优先级
  （必测/建议/可选）与「是否需云真机/云浏览器」标注的覆盖矩阵（CSV + Markdown）。覆盖
  BrowserStack/SauceLabs/阿里云真机/腾讯 WeTest 接入与国产浏览器内核注意点。触发词：
  "兼容性矩阵", "compatibility", "浏览器兼容", "设备矩阵", or after qa-test-analysis.
  英文触发词（English triggers）：compatibility matrix, browser compatibility, cross-device.
license: MIT
compatibility: "WorkBuddy / Claude / 通用 Agent（零依赖标准库）"
metadata:
  version: "1.0.0"
  category: traditional
  stage: 06-execution
  tier: 1
---
# qa-compat-matrix — 兼容性测试矩阵

兼容性测试的本质是**在有限资源下最大化覆盖高风险组合**。本技能把维度配置变成一张
**带优先级、带"是否需要云端设备"标注**的矩阵，避免盲目全排列。

> 不是所有组合都要测。先按流量/用户群定"必测"，其余"建议/可选"，移动端优先云真机。

## 维度

- **Web**：OS（Windows/macOS） × 浏览器（Chrome/Safari/Edge/Firefox + 国产内核）
- **移动**：设备（iPhone/各安卓机型） × OS（iOS/Android 版本）
- **其他**：分辨率（桌面/移动视口）、网络（WiFi/4G/弱网）

## 操作流程

### 步骤 1 — 准备维度配置

```json
{
  "web": {"os": ["Windows 11", "macOS 14"], "browsers": ["Chrome", "Safari", "Edge", "微信内置"]},
  "mobile": [
    {"device": "iPhone 14", "os": "iOS 17"},
    {"device": "Redmi Note 12", "os": "Android 13"}
  ],
  "must_pairs": ["Chrome|Windows 11", "Safari|iOS 17"],
  "cloud_browsers": ["微信内置", "UC", "360"],
  "resolutions": ["1920x1080", "375x812"]
}
```

### 步骤 2 — 生成矩阵

```bash
python scripts/gen_matrix.py --config matrix.json --out matrix.md --csv matrix.csv
```

产物：
- `matrix.md`：Web / Mobile 两张表，含优先级与"需云端"列。
- `matrix.csv`：机器可读，便于排期/追踪。

### 步骤 3 — 执行

- 必测组合本地或云真机跑；国产浏览器（微信/UC/360）走云浏览器。
- 云真机/云浏览器接入要点见 `references/matrix-guide.md`。

## 优先级与云端标注规则

- **必测(must)**：命中 `must_pairs` 或主流组合（Chrome+Win / Safari+iOS）。
- **建议(should)**：其余主流浏览器/设备。
- **可选(optional)**：长尾/小众。
- **需云端**：移动设备、国产内核浏览器、`cloud_browsers` 列表中的项。

## 定位金字塔（W5 增强）

移动端 / 跨端定位策略遵循定位金字塔（稳定度降序）：
**L1** accessibility-id（data-testid / data-qa）→ **L2** id/name/语义 css → **L3** 位置型 css（nth-child）→
**L4** 脆弱 css（深层嵌套 / 动态 class）→ **L5** XPath（仅兜底，须注释原因）。
配合 `qa-ui-automation/scripts/locator_health.py` 计算 `healthIndex`（L1=1.0…L5=0.0），
低于 65 触发预警，推动开发补 `data-testid` / `data-qa` 钩子把定位上提到 L1。

## 与上下游衔接

- 输入：用户群/流量数据、`qa-test-analysis` 风险。
- 输出：矩阵 → 执行（`qa-execution` 进度矩阵）/ 探索性（`qa-exploratory`）。
