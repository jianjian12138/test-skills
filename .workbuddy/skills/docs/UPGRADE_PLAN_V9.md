> ⚠️ **本文已被取代（仅供历史参考）**：V9 升级计划已由仓库根目录 [`UPGRADE_PLAN_V10.md`](../../UPGRADE_PLAN_V10.md)（V10 最终收口版）取代。当前验收以根版为准。

# WorkBuddy 测试技能套件 · V9 升级计划（验收整改交付版 · 已取代）

> 依据：`reviews/expert_review_2026-08-11/CONSOLIDATED_EXPERT_REVIEW.md`（四专家联合面板 **7.9/10**，裁定 **4×P0 + 9×P1**）
> 目标：分阶段**清零全部 P0（4 项）+ 全部 P1（9 项）**，非最小改动
> 系统根：`D:/test-skills/.workbuddy/skills/`（40 技能：38 传统 + 2 Agent 测试）
> 本计划逐阶段落地并经三道 CI 闸验证；本文是交付归档版（执行细节见 `C:\Users\Administrator\.workbuddy\plans\stellar-cascade-babbage.md`）

---

## 0. 三道 CI 闸（任何改动后必须仍全绿）

| 闸 | 命令 | 现状 |
|---|---|---|
| 1. golden 自测 | `python tests/run_all_tests.py` | **64/64 PASS** |
| 2. 漂移守卫 | `python qa-orchestrator/scripts/check_drift.py` | **rc=0（无漂移）** |
| 3. 可移植性 | `python tools/validate_portability.py` | **40 技能 / 72 脚本 PASS** |

复闸标准套（每阶段结束执行）：
```bash
PY="C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe"
ROOT="D:/test-skills/.workbuddy/skills"
"$PY" -m compileall -q "$ROOT"
"$PY" "$ROOT/tests/run_all_tests.py"
"$PY" "$ROOT/qa-orchestrator/scripts/check_drift.py"
"$PY" "$ROOT/tools/validate_portability.py"
echo "EXIT=$?"   # 三者均 0 方为通过
```

---

## 1. 六阶段总览与退出标志

| 阶段 | 清零项 | 退出标志（三道闸全绿 + 附加） | 状态 |
|---|---|---|---|
| **Phase 1** | P0-A, P0-B | route_next 超步 BLOCKED；close_loop 缺证据未闭合；golden 3 例 | ✅ |
| **Phase 2** | P0-C, P0-D | 多轮/间接注入 fixture 通过；calc_asr 拒 stub（exit 2） | ✅ |
| **Phase 3** | P1-2, P1-5 | grep 无"无需 pip"残留；signal-schema 语义 if-then + drift 13b | ✅ |
| **Phase 4** | P1-1, P1-4, P1-6 | T1 全填 verified_by；emit_signal 19 处字节一致；两 agent 写信号 | ✅ |
| **Phase 5** | P1-3, P1-7, P1-8 | 生成器行为测试；空 checker fail-closed；指标含置信带 | ✅ |
| **Phase 6** | P1-9 + 收尾 | route_next 含 cross_cutting_recommend；发布 V9 文档 + 复评 V12 | ✅ |

---

## 2. 各阶段关键落地（file:line + golden 用例）

### Phase 1 — P0-A 编排终止 + P0-B 闭合 fail-closed
- **P0-A**：`qa-orchestrator/scripts/_stages.py` 新增 `bump_step`/`ORCH_STATE_FILE` 状态机（防死循环）；`route_next.py` 注入 `max_steps_exceeded` BLOCKED + `artifact_mismatch` 诊断（治黑洞）；`check_drift.py` 规则 13（产物契约一致性）。
- **P0-B**：`close_loop.py:evaluate_closure` 顶部证据存在性硬闸——缺 test-report/bug_report/security_findings 且 `qa_required=true` → `closed=False` + `no_quality_evidence` blocker。
- golden：`t_route_max_steps` / `t_close_no_evidence` / `t_route_artifact_mismatch`。

### Phase 2 — P0-C 红队多轮 harness + P0-D stub 防呆
- **P0-C**：`qa-agent-security/scripts/run_attacks.py` 重写为多轮对话循环 + 工具运行时，间接注入真正进入 `tool_results`（`injection_target.channel=tool_result`）。
- **P0-D**：`calc_asr.py` 增 stub 闸门（note/source==stub → exit 2 阻断；`--allow-stub` 仍告警且 level=STUB_UNRATED）。
- golden：`t_run_attacks_multiturn` / `t_asr_stub_rejected` / `t_asr_stub_allow_warn`。

