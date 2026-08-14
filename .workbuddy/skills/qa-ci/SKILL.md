---

name: qa-ci
description: |-
  用于生成 CI/CD 流水线配置，让每次 push/PR 都自动运行 QA 测试套件
  （lint + 单元测试 + 接口/UI/安全扫描）。本技能从一份配置 JSON 生成可直接提交的
  GitHub Actions、GitLab CI、Jenkinsfile 配置，默认串起 lint → 单元 → 接口/UI →
  安全扫描的质量门禁。触发词："CI配置"、"流水线"、"GitHub Actions"、"GitLab CI"、
  "Jenkins"、"把测试接进CI"。
  英文触发词（English triggers）：CI/CD, pipeline, GitHub Actions, Jenkins.
license: MIT
compatibility: "WorkBuddy / Claude / 通用 Agent（零依赖标准库）"

metadata:
  version: "1.0.0"
  category: traditional
  stage: cross_cutting
  tier: 1
---
# qa-ci — CI/CD 流水线配置生成

把「测试接进流水线」这一步做成确定性生成：一份配置 JSON →
GitHub Actions / GitLab CI / Jenkinsfile 三选一或全要。
默认串起 **lint → 单元 → 接口/UI → 安全扫描**，让你每次提交都跑质量门禁。

> 测试不进 CI，等于没测。先有流水线，质量才有持续保障。

## 何时使用

- 要把测试套件接入持续集成。
- 用户说「CI 配置」「流水线」「GitHub Actions」「GitLab CI」「Jenkins」「把测试接进 CI」。

## 操作流程

### 步骤 1 — 填配置

```json
{"project":"order-svc","python_version":"3.13","providers":["github","gitlab"],
 "test_cmd":"pytest -q","lint_cmd":"flake8 .","security_cmd":"semgrep --config auto",
 "services":["postgres"],"branches":["main"]}
```

### 步骤 2 — 生成

```bash
python scripts/gen_ci.py --config ci.json --outdir ./ci_out
```

在 `ci_out/` 生成对应文件（` .github/workflows/qa.yml` / `.gitlab-ci.yml` / `Jenkinsfile`），
含 install → lint → test → security 阶段，缺省失败即阻断合并。

### 步骤 3 — 接入

- GitHub：提交 `.github/workflows/qa.yml`，PR 自动跑。
- GitLab：提交 `.gitlab-ci.yml`，需共享 Runner。
- Jenkins：用 Pipeline 导入 `Jenkinsfile`。

## 阶段约定

| 阶段 | 做什么 | 失败影响 |
| --- | --- | --- |
| install | 装依赖 | 阻断 |
| lint | 代码规范 / 静态检查 | 阻断 |
| test | 单元 + 接口/UI | 阻断 |
| security | Semgrep / Trivy | 阻断（可设警告阈值） |

## 与上下游衔接

- 输入：各专项技能的可执行命令（`qa-api-runner` pytest、`qa-security-scan` semgrep/trivy）。
- 输出：流水线文件 → 仓库提交；失败转 `qa-bug-report`。

## 参考资料

- 检查项、阈值、CLI 用法与常见坑：见 [`references/guide.md`](references/guide.md)。
