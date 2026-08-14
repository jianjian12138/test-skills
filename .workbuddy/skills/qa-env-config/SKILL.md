---

name: qa-env-config
description: |-
  当用户搭建或管理接口/UI 自动化的测试环境，需要把多环境配置（base URL、账号、
  token、DB 连接）与代码分离且避免泄露时使用。本技能生成各环境的 .env 模板脚手架，
  并约定环境切换与配置规范。触发词："配置测试环境"、"多环境怎么管理"、
  "接口依赖/token 怎么配"、"测试用例配置"，或在 qa-api-runner / qa-ui-automation
  之前使用。
  英文触发词（English triggers）：test environment, env config, multi-environment.
license: MIT
compatibility: "WorkBuddy / Claude / 通用 Agent（零依赖标准库）"

metadata:
  version: "1.0.0"
  category: traditional
  stage: 04-testdata
  tier: 1
---
# qa-env-config — 测试环境与配置管理

接口/UI 自动化的维护黑洞之一是「环境配置散落」：地址、账号、token、DB 写在代码或聊天里，
切换环境改一处漏一处，还容易把密码带进仓库。本技能约定**配置与代码分离、环境只改一个文件**，
并提供脚手架生成多环境模板。

## 何时使用

- 准备接口/UI 自动化运行环境。
- 用户说「配置测试环境」「多环境怎么管理」「token/依赖怎么配」。
- 在 `qa-api-runner` / `qa-ui-automation` 执行之前准备配置。

## 操作流程

### 步骤 1 — 生成配置模板

```bash
python scripts/init_env.py --outdir <变更>/06-execution/config --envs dev,test,staging
```
生成 `config/.env.example`（可提交）+ 各环境 `.env.<env>`（填真实值，勿提交）。

### 步骤 2 — 填写并隔离

- 真实值在 `.env.<env>` 中填写；把 `.env*` 加入 `.gitignore`，`.env.example` 留空模板入库。
- `qa-api-runner` 用 `--env-file config/.env.test` 指向当前环境；切换只改这一个参数。

### 步骤 3 — 依赖与鉴权

- 登录态：在 `.env` 填 `AUTH_TOKEN`，或由 `qa-api-runner` 的登录用例 `extract` 后注入后续请求。
- 接口依赖（前置接口、token 传递）由场景 JSON 的 `extract`/`${var}` 处理（见 `qa-api-runner`）。

## 规范（references/switching-guide.md）
- 配置集中在一个 `.env.<env>`，禁止散落代码/用例。
- 敏感信息只存本地 `.env`，不进仓库、不进聊天、不进报告明文。
- 环境切换 = 换 `--env-file`，不改动用例与脚本。

## 与上下游衔接
- 供 `qa-api-runner`、`qa-ui-automation` 运行时消费。
- 配合 `qa-test-data` 的基础数据准备。
- 上线/回归时在 `qa-release-check`（Phase 4）切换为生产预发环境校验。
