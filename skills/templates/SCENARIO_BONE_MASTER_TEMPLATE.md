# 通用业务场景“骨·肉·尺”主模板 (SCENARIO_BONE_MASTER_TEMPLATE.md — v12.1.0)

> **架构原则**：本模板提供与特定行业解耦的**“场景骨架模具”**。使用时先填写第一部分立好业务之**【骨】**，再在第二部分的每个节点插槽中挂载 `test-skills` 的 46 个纯通用原子技能填入深潜之**【肉】**，最后按第三部分的双轴之**【尺】**执行门禁验收。

## 一、【骨】业务场景状态机主干与守恒律 (Business Skeleton — 测试设计准则)
- **场景 ID 与名称**：`SCEN-[编号]` / `[填入业务场景名称]`
- **前置条件与角色矩阵**：`[角色 A / 租户 A / 初始资源状态]`
- **正向主干状态流转链**：
  `[初始态 S0] --(节点 N1: 接口/UI/事件)--> [中间态 S1] --(节点 N2: 核心处理/异步回调)--> [终态 S2]`
- **逆向逃生与异常补偿路径**：
  - `逆向分支 E1 (超时/取消)`：在 `[S1]` 触发超时或取消 -> 状态回退至 `[S_CLOSED]`，且前置锁定资源 100% 释放。
  - `逆向分支 E2 (重放/幂等)`：在 `[N1/N2]` 重复收到相同幂等键请求 -> 仅首次生效，后续请求幂等返回且零额外副作用。
- **跨节点业务守恒律 (Business Invariants — 跑完整个场景必须恒成立)**：
  - `守恒律 I1`：`[前置扣减/锁定总量] == [终态生效总量] + [异常回滚释放总量]`
  - `守恒律 I2`：`[主业务表状态] 与 [流水表/审计日志/外部通道状态] 100% 最终一致`

## 二、【肉】场景节点下钻与通用 Skill 挂载槽位表 (Node-Level Skill Slots — 节点深潜准则)
> 拒绝脱离场景的孤立接口断言；沿着上方场景骨架的每个节点（N1, N2...），按需挂载以下通用原子技能把每个节点打穿：

| 场景节点 | 节点形态 | 挂载【数据与边界】通用 Skill | 挂载【契约与权限】通用 Skill | 挂载【性能与韧性】通用 Skill | 挂载【安全与可观测】通用 Skill |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **节点 N1**<br>`[入口节点]` | `API / UI` | `qa-test-data` (合规造数)<br>`qa-unit-tdd` (空值/极值/边界) | `qa-api-contract` ($ref 校验)<br>`qa-compat-matrix` (跨端正交) | `qa-ui-automation` (ARIA 自愈)<br>`qa-a11y` (WCAG 无障碍) | `qa-security-scan` (注入核查)<br>`qa-privacy-compliance` (脱敏) |
| **节点 N2**<br>`[核心变更]` | `API / DB` | `qa-test-case-gen` (异常矩阵)<br>`qa-mutation` (AST 变异测试) | `qa-api-runner` (链路断言)<br>`bola-fuzz` (3D 越权矩阵) | `qa-perf-locust` (并发抢锁)<br>`qa-db-benchmark` (死锁压测) | `qa-agent-security` (红蓝对抗)<br>`qa-log-triage` (链路追踪) |
| **节点 N3**<br>`[异步/终态]` | `MQ / Cron` | `qa-data-reconcile` (对账核对)<br>`qa-flaky-detect` (竞态治理) | `qa-graphql-grpc` (多协议)<br>`qa-shadow-replay` (流量比对) | `qa-chaos` (超时/熔断注入)<br>`qa-synthetic-monitoring` (拨测) | `qa-release-check` (上线门禁)<br>`qa-archive` (基线归档) |

## 三、【尺】纵横双轴验收与度量红线 (Dual-Axis Gate — 验收与度量准则)
- **纵轴 · 场景连通性门禁（上线必要条件，保证“用户能走通”）**：
  - 正向状态机主干 + 逆向逃生分支通过率 = **100%**
  - 跨节点业务守恒律（`qa-data-reconcile`）核对偏差 = **0**
- **横轴 · 节点深潜覆盖度门禁（上线充分条件，严禁用场景通过率代替覆盖率）**：
  - 节点关联代码的增量行/分支覆盖率（`python3 qaskills.py tia`） >= **85.0%**
  - 节点 3D BOLA 越权矩阵（36 向量）与 OWASP ASI/AST10 红队探针拦截率 = **100%**
  - AI 辅助测试多轮执行一致性（`python3 qaskills.py eval` -> `τ-bench pass^5`） >= **85.0%**
