# WorkBuddy 全栈测试技能套件（QA Skills）

一套**轻量、可独立调用**的 QA 测试技能集合：覆盖「需求 → 分析 → 用例 → 数据/环境 → 接口文档 → 执行 → 报告/缺陷/发布 → 归档」完整生命周期，外加 11 项横切质量门禁与 2 个 Agent 测试专属技能。

**依赖分层（诚实声明）**：**治理/编排层（34 个方法学 + 编排技能）零第三方依赖，纯 Python 标准库即可运行**；**执行层 4 个技能需运行时依赖**（非标准库能力）：`qa-api-runner`(requests / mysql-connector / allure)、`qa-report` & `qa-test-case-gen`(openpyxl)、`qa-ui-automation`(playwright)。各技能 `runtime_dependencies` 字段声明其所需依赖，详见甲方交付手册 §8.1 的 `pip install` 清单。

> **依赖验证诚实边界（R-30）**：CI 的 `validate_portability` 仅做「声明 = 现实」的**静态**校验（扫描脚本顶层 import 与 `runtime_dependencies` 是否一致，未声明即 FAIL），**不实际安装、也不运行验证**所声明的第三方包。因此「声明了依赖」≠「目标环境已具备」——执行层 4 个技能（qa-api-runner / qa-report / qa-test-case-gen / qa-ui-automation）在落地环境须确保 requests/openpyxl/playwright 等**真实可用**（或走 `run_gates` 完整体检），否则运行期才会暴露缺包。

> 完整功能介绍、能力全景图、门禁接线、FAQ 见 [`SKILLS_DELIVERY.md`](../SKILLS_DELIVERY.md)（甲方交付手册）。
> 维护者命令（编译体检 / 自测 / 刷新注册中心 / 漂移校验 / 加新技能）见 [`MAINTAINERS.md`](MAINTAINERS.md)。

---

## 1. 三步上手（WorkBuddy 用户）

> `install.sh` / `install.ps1` 位于**仓库根目录**，源技能目录固定为 `<仓库根>/.workbuddy/skills`。
> 安装时请在**目标项目根目录**用路径调用本仓库的安装脚本（默认 flavor=workbuddy 装到 `./.workbuddy/skills`）。
> 注意：在 skills 仓库根目录直接 `./install.sh`（默认 flavor）会触发「源=目标」守卫而拒绝原地复制，须用 `--flavor claude/generic` 或 `--target` 指定别的目录。

```bash
# 在「目标项目」根目录执行，指向本 skills 仓库的 install.sh
/path/to/test-skills/install.sh                # 默认装到 ./.workbuddy/skills（workbuddy flavor）
#   Windows PowerShell 同理：
#   & "D:/path/to/test-skills/install.ps1"

# 2) 重新加载 WorkBuddy / 目标 agent（让平台扫描到 skills/）

# 3) 直接在对话里调用任意技能，例如：
#    「帮我做接口文档」        → qa-api-doc
#    「跑一轮接口自动化」      → qa-api-runner
#    「检查这次发布能否上线」  → qa-release-check
```

**不需要理解编排器，也不需要 CI**：每个技能就是一个 `SKILL.md`，你直接说需求，平台加载后执行。

---

## 2. 跨 Agent 安装（非 WorkBuddy 也行）

> 同样在「目标项目根目录」用路径调用 `install.sh`，并指定 flavor / target。

```bash
/path/to/test-skills/install.sh --flavor claude    # → ./.claude/skills   （Claude Code / Cursor 等）
/path/to/test-skills/install.sh --flavor generic   # → ./skills
/path/to/test-skills/install.sh --target /p/a/th   # 显式指定目标目录
```

内核（`SKILL.md` + 带版本脚本 + signals 契约）符合 Anthropic Agent Skills 开放标准，可在任意支持该标准的 agent 上加载；`qa-orchestrator` 编排层为可选，不装也能逐技能调用。

---

## 3. 分层采用（按需取用，不强制全装）

| 套餐 | 你得到什么 | 适合谁 |
|---|---|---|
| **Starter** | 复制你需要的单个/几个技能目录（`qa-api-runner`、`qa-a11y`…），直接调用 | 只想解决单点测试任务 |
| **Gates** | 在 Starter 基础上接入 `signals/` 契约 + `qa-release-check`，把质量门禁挂进 CI | 想给流水线加发布卡点 |
| **Full** | 再引入 `qa-orchestrator`，按 8 阶段生命周期路由整轮变更 | 想标准化「从需求到归档」全过程 |

> **关键事实**：38 个传统 QA 技能**全部可独立使用**，彼此不耦合。市面上的 skills 也是"装上一堆、按需调用"，本套件在易用性上**并不更复杂**——只是额外提供了可选编排与门禁能力。

---

## 4. 技能分布（40 个）

- **38 个传统 QA 技能**：8 阶段生命周期（需求/分析/用例/数据环境/接口文档/执行/报告缺陷发布/归档）+ 11 项横切门禁（风险/策略/CI/变异/flaky/无障碍/视觉回归/单测-TDD/混沌/代码评审/合成监控）。
- **2 个 Agent 测试专属技能**（不接入 8 阶段路由）：`qa-agent-eval`（能力评测）、`qa-agent-security`（红队评测）。
- **编排入口**（可选）：`qa-orchestrator`。

---

## 5. 几个能直接跑的命令（已校验参数）

```bash
# 接口文档：拉 Swagger → 落盘 Markdown + JSON
python qa-api-doc/scripts/swagger_fetch.py --url https://api.example.com/openapi.json \
       --output 05-api/api-doc.md --save-json 05-api/api-doc.json

# 接口执行：跑场景，产物写入目录
python qa-api-runner/scripts/run.py --scenario 06-execution/scenario.json --outdir 06-execution

# 无障碍门禁：写 signals/qa-a11y.json，有 A 级违规则 exit 1
python qa-a11y/scripts/a11y_check.py --in web/ --signals-dir signals --fail-on

# 单元/TDD 健康度门禁
python qa-unit-tdd/scripts/unit_health.py --metrics metrics.json --signals-dir signals --fail-on

# 发布门禁：扫 signals/，任一 blocking 即 exit 1
python qa-release-check/scripts/gen_release_checklist.py \
       --release release.json --signals-dir signals --out release-checklist.md --fail-on
```

> 各质量技能写入 `signals/<skill>.json`，`qa-release-check` 聚合任一 `blocking=true` 即阻断。新增质量维度只需该技能按 schema 写信号，门禁零改。完整命令见交付手册 §11–§12。

---

## 6. 诚实边界（摘要）

- `qa-a11y` 仅 WCAG 2.1 **A 级静态检查**；不做对比度/键盘可达性实测。
- `qa-visual-regression` 对比 **DOM + 关键视觉属性**，不做像素级图像 diff。
- `qa-chaos` / `qa-synthetic-monitoring` / `qa-code-review` 均为**规格治理门禁**：仅校验规格完整性，**不实际注入故障 / 不探测生产 / 不解析 AST**，与 `qa-security-scan`（ZAP/Semgrep）互补。
- 全部脚本为确定性逻辑，**不涉及模型推理**；AI 能力来自宿主平台加载 `SKILL.md` 后的规划执行。

---

## 7. 许可

MIT —— 见 [`LICENSE`](../../LICENSE)。
