# 项目使用手册与快速指南 (Usage Manual)

本文档由自动化发布流程生成，提供当前项目的快速上手与使用指引。

---

## 一、目录排版结构

```text
├── ci-examples/
│   ├── Jenkinsfile
│   └── README.md
├── evals/
│   ├── grader.py
│   └── run_evals.py
├── install.ps1
├── install.sh
├── LICENSE
├── make_dist.sh
├── qaskills.py
├── README.md
├── reviews/
│   └── acceptance-final/
├── skills/
│   ├── _diag_deadlink.py
│   ├── build_registry.py
│   ├── docs/
│   ├── LICENSE
│   ├── MAINTAINERS.md
│   ├── qa-a11y/
│   ├── qa-agent-eval/
│   ├── qa-agent-security/
│   ├── qa-api-contract/
│   ├── qa-api-doc/
│   ├── qa-api-runner/
│   ├── qa-archive/
│   ├── qa-bug-report/
│   ├── qa-bug-verify/
│   ├── qa-chaos/
│   ├── qa-ci/
│   ├── qa-code-review/
│   ├── qa-compat-matrix/
│   ├── qa-env-config/
│   ├── qa-execution/
│   ├── qa-exploratory/
│   ├── qa-flaky-detect/
│   ├── qa-mobile-autotest/
│   ├── qa-mutation/
│   ├── qa-orchestrator/
│   ├── qa-perf-analysis/
│   ├── qa-perf-design/
│   ├── qa-perf-jmeter/
│   ├── qa-perf-locust/
│   ├── qa-release-check/
│   ├── qa-report/
│   ├── qa-req-spec/
│   ├── qa-risk-based/
│   ├── qa-security-report/
│   ├── qa-security-scan/
│   ├── qa-synthetic-monitoring/
│   ├── qa-test-analysis/
│   ├── qa-test-case-gen/
│   ├── qa-test-data/
│   ├── qa-test-strategy/
│   ├── qa-ui-automation/
│   ├── qa-ui-kb/
│   ├── qa-ui-testid/
│   ├── qa-unit-tdd/
│   ├── qa-visual-regression/
│   ├── README.md
│   ├── references/
│   ├── REGISTRY.json
│   ├── templates/
│   ├── tests/
│   ├── tools/
│   └── workflows/
├── SKILLS_DELIVERY.md
└── training/
    ├── 01-认识测试技能套件.md
    ├── 02-安装与环境准备.md
    ├── 03-第一次跑通一条测试.md
    ├── 04-需求与测试分析.md
    ├── 05-用例与测试数据.md
    ├── 06-接口测试全流程.md
    ├── 07-执行阶段的多种测试类型.md
    ├── 08-报告缺陷发布与归档.md
    ├── 09-横切质量门禁与CI集成.md
    └── 10-Agent测试专题与进阶最佳实践.md
```

---

## 二、环境要求与前置依赖

- **Python** >= 3.10
- **Node.js** >= 18 (如包含前端模块)
- **Git** >= 2.30

---

## 三、快速开始

### 1. 安装与初始化
```bash
pip install -r requirements.txt  # 或 npm install
```

### 2. 本地运行与验证
```bash
pytest  # 或 npm run dev
```

---

## 四、贡献与提交规范

- 提交前请执行代码清理与门禁检查；
- 遵循 Conventional Commits 规范（feat/fix/docs/chore/refactor）。
