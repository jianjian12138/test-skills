# qa-orchestrator 使用指南（检查项 / 阈值 / CLI / 常见坑）

> 本技能是**半自动** QA 测试全生命周期编排脚手架：负责把「需求 → 分析 → 用例 → 数据/环境
> → 接口文档 → 执行(API/UI/性能/安全/探索/兼容/移动) → 报告 → 缺陷 → 发布 → 归档」8 阶段
> 串成可追踪的变更工作流。**它不实现具体分析/执行逻辑**，只做路由与落盘。

## 1. 核心脚本与 CLI

| 脚本 | 作用 | 常用参数 |
|---|---|---|
| `scripts/route_next.py` | 按 `stages.json` 路由下一阶段技能（含 W7 领域插槽合并） | `--change <slug>`、`--json` |
| `scripts/route_agent.py` | 独立路由 Agent 测试类技能（能力评测/红队） | `--json` |
| `scripts/close_loop.py` | 一键推进变更到归档，更新看板 | `--change <slug>`、`--apply` |
| `scripts/checkpoint.py` | 断点续推（checkpoint/resume）+ 轻量重试（A-01） | `--change <dir> --stage <d> --status done`、`--resume`、`--list` |
| `scripts/run_object.py` | Run 对象生命周期（W3：cancel/retry/override/replay） | `--new`、`--run-json <f> --cancel/--retry/--override/--replay` |
| `scripts/render_stages.py` | 渲染路由表 / 依赖图 | 无 |

## 2. 关键阈值与契约

- **编排层零第三方依赖**：`route_next/close_loop/render_stages` 仅用 Python 标准库；
  执行类阶段（性能/安全/UI 等）的第三方依赖在各自技能 frontmatter `runtime_dependencies`
  显式声明，编排器不 import 它们。
- **Agent 测试类不接入 8 阶段路由**：`qa-agent-eval` / `qa-agent-security` 经
  `route_agent.py` 与 `stages.json.agent_testing` 独立维路由，避免污染产品生命周期。
- **信号契约**：质量类技能写 `signals/<skill>.json`，结构见 `references/signal-schema.md`
  （SSOT = `scripts/_common.py:emit_signal`）。门禁唯一权威：**任一 `blocking=true` 即阻断**
  （`qa-release-check` → `sys.exit(1)`）。

## 3. 常见坑

1. **执行阶段需要被测环境就绪**：route_next 只告诉你"下一步该跑哪个技能"，不会替你起服务 /
   造数据。环境没好就跑执行类技能会失败——这是设计使然，不是编排 bug。
2. **人工确认不可跳过**：发布/归档等阶段的最终判定需人工确认，编排器不臆造执行结果。
3. **`--apply` 才落盘**：`close_loop.py` 不加 `--apply` 只打印待办，不会改动看板。
4. **漂移卡点**：改动 `stages.json` / `SKILL.md` 路由表后，务必跑
   `python qa-orchestrator/scripts/check_drift.py`，任一清单不一致即 `exit 1`。

## 4. 快速自检

```bash
python .workbuddy/skills/qa-orchestrator/scripts/check_drift.py   # 无漂移 = exit 0
python .workbuddy/skills/tests/run_all_tests.py                    # 全量 golden 自测
```
