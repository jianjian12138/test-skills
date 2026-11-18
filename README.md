# 通用测试技能套件 (Universal QA Skills — v12.1.0 L6.0 自治质量工程网格)

🚀 **AI-First 工业级通用 QA 原子技能库、可插拔场景骨架模具与双模 MCP 基础设施（v12.1.0 L6.0 版）**。以**“场景是骨、接口是肉、双轴为尺”**为最高测试工程宪章，严格遵循**“三层正交解耦架构”**——顶层提供测试设计/验收/度量准则，中间层提供与特定行业解耦的 **6 套通用业务场景骨架模板**，底层内置 **49 项零业务耦合的纯通用原子 QA 技能**、**L1/L2 渐进式技能路由器**、**`stdio` + [MCP Streamable HTTP](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports) 双模网关**、**AST + `coverage.py` 动静融合精准测试（TIA）**、**[Playwright MCP](https://playwright.dev/mcp/introduction) ARIA 无障碍树自愈**、**[OWASP ASI:2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/) & [AST10](https://owasp.org/projects/agentic-skills-top-10) 红蓝对抗飞轮**及 **[τ-bench (tau-bench)](https://arxiv.org/html/2406.12045v1) `pass^k` ($k=5$)** 自动化评测门禁。

- **仓库主页**：[jianjian12138/test-skills](https://github.com/jianjian12138/test-skills)
- **当前版本**：`v12.1.0`（L6.0 Bone-Meat-Ruler Edition）
- **核心特性**：`Bone-Meat-Ruler Charter` · `6 Pluggable Scenario Templates` · `49 Universal Skills (Zero Domain Coupling)` · `Dual-Mode MCP` · `Hybrid TIA` · `Playwright ARIA Healer` · `3D BOLA Fuzzer` · `τ-bench pass^5 Evals`
- **开源协议**：MIT License

## 1. 核心测试工程宪章：“场景是骨、接口是肉、双轴为尺”

在测试过程与 AI Agent 自动化测试中，对“以业务场景为基础”必须按**设计、验收、度量**三个维度严格定界（详见 `skills/docs/TESTING_CHARTER_BONE_MEAT_RULER.md`）：

| 准则的含义 | 工程判定 | 核心理由与架构落位 |
| :--- | :--- | :--- |
| **测试设计准则**：先有场景，再有用例 | **成立，且是最优先的一条** | 用例是从场景切出来的，反过来脱离场景直接对接口切用例，极易切出一堆没人用的无效接口断言，且漏掉跨节点状态断裂。 |
| **上线验收准则**：场景全绿才允许上线 | **成立，但只能是必要条件** | 它只保证“正常用户顺着主干道能走通”，并不保证每个节点的边界极值、并发性能、跨租户越权与安全注入没问题。 |
| **质量度量准则**：用场景通过率代替覆盖率 | **不成立（严禁替代）** | 一个场景只覆盖一条路径，10 条场景全绿不代表 49 个通用技能对应的边界、异常码、BOLA 越权与死锁分支都测过。 |

> **三层正交解耦设计**：
> 1. **宪章层（骨·肉·尺准则）**：场景决定测什么、按什么顺序测、什么算走通（**骨**）；通用原子技能负责把每个节点的边界值、异常码、权限、性能打穿（**肉**）；纵轴场景连通率与横轴节点覆盖率联合裁决上线（**尺**）。
> 2. **模具层（可插拔业务场景模板 `skills/templates/`）**：业务场景不写死在技能代码里，而是作为标准化填空模具给出（含主模板 `SCENARIO_BONE_MASTER_TEMPLATE.md` 及 5 大通用拓扑模板）。
> 3. **刀片层（49 项纯通用原子技能 `skills/qa-*/`）**：所有 Skill 保持 100% 纯技术通用性，不加入任何特定行业业务逻辑，随插随用。

## 2. 6 套可插拔通用业务场景模板（`skills/templates/`）

通过 `python3 qaskills.py templates` 或 MCP 工具 `list_scenario_templates` 可直接检索并套用以下通用场景模具：

| 模板 ID | 模板文件路径 | 通用拓扑范式与适用场景 |
| :--- | :--- | :--- |
| `SCEN-MASTER` | `skills/templates/SCENARIO_BONE_MASTER_TEMPLATE.md` | **通用业务场景“骨·肉·尺”主模板**（含状态机主干、逆向逃生、守恒律、节点 Skill 挂载槽与双轴门禁） |
| `SCEN-TPL-01` | `skills/templates/scenarios/01_STATE_MACHINE_AND_COMPENSATION_TEMPLATE.md` | **状态机流转与逆向超时/退回补偿模板**（创建→锁定→履约→超时关闭释放/退回冲正） |
| `SCEN-TPL-02` | `skills/templates/scenarios/02_HIGH_CONCURRENCY_QUOTA_DEDUCTION_TEMPLATE.md` | **高并发资源争抢与配额/余额扣减模板**（原子锁、防超扣/防负值、相同幂等键并发重放） |
| `SCEN-TPL-03` | `skills/templates/scenarios/03_MULTI_TENANT_RBAC_APPROVAL_TEMPLATE.md` | **多角色审批流与跨租户权限隔离模板**（提交/审批职责分离、租户间 3D BOLA 100% 隔离） |
| `SCEN-TPL-04` | `skills/templates/scenarios/04_ASYNC_EVENT_AND_RECONCILIATION_TEMPLATE.md` | **异步事件驱动、乱序回调与跨库对账模板**（Webhook 乱序防状态回退、轮询补偿、台账平账） |
| `SCEN-TPL-05` | `skills/templates/scenarios/05_AI_AGENT_MULTI_TURN_TOOL_CALL_TEMPLATE.md` | **AI Agent 多轮工具调用、边界追问与防越狱模板**（L1 路由、缺失参数追问、OWASP ASI 防御） |

## 3. 极速开始 (Quick Start)

```bash
# ① [v12.1 新增] 查看通用业务场景“骨·肉·尺”模板清单或导出主模板
python3 qaskills.py templates
python3 qaskills.py templates --id SCEN-MASTER

# ② L1 渐进式技能路由：从 49 个纯通用技能中精准收敛 <= 4 个候选并查看 Token 节省账本
python3 qaskills.py route "Playwright ARIA 无障碍树选择器自愈"

# ③ L2 按需加载：读取指定通用技能的完整 SKILL.md 四维边界契约与本地脚本说明
python3 qaskills.py load qa-ui-automation

# ④ 生成中国大陆合规测试数据（支持 id_card / phone / name / 跨表状态机关联 order_chain）
python3 qaskills.py data --type order_chain --count 2

# ⑤ 运行动静融合 TIA 精准测试分析（Git Diff + AST + .coverage SQLite 动态上下文）
python3 qaskills.py tia --diff HEAD~1

# ⑥ 基于 Playwright MCP ARIA 快照自愈失效的 UI 选择器
python3 qaskills.py aria-heal --selector "#legacy-pay-btn" --intent "立即提交并支付"

# ⑦ 生成 3D BOLA/IDOR 接口越权测试矩阵（4 角色 × 3 动作 × 3 状态 = 36 向量）
python3 qaskills.py bola-fuzz --endpoint "/api/v1/orders/{order_id}"

# ⑧ 运行 OWASP ASI:2026 & AST10 红蓝对抗自主进化博弈
python3 qaskills.py swarm --rounds 6

# ⑨ 运行全量单元测试、跨平台无死链检查与 τ-bench pass^5 自动化评测门禁
python3 -m unittest discover -s tests -p "test_*.py" -v
python3 qaskills.py eval
```

## 4. 接入双模 Model Context Protocol (MCP)

本套件内置纯标准库双模 MCP 服务端（暴露 `list_scenario_templates`、`route_qa_skills`、`load_skill_sop`、`list_qa_skills`、`generate_test_data`、`sanitize_sensitive_data`、`run_tia_analysis`、`heal_ui_locator_aria`、`run_quality_gate`、`run_red_blue_swarm` 共 **10 个原生 MCP Tools**）：

```json
{
  "mcpServers": {
    "universal-qa-skills-l6": {
      "command": "python3",
      "args": ["/path/to/test-skills/skills/tools/mcp_server.py", "--transport", "stdio"]
    }
  }
}
```

远程团队共享模式（[MCP Streamable HTTP](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports)）：

```bash
python3 qaskills.py serve-mcp --transport http --host 127.0.0.1 --port 8765
```

## 5. 49 个纯通用原子 QA 技能全景矩阵

| 生命周期阶段 | 包含的纯通用原子技能 ID（共 49 项，零业务耦合） |
| :--- | :--- |
| **① 需求、分析与顶层策略** (`requirements`) | `qa-req-spec`、`qa-prompt-refine`（模糊指令打磨为可执行契约）、`qa-test-analysis`、`qa-code-review`、`qa-test-strategy` |
| **② 用例生成与测试数据** (`tdm_cases`) | `qa-test-case-gen`、`qa-test-data`、`qa-mock-service`（下游未就绪时的状态化 Mock）、`qa-env-config` |
| **③ 接口契约与多协议测试** (`api_testing`) | `qa-api-doc`、`qa-api-contract`、`qa-api-runner`、`qa-graphql-grpc` |
| **④ UI、移动端与跨端执行** (`ui_mobile`) | `qa-ui-automation`（[Playwright MCP ARIA](https://testquality.com/playwright-test-agents-mcp-architecture-2026/)）、`qa-ui-kb`、`qa-ui-testid`、`qa-mobile-autotest`、`qa-compat-matrix`、`qa-exploratory`、`qa-execution` |
| **⑤ 性能、压测与容量诊断** (`performance`) | `qa-perf-design`、`qa-perf-locust`、`qa-perf-jmeter`、`qa-db-benchmark`、`qa-perf-analysis` |
| **⑥ 安全扫描、审计与合规** (`security`) | `qa-security-scan`、`qa-privacy-compliance`、`qa-security-report` |
| **⑦ 报告、缺陷、发布与归档** (`release_ops`) | `qa-report`、`qa-bug-report`、`qa-bug-verify`、`qa-incident-retro`（事故时间线与改进项闭环）、`qa-release-check`、`qa-archive` |
| **⑧ 横切门禁、编排与 Agent 评测** (`quality_gates_agent`) | `qa-orchestrator`、`qa-risk-based`、`qa-flaky-detect`、`qa-mutation`、`qa-a11y`（[WCAG 2.2](https://playwrightmasters.in/playwright-accessibility/)）、`qa-visual-regression`、`qa-unit-tdd`、`qa-chaos`、`qa-ci`、`qa-synthetic-monitoring`、`qa-log-triage`、`qa-data-reconcile`、`qa-shadow-replay`、`qa-agent-eval`（[τ-bench `pass^k`](https://qaskills.sh/blog/tau-bench-agent-evaluation-guide-2026)）、`qa-agent-security`（[OWASP ASI:2026](https://deepstrike.io/blog/agentic-ai-security) & [AST10](https://owasp.org/projects/agentic-skills-top-10)） |

## 6. 开源许可证

本项目基于 **MIT License** 开源。
