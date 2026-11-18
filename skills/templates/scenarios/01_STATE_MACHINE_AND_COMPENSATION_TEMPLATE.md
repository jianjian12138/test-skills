# SCEN-TPL-01 — 状态机流转与逆向超时/退回补偿场景模板

> **适用范围（零业务耦合通用模具）**：适用于任何包含“创建 -> 锁定 -> 确认/完成 -> 超时关闭/主动取消/逆向退回”的生命周期流转业务。

## 一、【骨】场景状态机主干与守恒律 (Business Skeleton)
- **正向主干流转**：`[初始态 S0: DRAFT] --(动作 N1: 创建并锁定前置资源)--> [中间态 S1: PENDING] --(动作 N2: 确认/履约)--> [终态 S2: COMPLETED]`
- **逆向逃生与异常补偿**：分支 E1 (超时/取消): [S1: PENDING] --(超过 TTL 或主动取消)--> [S_CLOSED] 且 100% 释放 N1 锁定的资源；分支 E2 (终态逆向): [S2: COMPLETED] --(发起退回)--> [S_REVERSED] 且冲正台账。
- **跨节点业务守恒律**：守恒式 1: 锁定资源总量 == 已履约消耗量 + 已取消释放量 + 在途锁定中数量；守恒式 2: 已关闭(S_CLOSED)状态严禁再次跃迁至已完成(S2)。

## 二、【肉】节点通用 Skill 挂载槽位 (Node-Level Skill Slots)
- **入口与造数槽位**：挂载 `qa-req-spec`、`qa-test-analysis`、`qa-test-data`（`order_chain` 状态机关联造数与 PII 脱敏）。
- **契约与越权槽位**：挂载 `qa-api-contract`、`qa-api-runner` 与 `bola-fuzz`（验证 4 角色 × 3 动作 × 3 状态越权拦截）。
- **并发、韧性与安全槽位**：挂载 `qa-ui-automation`（ARIA 快照自愈）、`qa-perf-locust`、`qa-db-benchmark`、`qa-chaos`、`qa-data-reconcile` 与 `qa-agent-security`。

## 三、【尺】双轴验收与度量红线 (Dual-Axis Gate)
- **纵轴（必要条件）**：正向流转与逆向补偿分支 100% 走通，守恒律核对零偏差。
- **横轴（充分条件）**：增量代码行覆盖率（`tia`）>= 85.0%，3D BOLA 越权与 OWASP 红蓝探针拦截率 100%，`τ-bench pass^5` >= 85.0%。
