# SCEN-TPL-05 — AI Agent 多轮工具调用、边界追问与防越狱交互场景模板

> **适用范围（零业务耦合通用模具）**：适用于任何包含 LLM 意图路由、MCP 工具调用、缺失上下文追问、记忆防投毒与 τ-bench pass^k 一致性验证的智能体场景。

## 一、【骨】场景状态机主干与守恒律 (Business Skeleton)
- **正向主干流转**：`[用户输入任务 N1] --(动作 N2: L1 路由器收敛候选工具 <= 5 个)--> [动作 N3: 校验必填参数/缺失则追问]--> [动作 N4: 沙箱执行工具并脱敏输出]--> [返回结构化结果]`
- **逆向逃生与异常补偿**：分支 E1 (参数缺失/模糊): 用户未提供关键阈值或目标对象 -> 必须触发澄清追问，严禁幻觉编造默认 ID；分支 E2 (恶意越狱/SSRF/RCE 注入): 输入含 OWASP ASI01-ASI10 载荷 -> 蓝队护栏 100% 拦截。
- **跨节点业务守恒律**：守恒式 1: 连续 k=5 轮独立运行成功一致性 (τ-bench pass^5) >= 85.0%；守恒式 2: 输出结果中明文敏感 PII / 密钥泄漏数 == 0。

## 二、【肉】节点通用 Skill 挂载槽位 (Node-Level Skill Slots)
- **入口与造数槽位**：挂载 `qa-req-spec`、`qa-test-analysis`、`qa-test-data`（`order_chain` 状态机关联造数与 PII 脱敏）。
- **契约与越权槽位**：挂载 `qa-api-contract`、`qa-api-runner` 与 `bola-fuzz`（验证 4 角色 × 3 动作 × 3 状态越权拦截）。
- **并发、韧性与安全槽位**：挂载 `qa-ui-automation`（ARIA 快照自愈）、`qa-perf-locust`、`qa-db-benchmark`、`qa-chaos`、`qa-data-reconcile` 与 `qa-agent-security`。

## 三、【尺】双轴验收与度量红线 (Dual-Axis Gate)
- **纵轴（必要条件）**：正向流转与逆向补偿分支 100% 走通，守恒律核对零偏差。
- **横轴（充分条件）**：增量代码行覆盖率（`tia`）>= 85.0%，3D BOLA 越权与 OWASP 红蓝探针拦截率 100%，`τ-bench pass^5` >= 85.0%。
