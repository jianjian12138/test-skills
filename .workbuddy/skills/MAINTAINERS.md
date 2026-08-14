# 维护者指南（Maintainers）

本文档从交付手册 §14 抽出，面向**套件维护者 / 接手者**。普通使用者无需阅读，直接看 `README.md`。

> 所有命令在仓库根目录（`<repo>`）或 `skills/` 目录执行均可，路径按实际位置调整。
> 解释器：`python3`（Python 3.10+，编排/论证层纯标准库、零第三方依赖；执行层按需运行时依赖，见各技能 `runtime_dependencies`）。

---

## 1. 日常体检命令

| 任务 | 命令 |
|---|---|
| 全量脚本编译体检 | `python -m compileall .workbuddy/skills` |
| 跑全部 golden 自测 | `python .workbuddy/skills/tests/run_all_tests.py` |
| 刷新注册中心 | `python .workbuddy/skills/build_registry.py` |
| 渲染路由表 | `python .workbuddy/skills/qa-orchestrator/scripts/render_stages.py` |
| 漂移一致性校验（CI 卡点） | `python .workbuddy/skills/qa-orchestrator/scripts/check_drift.py` |
| 生成依赖图 | `python .workbuddy/skills/tools/gen_deps.py` |

> **单一事实源**：`stages.json` 是编排唯一事实源；`REGISTRY.json` 是技能注册中心。二者与 `SKILL.md` 路由表须一致，`check_drift.py` 为其卡点。

---

## 2. 公共代码约定

每个带脚本的方法学技能在 `scripts/_common.py` **自包含**一份公共库（`emit_signal` / `load_json` / `save_json` / `read_text` / `wilson_ci` / `two_prop_z`）。这是刻意的 vendoring：**不使用跨目录 `lib/` 包**，以保证每个技能目录可单目录分解、可独立分发（符合 Anthropic Agent Skills 单目录可分解性）。

> 早期版本曾用 `lib/common.py` 共享包，已于 V6 升级移除——若看到对 `lib/common.py` 的引用，均为过时文档。

---

## 3. 质量信号契约

- 质量技能写 `signals/<skill>.json`，结构见 `references/signal-schema.md`。
- 门禁唯一权威：**任一 `blocking=true` 即阻断**（`qa-release-check` → `sys.exit(1)`）。
- 新增质量维度：让新技能按 schema 写信号即可，门禁零改动。

---

## 4. 如何新增一个技能

1. 新建 `qa-xxx/SKILL.md`（含 `name` / `description` / `license: MIT`；**不要写** `agent_created` 等非标准 frontmatter 字段）。
2. 如需脚本：建 `qa-xxx/scripts/xxx.py`，复用 `scripts/_common.py` 的 `emit_signal`。
3. 若接编排：在 `stages.json` 的对应阶段 `skills` / `alternates`，或 `cross_cutting` 数组追加。
4. 刷新并校验：`python build_registry.py && python qa-orchestrator/scripts/check_drift.py`。
5. 补 `tests/run_all_tests.py` 里的 golden 用例（阻断/放行双场景）。

---

## 5. 发布 / 分发

```bash
# 跨 agent 安装
./install.sh                       # 默认 → ./.workbuddy/skills
./install.sh --flavor claude        # → ./.claude/skills
./install.sh --flavor generic       # → ./skills
./install.sh --target /p/a/th

# 整包 zip 分发（install.sh 已自动剔除维护工具与缓存）
```

`install.sh` / `install.ps1` 装后自动清理 `__pycache__`、`build_registry.py`、`REGISTRY.json`、`check_drift.py`、`tools/`，保持分发包干净。
