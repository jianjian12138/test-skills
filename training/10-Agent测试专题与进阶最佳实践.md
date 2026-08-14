# 第 10 篇：Agent 测试专题 + 进阶与最佳实践

> 本篇目标：讲清两个**不接入 8 阶段路由**的特殊技能——`qa-agent-eval`（评测 AI Agent 能力）和 `qa-agent-security`（Agent 红队评测）；再补充进阶机制（Run 对象、断点续推）和一套给小白的最佳实践清单。

---

## 10.1 为什么 Agent 测试是独立专题？

普通测试测的是「业务系统」（一个网站、一个 API）。而这两技能测的是 **「AI Agent 本身」**——它会不会答错、会不会被骗子 prompt 骗走数据、规划能力稳不稳。

> 关键区分：**被测对象是 Agent，不是业务系统**。所以它们不进 8 阶段路由，单独成类（REGISTRY 里 `category=agent`）。

---

## 10.2 `qa-agent-eval`：Agent 能力评测

### 它度量什么

| 维度 | 说明 |
|---|---|
| 任务完成率 | `Pass@1` / `Pass@k`（注意字段名 `pass_at_1_macro`，避免与无偏 Pass@1 混淆） |
| 工具调用准确率 | Agent 调对工具/参数的比例 |
| 五维评分卡 | 规划 / 记忆 / 可靠性等（缺数据维度显式标 `na`，不假装算） |
| 轨迹（trace）崩溃分析 | 导入真实轨迹（agentdojo 等），识别长程崩溃模式 |

### 怎么用

1. `gen_task.py`：设计并生成**自包含评测任务目录**（含隐藏 rubric 判分标准）；
2. 跑被测 Agent，收集轨迹；
3. `calc_metrics.py` / `grade_run.py` / `grade_trace.py` / `scorecard.py`：算指标、判分、出评分卡。

> 统计严谨性：指标带 **Wilson 95% 置信区间**，不会拿一个点估计吹「准确率 100%」。这是专业做法，避免误判。

---

## 10.3 `qa-agent-security`：Agent 红队评测

### 双轴判定（不要只看一个）

| 轴 | 含义 |
|---|---|
| **ASR（攻击成功率）** | 红队攻击得手的比例 |
| **效用保持率** | 被攻击后 Agent 还能正常干活的比例（夹在 [0,1]，不会 >1） |

只看 ASR 会误判——有些防御是「宁可变傻也不被骗」，效用掉了也不行。双轴才公正。

### 9 大攻击面

`injection_direct`（直接注入）、`injection_indirect`（间接注入）、`overreach`（越权）、`exfil`（数据泄露）、`long_context_crash`（长上下文崩溃）、`tool_abuse`（工具滥用）、`sandbox_escape`（沙箱逃逸）、`multi_turn_induction`（多轮诱导）、`bias`（偏见）。

### 危害定级

行动危害按 **L0–L6** 分级；`SURFACE_DEFAULT_HARM` 严格对齐上面 9 个真实攻击面。当危害靠推断得出时，会显式告警「可能与真实危害存在偏差（高估或低估）」——**不假装精确**。

```bash
# 生成攻击集 → 跑攻击 → 判攻 → 算 ASR
python .workbuddy/skills/qa-agent-security/scripts/gen_attacks.py ...
python .workbuddy/skills/qa-agent-security/scripts/run_attacks.py ...
python .workbuddy/skills/qa-agent-security/scripts/judge_attack.py ...
python .workbuddy/skills/qa-agent-security/scripts/calc_asr.py ...
```

---

## 10.4 进阶机制：Run 对象与断点续推

### Run 对象（W3）

把「一次测试 / 一次变更推进」建模为 **Run**（`run_object.py`）：承载 run_id、模型/Prompt/工具版本、超时、配置覆盖，支持 `cancel` / `retry` / `apply_config_override` / `replay`，所有动作记入 `history`（确定性、可审计）。

> 企业架构原则：**协议层（MCP/CLI/API）不能代替运行架构**——超时、取消、重试、重放发生在 Run 层。

