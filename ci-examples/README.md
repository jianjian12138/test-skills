# CI 门禁接入示例（RK-06）

本目录给出三套**真实接入** QA skills 套件的 CI 配置，不是通用占位。三套都按顺序跑了
套件自身的**三道闸 + 零依赖安全扫描**，任一非零退出即阻断合并：

| 文件 | 平台 | 关键步骤 |
|---|---|---|
| `.github/workflows/qa.yml` | GitHub Actions | `run_gates.py`（compileall → REGISTRY 派生 → check_drift(strict) → validate_portability → run_all_tests）→ scan_secrets |
| `.gitlab-ci.yml` | GitLab CI | 同上（gates + security 两 stage） |
| `Jenkinsfile` | Jenkins | 同上（Gates + Security 两 stage） |

## 统一门禁入口（R-02 硬化）

`tools/run_gates.py` 是**单一 CI 入口**，一条命令跑齐全部门禁并 fail-closed（任一非零即阻断）：

1. **compileall**：所有技能脚本纯标准库，先确保能编译（零第三方依赖）。
2. **REGISTRY 派生一致性**：重跑 `build_registry.py` 重建 `REGISTRY.json`，与已提交版做本质一致性比对
   （name/category/stage/tier/scripts/orchestrated，忽略日期），捕获「新增技能未进 REGISTRY / REGISTRY 静默脱管」。
3. **check_drift.py**（启用 `--require-verified --strict-meta`）：文档层 / 契约防漂移卡点 + R-02 硬化的
   两道可选严格闸（`--strict-meta` 要求每技能声明 `version`/`metadata.tier`，`--require-verified` 要求 T1 技能
   `verified_by` 非空）；并含 **S-02 SSOT 规则**（metadata↔REGISTRY 一致性）。
4. **validate_portability.py**：跨 agent 可移植性（name/description/license 齐全、零 `lib/` 引用、
   第三方 import 均经 `runtime_dependencies` 声明、零编译失败）。
5. **run_all_tests.py**：golden 自测，**覆盖异常路径 fail-closed**（损坏信号 / 时区戳 / 缺失新鲜度 /
   语义矛盾等），不是只看 happy-path。

> 安全扫描 `scan_secrets.py` 仍单独 stage 运行（零依赖自带扫描器，命中即写 blocking 信号并 `rc=1`）。

## 适配你自己的仓库

- 路径前缀 `.workbuddy/skills/` 是默认 WorkBuddy 技能目录；若你用 `--flavor claude`（`.claude/skills`）
  或 `--flavor generic`（`skills`），把前缀替换即可。
- 三道闸均**退出码即门禁**：CI 平台默认"非零即失败"，无需额外 `allow_failure`。
- 安全扫描的 `--path .` 扫描整个仓库；生产环境建议缩小到源码目录（如 `--path src`）。

> 来源：本目录是 `RK-06` 整改交付物，取代原先 `.tmp_test_phase4/ci_out/` 里的通用占位示例
> （flake8/pytest/semgrep，未接任何 qa-* 门禁）。
