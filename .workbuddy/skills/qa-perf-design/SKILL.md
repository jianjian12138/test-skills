---

name: qa-perf-design
description: |-
  当测试工程师需要把需求、NFR 或容量目标翻译成可执行的性能测试方案时使用：设计
  负载 load / 压力 stress / 疲劳 endurance(soak) / 尖峰 spike 四类场景，明确并发数、
  目标 TPS、爬坡 ramp-up、思考时间 think-time 与 SLA 阈值。触发词："性能测试方案"、
  "压测设计"、"性能场景"、"容量评估"、"并发多少"，或在 qa-req-spec / qa-test-analysis
  之后使用。
  英文触发词（English triggers）：performance test design, load testing, stress testing.
license: MIT
compatibility: "WorkBuddy / Claude / 通用 Agent（零依赖标准库）"

metadata:
  version: "1.0.0"
  category: traditional
  stage: 06-execution
  tier: 1
---
# qa-perf-design — 性能测试场景设计

把「需求 / NFR / 容量目标」翻译成一份可执行的性能测试方案：
**负载（load）/ 压力（stress）/ 疲劳（endurance/soak）/  spike（尖峰）** 四类场景，
明确并发数、目标 TPS、爬坡（ramp-up）、思考时间（think-time）、SLA 阈值。

> 性能测试不是「把并发开到最大」。先定目标，再定场景，最后才有脚本与结果判定。

## 何时使用

- 需求或 NFR 里出现「响应时间」「并发」「吞吐」「峰值」「稳定性」等字眼。
- 用户说「性能测试方案」「压测设计」「容量评估」「这个接口扛得住多少」。
- 上线前容量规划、大促保障、接口性能基线建立。

## 四类场景模型

| 场景类型 | 目的 | 关键参数 | 判定重点 |
| --- | --- | --- | --- |
| 负载 Load | 验证日常/峰值容量下达标 | 目标并发 + 目标 TPS | 是否达到 SLA |
| 压力 Stress | 找拐点 / 极限 | 逐步加压至失败 | 拐点位置、失败模式 |
| 疲劳 Endurance | 找内存泄漏 / 退化 | 中高负载长时间 | 资源是否持续增长 |
| 尖峰 Spike | 突发流量韧性 | 瞬间 0→峰值→回落 | 能否快速恢复 |

## 操作流程

### 步骤 1 — 提取性能目标

从需求 / NFR 中抽取：
- **业务量**：日活、峰值 QPS、核心交易笔数。
- **SLA**：P95 响应时间、错误率上限、TPS 下限。
- **约束**：数据量、缓存策略、依赖方限流。

### 步骤 2 — 设计场景矩阵

按 `references/scenario-template.md` 填写场景矩阵。每个场景明确：
`name / type / users / spawn_rate / duration / think_time / target_tps / sla`。

### 步骤 3 — 生成方案文档

用脚本把场景 JSON 渲染成可读方案（含 SLA 判定口径）：

```bash
python scripts/gen_perf_plan.py --scenarios scenarios.json --out plan.md
```

### 步骤 4 — 衔接下游

- 方案交给 `qa-perf-locust` **或** `qa-perf-jmeter` 生成脚本（两者共用本技能的
  场景 JSON schema，可互换；Locust 偏代码化/CI，JMeter 偏无代码/分布式）。
- 结果交给 `qa-perf-analysis`（Locust）**或** `qa-perf-jmeter` 的 analyze 脚本
  （JMeter）做吞吐 / 延迟 / 瓶颈判定，口径一致便于横向比较。
- SLA 是否达标进入 `qa-report` / 上线评审。

## 估算速算（给一个起点）

```
目标并发 ≈ 峰值QPS × 平均响应时间(秒)
例：峰值 1000 QPS，P95=0.5s → 约 500 并发即打满峰值吞吐
```
> 注意：这只是「刚好打满吞吐」的并发下界；真实压测需在此之上加压找拐点。

## 深化能力（V2）

- 容量规划计算：`scripts/calc_capacity.py` 由 峰值QPS × 平均RT × 余量 推导目标并发
  与所需 TPS，并给出拐点/饱和识别提示。
- 容量公式、资源监控指标（CPU/内存/连接）、测试清单见 `references/checklist.md`。

## 与上下游衔接

- 输入：`qa-req-spec` / `qa-test-analysis` 的 NFR 与测试点。
- 输出：`qa-perf-locust`（脚本）、`qa-perf-analysis`（结果）、`qa-report`（结论）。
- 与 JMeter 路线互通：同 schema 直接喂给 `qa-perf-jmeter`。
