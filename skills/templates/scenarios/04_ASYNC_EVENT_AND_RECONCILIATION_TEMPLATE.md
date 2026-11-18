# SCEN-TPL-04 — 异步事件驱动、乱序回调与跨库最终一致性对账场景模板

> **适用范围（零业务耦合通用模具）**：适用于任何包含 Webhook 异步通知、消息队列投递、回调乱序到达与跨系统对账（Reconciliation）的业务场景。

## 一、【骨】场景状态机主干与守恒律 (Business Skeleton)
- **正向主干流转**：`[主系统发起异步指令 N1] --(动作 N2: 外部通道异步处理)--> [接收 Webhook/MQ 回调 N3] --(动作 N4: 更新本地状态并触发对账 N5)--> [对账平账 RECONCILED]`
- **逆向逃生与异常补偿**：分支 E1 (回调乱序): “完成通知”先于“处理中通知”到达 -> 状态机遵循高水位单调递增，严禁被旧状态覆盖回退；分支 E2 (通知丢失): 主动轮询补偿任务在 T+N 分钟内拉平状态。
- **跨节点业务守恒律**：守恒式 1: 上游通道成功总笔数/总额 == 下游落库成功总笔数/总额 + 待平账差错池记录；守恒式 2: 重复投递 K 次回调产生的业务副作用次数 == 1。

## 二、【肉】节点通用 Skill 挂载槽位 (Node-Level Skill Slots)
- **入口与造数槽位**：挂载 `qa-req-spec`、`qa-test-analysis`、`qa-test-data`（`order_chain` 状态机关联造数与 PII 脱敏）。
- **契约与越权槽位**：挂载 `qa-api-contract`、`qa-api-runner` 与 `bola-fuzz`（验证 4 角色 × 3 动作 × 3 状态越权拦截）。
- **并发、韧性与安全槽位**：挂载 `qa-ui-automation`（ARIA 快照自愈）、`qa-perf-locust`、`qa-db-benchmark`、`qa-chaos`、`qa-data-reconcile` 与 `qa-agent-security`。

## 三、【尺】双轴验收与度量红线 (Dual-Axis Gate)
- **纵轴（必要条件）**：正向流转与逆向补偿分支 100% 走通，守恒律核对零偏差。
- **横轴（充分条件）**：增量代码行覆盖率（`tia`）>= 85.0%，3D BOLA 越权与 OWASP 红蓝探针拦截率 100%，`τ-bench pass^5` >= 85.0%。
