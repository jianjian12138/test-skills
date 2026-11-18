# SCEN-TPL-02 — 高并发资源争抢与配额/余额扣减场景模板

> **适用范围（零业务耦合通用模具）**：适用于任何包含有限配额、库存、账户余额、并发抢锁、防超卖与防双花幂等的业务场景。

## 一、【骨】场景状态机主干与守恒律 (Business Skeleton)
- **正向主干流转**：`[初始配额 Q0 > 0] --(动作 N1: N 个并发请求同时申请扣减 Δq)--> [原子锁校验与扣减 N2] --(动作 N3: 写入扣减流水)--> [剩余配额 Q_rem >= 0]`
- **逆向逃生与异常补偿**：分支 E1 (配额不足): 当 Q_rem < Δq 时立即拒绝并返回确定性错误码，严禁出现 Q_rem < 0；分支 E2 (相同幂等键重放): 同一 request_id 并发重发 50 次仅生效 1 次。
- **跨节点业务守恒律**：守恒式 1: 初始配额 Q0 - 剩余配额 Q_rem == Σ(成功扣减流水金额/数量)；守恒式 2: 任何时刻 Q_rem >= 0（零超扣/零负值）。

## 二、【肉】节点通用 Skill 挂载槽位 (Node-Level Skill Slots)
- **入口与造数槽位**：挂载 `qa-req-spec`、`qa-test-analysis`、`qa-test-data`（`order_chain` 状态机关联造数与 PII 脱敏）。
- **契约与越权槽位**：挂载 `qa-api-contract`、`qa-api-runner` 与 `bola-fuzz`（验证 4 角色 × 3 动作 × 3 状态越权拦截）。
- **并发、韧性与安全槽位**：挂载 `qa-ui-automation`（ARIA 快照自愈）、`qa-perf-locust`、`qa-db-benchmark`、`qa-chaos`、`qa-data-reconcile` 与 `qa-agent-security`。

## 三、【尺】双轴验收与度量红线 (Dual-Axis Gate)
- **纵轴（必要条件）**：正向流转与逆向补偿分支 100% 走通，守恒律核对零偏差。
- **横轴（充分条件）**：增量代码行覆盖率（`tia`）>= 85.0%，3D BOLA 越权与 OWASP 红蓝探针拦截率 100%，`τ-bench pass^5` >= 85.0%。
