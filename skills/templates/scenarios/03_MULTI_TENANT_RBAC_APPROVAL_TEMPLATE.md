# SCEN-TPL-03 — 多角色审批流与跨租户权限隔离场景模板

> **适用范围（零业务耦合通用模具）**：适用于任何包含多租户隔离（Tenant A/B）、多角色分级授权（提交人/审批人/审计员）与状态越权防护的业务场景。

## 一、【骨】场景状态机主干与守恒律 (Business Skeleton)
- **正向主干流转**：`[租户 A 提交人创建资源 R_A (状态: SUBMITTED)] --(动作 N1: 租户 A 审批人审核)--> [状态: APPROVED] --(动作 N2: 执行生效)--> [状态: ACTIVE]`
- **逆向逃生与异常补偿**：分支 E1 (横向越权 BOLA): 租户 B 任何角色尝试读取/修改/删除 R_A -> 必须 100% 拦截 (403/404)；分支 E2 (职责分离冲突): 提交人尝试自审自批 R_A -> 必须拦截 (403)。
- **跨节点业务守恒律**：守恒式 1: 跨租户数据可见性交集 == 空集 (∅)；守恒式 2: 未经 APPROVED 状态的资源严禁直接进入 ACTIVE 态。

## 二、【肉】节点通用 Skill 挂载槽位 (Node-Level Skill Slots)
- **入口与造数槽位**：挂载 `qa-req-spec`、`qa-test-analysis`、`qa-test-data`（`order_chain` 状态机关联造数与 PII 脱敏）。
- **契约与越权槽位**：挂载 `qa-api-contract`、`qa-api-runner` 与 `bola-fuzz`（验证 4 角色 × 3 动作 × 3 状态越权拦截）。
- **并发、韧性与安全槽位**：挂载 `qa-ui-automation`（ARIA 快照自愈）、`qa-perf-locust`、`qa-db-benchmark`、`qa-chaos`、`qa-data-reconcile` 与 `qa-agent-security`。

## 三、【尺】双轴验收与度量红线 (Dual-Axis Gate)
- **纵轴（必要条件）**：正向流转与逆向补偿分支 100% 走通，守恒律核对零偏差。
- **横轴（充分条件）**：增量代码行覆盖率（`tia`）>= 85.0%，3D BOLA 越权与 OWASP 红蓝探针拦截率 100%，`τ-bench pass^5` >= 85.0%。