### Phase 3 — P1-2 文档"零依赖"清零 + P1-5 契约语义
- **P1-2**：`README.md` / `SKILLS_DELIVERY.md` 改为分层声明（治理/编排层零依赖；执行层 4 技能需运行时依赖，附 §8.1 pip 清单）；`grep` 残留已清零。
- **P1-5**：`references/signal-schema.md` 明确"blocking 是唯一阻断权威"；`signal-schema.json` 加 `blocking→severity` if-then；`check_drift.py` 规则 13b 语义校验。
- golden：`t_signal_schema_semantic`。

### Phase 4 — P1-1 信任证据 + P1-4 信号 SSOT + P1-6 agent 接入
- **P1-1**：`build_registry.py` 回填 verified_by（38 T1 填 `ci:run_all_tests`+日期，2 纯文档标 `pending`）；`check_drift.py` 可选 `--require-verified`。
- **P1-4**：`tools/gen_common.py` 统一生成全仓 `emit_signal`（19 处字节一致）；`check_drift.py` 规则 9 升级校验全部定义。
- **P1-6**：`calc_metrics.py`/`calc_asr.py` 内置字节一致 `emit_signal` 写 `signals/*.json`（阈值触发阻断）；`stages.json` `agent_testing.emits_signals=true`；release-check 通用消费已端到端验证（agent 阻断信号 → exit 1）。
- golden：`t_emit_signal_ssot` / `t_agent_eval_emits_signal` / `t_agent_security_emits_signal`。

### Phase 5 — P1-3 生成器测试 + P1-7 checkers 强制 + P1-8 指标置信带
- **P1-3**：`tests/run_all_tests.py:t_generator_minimal_behavior` 对 10 个生成器做最小行为断言（不再仅 py_compile）。
- **P1-7**：`gen_task.py:autogen_checkers` 默认 rubric 不再全空（抽 required_substrings/tool_sequence + `checkers_autogen` 标注）；`grade_run.py` 空 checkers → `rc=2` fail-closed（`--no-require-checkers` 退回自报并告警）。
- **P1-8**：`calc_metrics.py` 加 `bootstrap_ci`（B=2000 有放回、seed 可复现）+ 任务级 mean/std + `dims_std` + `small_sample_warn`（n_tasks<8）。
- golden：`t_generator_minimal_behavior` / `t_grade_empty_checkers_failclosed` / `t_gen_task_autogen_checkers` / `t_calc_metrics_confidence`。

### Phase 6 — P1-9 横切调度 + 收尾
- **P1-9**：`_stages.py` 新增 `CROSS_CUTTING_TRIGGERS`（按文件后缀/名/关键词/完成阶段数触发）+ `recommend_cross_cutting`；`route_next.py` 6 个 result 分支注入 `cross_cutting_recommend`（JSON 必含，--auto 保持只输出主技能名）；`close_loop.py` 增 `cross_cutting` 追踪状态 + 顶层 `cross_cutting_hint` + `--mark-cross` 记录 + `--strict-cross`（opt-in 门禁）。
- 收尾：本文 `docs/UPGRADE_PLAN_V9.md` + `reviews/CONSOLIDATED_REVIEW_V12.md`（自评 ≤ 面板 7.9+0.3=8.2）；`SKILLS_DELIVERY.md` 升 V9、自测数 64/64、verified_by 回填说明。
- golden：`t_route_cross_cutting_recommend` / `t_close_cross_cutting_tracker`。

---

## 3. 关键纪律（不假绿）

- **全部修复 fail-closed 默认**：P0-B 缺证据→未闭合；P0-D stub→拒评；P1-7 空 checker→不自动 PASS；P1-1 未验证→非空但标 pending。
- **golden 不得为过而改预期**：P0-D 导致 agent-security 用例改用真实 fixture 或显式 `--allow-stub` 断言"被拒"。
- **check_drift 是防回归主力**：P0-A 产物契约、P1-4 19 处一致、P1-5 语义、P1-6 agent 信号声明均落入 drift 新规则。
- **复评 meta 上限**：CONSOLIDATED_REVIEW_V12 自评 ≤ 8.2，杜绝自评虚高（评审 §八 已指出自评 9.4 高于专家 7.9）。

---

## 4. Owner / 时间线

| 项 | 内容 |
|---|---|
| 计划制定 | 四专家评审 → V9 6 阶段计划（2026-08-11） |
| 执行 | 单人在本会话内逐阶段闭环（Phase 1 → 6） |
| 验证 | 三道闸全程复跑：compileall OK / 64/64 / drift 0 / portability 40/72 |
| 交付物 | `docs/UPGRADE_PLAN_V9.md`、`reviews/CONSOLIDATED_REVIEW_V12.md`、`SKILLS_DELIVERY.md`(V9) |
| 后续建议 | 甲方独立验收复评；tier-1 人工冒烟；阈值按 SLA 调参；分发评估 MCP/ skills add |