### ⚠️ replay ≠ 重跑

`replay` 只把 Run 状态标为 `replayed`（记录事件流可按序还原），**不重新触发底层执行**。真要重跑，用 `retry`（标记阶段待重做）或重新发起一次新 Run。别把「重放记录」当成「重新测了一遍」。

### 断点续推（A-01）

见 [第 3 篇](03-第一次跑通一条测试.md) 的 `checkpoint.py`：`--resume` 只**打印**下一步，**不自动执行**，须人或 agent 显式确认后再调对应技能——这是半自动契约，防止编排器擅自替你做决定。

---

## 10.5 小白最佳实践清单

1. **从 Starter 用起**：先装 1–2 个需要的技能，别一上来全装 40 个。
2. **需求先规范再分析**：`qa-req-spec` → `qa-test-analysis`，别跳过直接写用例。
3. **用例必覆盖正/负/边界**：只测正向 = 上线翻车。
4. **信任 signals，但理解边界**：门禁用 `signals/blocking` 卡发布（fail-closed）；治理型门禁只校验规格，真实注入/扫描靠专业工具。
5. **执行层依赖要真实可用**：`qa-api-runner`(requests/mysql/allure)、`qa-report`&`qa-test-case-gen`(openpyxl)、`qa-ui-automation`(playwright) 在目标环境要确保 pip 包到位。
6. **别在 skills 仓库根裸跑 `./install.sh`**：会触发源=目标守卫，用 `--flavor generic` 或 `--target` 指到别处。
7. **产物落盘、按变更归集**：用编排器建 `changes/<slug>/` 工作区，让一轮测试可追溯；最后 `qa-archive` 归档。
8. **诚实看待验证状态**：留意 `verified_by=pending` 的技能（方法学/知识库类），使用前心里有数。

---

## 10.6 常见误区 FAQ

| 问题 | 答案 |
|---|---|
| 装了 `qa-chaos` 就等于能做混沌工程？ | 否。它只校验混沌实验「是否受治理」（有稳态假设/回退），不实际注入故障。真注入接 Chaos Mesh。 |
| `qa-a11y` 过了就等于无障碍达标？ | 仅 WCAG 2.1 A 级静态检查，不含对比度/键盘实测。深度检测接 axe-core/pa11y。 |
| 治理层零依赖，执行层也不用装包？ | 执行层 4 个技能需 requests/openpyxl/playwright，落地环境必须真实可用。 |
| `replay` 是重新跑测试吗？ | 不是。它只还原事件流记录，不触发执行；重跑用 `retry` 或新 Run。 |
| 40 个技能必须全用？ | 不必。38 个传统技能（含编排器）彼此独立，2 个 Agent 测试技能按需取用。 |

---

## 10.7 到这里，你已经能上手了

回顾 10 篇路线：
1. [认识套件](01-认识测试技能套件.md) → 2. [安装](02-安装与环境准备.md) → 3. [最小闭环](03-第一次跑通一条测试.md)
4. [需求分析](04-需求与测试分析.md) → 5. [用例数据](05-用例与测试数据.md) → 6. [接口测试](06-接口测试全流程.md)
7. [执行类型](07-执行阶段的多种测试类型.md) → 8. [报告归档](08-报告缺陷发布与归档.md) → 9. [门禁CI](09-横切质量门禁与CI集成.md) → 10. [Agent专题+最佳实践](10-Agent测试专题与进阶最佳实践.md)（本篇）

**想要更权威的细节**（功能全集、门禁接线、FAQ 全量、维护者命令），去看仓库里的：
- `SKILLS_DELIVERY.md` —— 甲方交付手册（功能介绍/能力全景/门禁接线/FAQ）
- `.workbuddy/skills/MAINTAINERS.md` —— 维护者命令（编译体检/自测/刷新注册中心/漂移校验/加新技能）
- 每个技能的 `SKILL.md` 与 `references/` —— 具体参数与用法

祝测试顺利。记住一句话：**先规范、全覆盖、信门禁、明边界**——这就是这套套件的设计哲学。
