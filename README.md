# 通用测试技能套件 (Universal QA Skills — L5.0 Industrial Edition)

> 🚀 **全球领先的 AI-First 通用 QA 细分领域技能库与 MCP 基础设施**。
> 覆盖「需求 → 分析 → 用例 → TDM造数/环境 → 接口契约 → 多端执行 → 质量红线/缺陷/发布 → 归档」完整生命周期，外加 11 项横切门禁、2 个 Agent 专属评测技能、**Model Context Protocol (MCP) 原生服务**、**TIA 精准测试**与**红蓝博弈自主进化引擎**。

[![version](https://img.shields.io/badge/version-v11.0.0_L5.0-blue)](./SKILLS_DELIVERY.md)
[![license](https://img.shields.io/badge/license-MIT-green)](./LICENSE)
[![mcp](https://img.shields.io/badge/MCP-JSON--RPC_2.0-purple)](./skills/tools/mcp_server.py)
[![evals](https://img.shields.io/badge/Eval-100%25_Passed-brightgreen)](./evals/run_evals.py)
[![zero-deps](https://img.shields.io/badge/Zero--Deps-36_Skills-orange)]()

---

## 🏷️ 推荐的 GitHub About 与 Topics 设置

请在您的 [GitHub 仓库主页](https://github.com/jianjian12138/test-skills) 右上角 **⚙️ Edit repository details** 中填入：

- **Description (About)**:
  `AI-driven Universal QA Skills, MCP Server, Precision Testing (TIA), and Evals for all AI coding agents.`
- **Website**:
  `https://github.com/jianjian12138/test-skills`
- **Topics (标签推荐)**:
  `testing` `ai-agent` `qa-automation` `model-context-protocol` `mcp-server` `pytest` `playwright` `testops` `precision-testing` `promptfoo` `developer-tools`

---

## 🏗️ L5.0 全球顶级工业级架构全景

```text
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               Universal QA Skills 体系全景 (L5.0)                               │
├────────────────────────────────┬────────────────────────────────┬───────────────────────────────┤
│       40 个细分原子 QA 技能     │    MCP 原生服务 (JSON-RPC)     │    自动化 Eval 质量评测飞轮   │
├────────────────────────────────┼────────────────────────────────┼───────────────────────────────┤
│ • 8 大生命周期阶段全覆盖       │ • 零依赖 stdio 管道            │ • Golden Dataset 基准测试集   │
│ • 11 项数据驱动横切门禁        │ • Cursor / Claude Code 即插即用│ • 确定性 Grader 规则打分器    │
│ • 2 项 Agent 专属评测与安全    │ • 动态造数 / 门禁评估 / TIA     │ • CI 质量硬门禁 (最低 85 分)  │
├────────────────────────────────┼────────────────────────────────┼───────────────────────────────┤
│   🎯 TIA 精准测试分析引擎      │   ⚡ 流量镜像重放 (Shadow QA)   │   ⚔️ 红蓝对抗自主进化引擎     │
├────────────────────────────────┼────────────────────────────────┼───────────────────────────────┤
│ • Git Diff + AST 语法调用链    │ • HAR / 网关流量基准快照沉淀   │ • 红队: 变异/越权/注入攻击    │
│ • 秒级计算变更受影响用例       │ • 零代码智能重放与 Diff 断言   │ • 蓝队: 自愈加固生成防御用例  │
└────────────────────────────────┴────────────────────────────────┴───────────────────────────────┘
```

---

## ⚡ 极速开始 (Quick Start)

### 1. 使用 `qaskills` 统一交互式 CLI

```bash
# ① 检索 40 个细分测试技能
python qaskills.py list
python qaskills.py search api

# ② 动态生成中国大陆合规脱敏测试数据 (手机号/身份证/姓名)
python qaskills.py data --type id_card --count 3
python qaskills.py data --type phone --count 3

# ③ 运行 TIA 精准测试分析 (查看 Git 变更影响了哪些用例)
python qaskills.py tia --diff HEAD~1

# ④ 运行红蓝对抗自主进化博弈
python qaskills.py swarm

# ⑤ 运行技能自动化 Eval 质量打分套件
python qaskills.py eval
```

---

## 🔌 接入 Model Context Protocol (MCP)

本套件原生内置基于纯标准库的 QA MCP Server，可直接在 **Cursor / Claude Code / Antigravity** 的 `mcp_config.json` 中挂载：

```json
{
  "mcpServers": {
    "universal-qa-skills": {
      "command": "python",
      "args": ["/path/to/test-skills/skills/tools/mcp_server.py"]
    }
  }
}
```

**支持的 MCP 原生 Tools**：
- `list_qa_skills`：动态检索 40 个细分领域技能；
- `generate_test_data`：动态生成合规大陆手机号、身份证与姓名；
- `sanitize_sensitive_data`：输入数据主动脱敏清洗（打码掩码）；
- `run_quality_gate`：质量信号红线门禁评估；
- `run_tia_analysis`：Git 变更精准测试分析；
- `run_red_blue_swarm`：红蓝博弈自愈加固。

---

## 📦 40 个细分 QA 技能完整矩阵

### ① 需求与测试分析
- `qa-req-spec`：非结构化 PRD / 原型文档智能结构化与提取
- `qa-test-analysis`：需求细化拆解、测试点全维度覆盖与风险识别

### ② 用例生成与测试数据 (TDM)
- `qa-test-case-gen`：标准测试用例集生成与 Excel 导出
- `qa-test-data`：本土化合规测试数据工厂（身份证校验码/手机号/动态时间序列/智能 PII 脱敏）
- `qa-env-config`：多环境配置隔离与 Base URL 映射

### ③ 接口契约与多端自动化执行
- `qa-api-doc`：接口规范生成与校验
- `qa-api-contract`：OpenAPI 3.0 / 3.1 破坏性变更检测与 `$ref` 递归解析
- `qa-api-runner`：接口自动化测试真实执行与断言
- `qa-ui-automation`：Playwright UI 自动化测试与**多级选择器自愈 (Self-Healing)**
- `qa-ui-kb` / `qa-ui-testid`：UI 页面对象知识库与 `data-testid` 自动注入
- `qa-perf-locust` / `qa-perf-jmeter` / `qa-perf-design`：性能压测全生命周期方案与脚本生成
- `qa-mobile-autotest`：移动端 App 自动化测试流水线
- `qa-security-scan`：OWASP Top 10 安全核查与敏感信息扫描
- `qa-exploratory`：探索性测试章程（Charter）与启发式引导
- `qa-compat-matrix`：OS × 浏览器 × 设备跨端兼容性矩阵

### ④ 报告、缺陷、发布与归档
- `qa-report`：执行结果多维度聚合图表与上线评估
- `qa-bug-report` / `qa-bug-verify`：结构化缺陷单与验证闭环
- `qa-release-check`：生产发布多重上线门禁检查
- `qa-archive`：测试资产全量版本化归档

### ⑤ 横切质量门禁与 Agent 专属测试
- `qa-risk-based` / `qa-flaky-detect` / `qa-mutation` / `qa-a11y` / `qa-visual-regression` / `qa-unit-tdd` / `qa-chaos` / `qa-ci` / `qa-synthetic-monitoring`
- `qa-agent-eval`：被测 AI Agent 本身的能力、Pass@k 与轨迹可靠性评估
- `qa-agent-security`：被测 AI Agent 的 Prompt 越狱注入与红队安全测试

---

## 🧪 自动化评测体系 (Eval Harness)

每次技能迭代均可通过以下命令进行防回归量化跑分：

```bash
python evals/run_evals.py
```

```text
============================================================
  🧪 Universal QA Skills - 自动化 Eval 评测套件
============================================================
▶ [qa-test-case-gen] 用户认证与支付用例集   -> 100.0 / 100.0 [✅ PASS]
▶ [qa-agent-security] Prompt 注入与越狱报告 -> 100.0 / 100.0 [✅ PASS]
============================================================
  📊 综合质量得分: 100.0 / 100.0 | 最低门禁: 85.0 分 (🎉 全部通过)
============================================================
```

---

## 📄 开源许可证

本项目基于 [MIT License](./LICENSE) 开源。
