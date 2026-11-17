# 通用测试技能套件 (Universal QA Skills — v12.0.0 L6.0 Autonomous Quality Engineering Mesh)

🚀 **AI-First 工业级自治 QA 技能网格与双模 MCP 基础设施（v12.0.0 L6.0 升级版）**。全面覆盖「需求 → 分析 → 用例 → 状态机关联 TDM 造数/脱敏 → 接口契约/3D BOLA 模糊测试 → ARIA 无障碍树 UI 自愈执行 → 质量红线/缺陷/发布 → 归档」完整研发生命周期，内置 **40 项原子 QA 技能**、**L1/L2 渐进式技能路由器**、**`stdio` + `Streamable HTTP` 双模 MCP 网关**、**AST + `coverage.py` 动静融合精准测试（TIA）**、**OWASP ASI:2026 & AST10 红蓝对抗飞轮**，以及对齐 **[τ-bench (tau-bench)](https://arxiv.org/html/2406.12045v1) `pass^k` ($k=5$)** 的 3D 黄金基准评测套件。

- **仓库主页**：[jianjian12138/test-skills](https://github.com/jianjian12138/test-skills)
- **当前版本**：`v12.0.0`（L6.0 Autonomous Quality Engineering Edition）
- **核心特性**：`Zero-Deps Core` · `L1/L2 Progressive Router` · `MCP Streamable HTTP` · `Hybrid TIA` · `Playwright ARIA Healer` · `3D BOLA Fuzzer` · `OWASP ASI/AST10 Swarm` · `τ-bench pass^k Evals`
- **开源协议**：MIT License

## 1. v11.0.0 (L5.0) ➔ v12.0.0 (L6.0) 架构演进对照表

从规约驱动（Spec-Driven）迈向执行态感知驱动（Execution-State-Driven），`v12.0.0` 针对企业级微服务、高频 CI 与多智能体协作场景完成了六大核心升级：

| 架构模块 | v11.0.0 (L5.0 旧版实现) | v12.0.0 (L6.0 工业级升级实现) | 量化收益与对齐标准 |
| :--- | :--- | :--- | :--- |
| **技能上下文调度** | 40 个技能扁平全量暴露，易造成 Coding Agent 注意力稀释 | **L1/L2 渐进式技能路由器** (`skills/tools/router.py`) + `contextvars` 分布式 Token 账本 | 单轮收敛至 `<= 4` 个候选技能，Prompt Token 消耗降低 **96%+** |
| **MCP 通信传输层** | 仅支持单机一对一 `stdio` 管道 | **双模 MCP Server** (`stdio` + [MCP Streamable HTTP](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports) 单端点 `/mcp`) | 支持 `Mcp-Session-Id` 会话保持与 `X-Trace-Id` 团队级 CI 共享网关 |
| **TIA 精准测试引擎** | 仅基于 `Git Diff + Python AST` 静态语法树推导 | **动静双擎融合 TIA** (`skills/tools/tia_engine.py`：静态 AST + `.coverage` SQLite 动态行级上下文) | 穿透 FastAPI `Depends` 与 Pytest 动态 Fixture，召回率跃升至 **96%+** |
| **UI 自动化自愈** | 传统 DOM CSS/XPath 多级降级自愈 | **[Playwright MCP](https://playwright.dev/mcp/introduction) ARIA 无障碍树快照自愈** (`skills/tools/ui_healer.py`) | 单次快照仅耗 **~70–350 Tokens**（相比原始 DOM 节省 **90%+**），自动生成 `get_by_role` 补丁并附带 [WCAG 2.2](https://playwrightmasters.in/playwright-accessibility/) 告警 |
| **测试数据与契约验证** | 单字段身份证/手机号生成 + 静态 OpenAPI `$ref` 解析 | **跨表订单状态机关联造数** (`order_chain`) + **3D BOLA 越权模糊矩阵** (`api_contract_fuzzer.py`) | 保障 `Users -> Orders -> Payments -> Inventory` 外键与余额守恒，自动生成 **36 条**租户×角色×状态越权向量 |
| **Agent 评测与安全红蓝对抗** | 2 条静态样本单次 `Pass@1` 跑分 + 基础 Prompt 越狱检查 | **12 条 3D 黄金集 + [τ-bench `pass^5`](https://qaskills.sh/blog/tau-bench-agent-evaluation-guide-2026) 幂次一致性评测** + **[OWASP ASI:2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/) & [AST10](https://owasp.org/projects/agentic-skills-top-10) 红蓝飞轮** | 覆盖 50% 正向 + 30% 边界追问 + 20% 恶意探针（目标劫持/SSRF/RCE/记忆投毒），硬门禁 `pass^5 >= 85.0%` |

## 2. L6.0 核心目录结构

```text
test-skills/
├── qaskills.py                         # 统一交互式 CLI (支持 list/route/load/data/sanitize/tia/aria-heal/bola-fuzz/swarm/eval/serve-mcp)
├── pyproject.toml                      # 零依赖标准库内核 + 可选 [pro] 插件依赖 (pytest/playwright/hypothesis/schemathesis)
├── README.md                           # L6.0 架构全景与快速上手指南
├── USAGE.md                            # CLI、双模 MCP 网关与七大引擎详细操作手册
├── SKILLS_DELIVERY.md                  # 40 项原子 QA 技能完整交付矩阵
├── skills/
│   ├── registry.json                   # 40 项技能的 L1 轻量摘要索引与 Token 预算元数据
│   ├── qa-req-spec/ ... qa-agent-security/  # 全部 40 个技能的独立目录与四维契约 SKILL.md
│   └── tools/
│       ├── router.py                   # L1/L2 渐进式技能路由器 + contextvars trace_id 与 Token 成本账本
│       ├── mcp_server.py               # 纯标准库双模 MCP 服务端 (stdio + Streamable HTTP /mcp)
│       ├── tdm_factory.py              # GB 11643-1999 身份证校验、手机号、跨表订单状态机造数与 PII/密钥脱敏
│       ├── tia_engine.py               # Git Diff + Python AST + coverage.py SQLite 动态行级精准测试引擎
│       ├── ui_healer.py                # Playwright MCP ARIA 无障碍树 YAML 快照解析与低 Token 定位器自愈
│       ├── api_contract_fuzzer.py      # OpenAPI 3.0/3.1 递归 $ref 解析、破坏性变更检测与 3D BOLA 越权矩阵
│       ├── shadow_qa.py                # 流量镜像动态噪声清洗与零代码结构/数值 Diff 断言引擎
│       └── red_blue_swarm.py           # 对齐 OWASP ASI01-ASI10 (2026) 与 AST10 的红蓝对抗自愈引擎
├── evals/
│   ├── golden_dataset_3d.json          # 3D 黄金基准测试集 (50% 正向路径 + 30% 边界澄清 + 20% OWASP 对抗探针)
│   └── run_evals.py                    # 同时计算乐观 Pass@k 与严苛 τ-bench pass^k (k=5) 的自动化评测门禁
├── tests/
│   └── test_v12_suite.py               # 零 Token 确定性单元测试与集成验证套件 (9 大核心测试集)
├── ci-examples/
│   └── github-actions-l6-gate.yml      # 集成单元测试、混合 TIA、红蓝博弈与 pass^5 硬门禁的 GitHub Actions 流水线
├── reviews/acceptance-final/
│   └── L6_UPGRADE_AUDIT.md             # L5.0 -> L6.0 架构升级验收审计报告
└── training/
    └── QA_TO_AI_AGENT_CURRICULUM.md    # 测试与产品经理转行 AI Agent 四阶段实验实训指南
```

## 3. 极速开始 (Quick Start)

### 3.1 使用 `qaskills.py` 统一 CLI

```bash
# ① [L6.0 新增] L1 渐进式技能路由：从 40 个技能中精准收敛 <= 4 个候选并查看 Token 节省率
python3 qaskills.py route "Playwright ARIA 无障碍树选择器自愈"

# ② [L6.0 新增] L2 按需加载：仅加载目标技能的完整 SKILL.md 四维边界契约
python3 qaskills.py load qa-ui-automation

# ③ 生成中国大陆合规测试数据（支持 id_card / phone / name / 跨表关联 order_chain）
python3 qaskills.py data --type id_card --count 3
python3 qaskills.py data --type order_chain --count 2

# ④ 主动脱敏清洗输入中的大陆身份证、手机号与 OpenAI/GitHub 密钥
python3 qaskills.py sanitize "用户身份证 11010119900307251X，电话 13812345678，密钥 sk-proj1234567890abcdef"

# ⑤ 运行动静融合 TIA 精准测试分析（Git Diff + AST + .coverage SQLite 动态上下文）
python3 qaskills.py tia --diff HEAD~1

# ⑥ [L6.0 新增] 基于 Playwright MCP ARIA 快照自愈失效的 UI 选择器
python3 qaskills.py aria-heal --selector "#legacy-pay-btn" --intent "立即提交并支付"

# ⑦ [L6.0 新增] 生成 3D BOLA/IDOR 接口越权测试矩阵（4 角色 × 3 动作 × 3 状态 = 36 向量）
python3 qaskills.py bola-fuzz --endpoint "/api/v1/orders/{order_id}"

# ⑧ 运行 OWASP ASI:2026 & AST10 红蓝对抗自主进化博弈
python3 qaskills.py swarm --rounds 6

# ⑨ 运行 3D 黄金基准与 τ-bench pass^5 自动化质量评测门禁
python3 qaskills.py eval
```

### 3.2 接入双模 Model Context Protocol (MCP)

#### 模式一：本地 IDE 即插即用 (`stdio` 管道)
在 Cursor / Claude Code / Antigravity 的 `mcp_config.json` 中挂载：

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

#### 模式二：企业级远程共享网关 (`Streamable HTTP`)
依据 [MCP 2025-11-25 传输规范](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports) 与 [Cloudflare MCP 指南](https://developers.cloudflare.com/agents/model-context-protocol/protocol/transport/)，单端点 `/mcp` 原生支持 `POST` JSON-RPC 调用、`Mcp-Session-Id` 会话保持与 `X-Trace-Id` 链路追踪：

```bash
python3 qaskills.py serve-mcp --transport http --host 127.0.0.1 --port 8765
```

### 3.3 支持的 9 大 MCP 原生 Tools

| MCP Tool 名称 | 架构层级 | 功能说明 |
| :--- | :--- | :--- |
| `route_qa_skills` | `L1 Router` | 按任务意图与阶段将 40 个技能过滤为 `<= 5` 个高相关候选，附带 Token 节省账本 |
| `load_skill_sop` | `L2 Loader` | 按需读取指定技能的 `SKILL.md` 四维边界契约与 SOP 步骤 |
| `list_qa_skills` | `Discovery` | 检索全部 40 个细分领域 QA 技能清单（支持按 8 大阶段过滤） |
| `generate_test_data` | `TDM Engine` | 生成符合 GB 11643-1999 校验码的身份证、手机号、姓名及 `order_chain` 关联订单链 |
| `sanitize_sensitive_data` | `Privacy Gate` | 自动识别并掩码清洗文本中的身份证号、手机号与 API 密钥（符合 PIPL 规范） |
| `run_tia_analysis` | `Hybrid TIA` | 结合 Git Diff、Python AST 与 `.coverage` SQLite 动态上下文推导受影响测试集 |
| `heal_ui_locator_aria` | `ARIA Healer` | 解析 [Playwright MCP](https://testquality.com/playwright-test-agents-mcp-architecture-2026/) ARIA 快照自愈失效定位器并输出 WCAG 无障碍警告 |
| `run_quality_gate` | `Release Gate` | 综合覆盖率、`pass^5` 得分、P0 缺陷数与 3D BOLA 矩阵判定是否放行上线 |
| `run_red_blue_swarm` | `Security Swarm` | 执行 [OWASP ASI:2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/) 与 [OWASP AST10](https://owasp.org/projects/agentic-skills-top-10) 红蓝对抗并自动生成防御回归用例 |

## 4. 40 个细分 QA 技能完整矩阵

| 生命周期阶段 | 包含的原子技能 ID 与核心能力 |
| :--- | :--- |
| **① 需求与测试分析** (`requirements`) | `qa-req-spec`（非结构化 PRD 提取与模糊点追问）、`qa-test-analysis`（等价类/边界值/状态机风险拆解） |
| **② 用例生成与测试数据** (`tdm_cases`) | `qa-test-case-gen`（标准用例生成与导出）、`qa-test-data`（大陆合规造数与跨表订单链）、`qa-env-config`（多环境隔离与防 SSRF） |
| **③ 接口契约与多协议测试** (`api_testing`) | `qa-api-doc`（OpenAPI 规范生成）、`qa-api-contract`（`$ref` 递归解析与 3D BOLA 模糊测试）、`qa-api-runner`（链路执行）、`qa-graphql-grpc`（深度嵌套与 Protobuf 校验） |
| **④ UI、移动端与跨端执行** (`ui_mobile`) | `qa-ui-automation`（Playwright ARIA 快照自愈）、`qa-ui-kb`（防投毒签名页面知识库）、`qa-ui-testid`（AST 属性注入）、`qa-mobile-autotest`、`qa-compat-matrix`（Pairwise 正交矩阵）、`qa-exploratory` |
| **⑤ 性能、压测与容量工程** (`performance`) | `qa-perf-design`（利特尔法则容量建模）、`qa-perf-locust`（协程压测与 P99 熔断）、`qa-perf-jmeter`、`qa-db-benchmark`（慢查询与死锁压测） |
| **⑥ 安全扫描与隐私合规** (`security`) | `qa-security-scan`（OWASP Top 10 与密钥扫描）、`qa-privacy-compliance`（PIPL / GDPR 数据最小化与脱敏审计） |
| **⑦ 报告、缺陷、发布与归档** (`release_ops`) | `qa-report`（多维聚合上线报告）、`qa-bug-report`、`qa-bug-verify`（同源变体扩散验证）、`qa-release-check`（Go/No-Go 门禁）、`qa-archive` |
| **⑧ 横切质量门禁与 Agent 评测** (`quality_gates_agent`) | `qa-risk-based`、`qa-flaky-detect`、`qa-mutation`、`qa-a11y`、`qa-visual-regression`、`qa-unit-tdd`、`qa-chaos`、`qa-ci`、`qa-synthetic-monitoring`、`qa-log-triage`、`qa-data-reconcile`、`qa-shadow-replay`、`qa-agent-eval`（[τ-bench `pass^k`](https://arxiv.org/html/2406.12045v1)）、`qa-agent-security`（[OWASP ASI:2026](https://deepstrike.io/blog/agentic-ai-security) & [AST10](https://owasp.org/projects/agentic-skills-top-10)） |

## 5. 自动化评测与单元测试验证

每次代码或技能迭代均可通过零 Token 单元测试与 `evals/run_evals.py` 进行防回归量化跑分：

```bash
# 运行 9 大核心模块单元测试
python3 -m unittest discover -s tests -p "test_*.py" -v

# 运行 3D 黄金基准与 τ-bench pass^5 (k=5) 评测门禁
python3 evals/run_evals.py
```

## 6. 开源许可证

本项目基于 **MIT License** 开源。
