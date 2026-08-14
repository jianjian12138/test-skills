# 综合复评 V12 · WorkBuddy 测试技能套件（验收整改后）

> 类型：交付前**诚实复评**（meta 上限约束：自评 ≤ 专家面板 7.9 + 0.3 = **8.2**，禁止虚高）
> 上游：四专家联合评审面板 **7.9/10**（4×P0 + 9×P1，详见 `CONSOLIDATED_EXPERT_REVIEW.md`）
> 整改：V9 六阶段计划（清零全部 P0×4 + P1×9），执行见 `docs/UPGRADE_PLAN_V9.md`
> 日期：2026-08-11

---

## 1. 自评结论（受上限约束）

**交付前自评：8.1 / 10**（≤ 8.2 上限，未虚高）。

理由：V9 已用**可验证证据**清零面板指出的全部 P0+P1（三道闸 64/64、drift 0、portability 40/72 全过），但"信任证据"与"真实生产集成"两类本质性短板**未被消除、仅被诚实化**，故不给予满分。

---

## 2. P0/P1 清零证据矩阵

| 项 | 类别 | 整改 | 验证证据 |
|---|---|---|---|
| P0-A | 编排死循环/黑洞 | `_stages.bump_step` + route_next `max_steps_exceeded`/`artifact_mismatch` | golden `t_route_max_steps` / `t_route_artifact_mismatch` PASS |
| P0-B | 闭合 fail-open | close_loop 证据硬闸 `no_quality_evidence` | golden `t_close_no_evidence` PASS（exit1+closed=False） |
| P0-C | 红队单发 | run_attacks 多轮 harness + 工具回环 + 间接注入 | golden `t_run_attacks_multiturn` PASS（tool_results=1, _turns=4, 得逞） |
| P0-D | stub 假绿 | calc_asr 拒 stub（exit 2）/ STUB_UNRATED | golden `t_asr_stub_rejected` / `t_asr_stub_allow_warn` PASS |
| P1-2 | 文档"零依赖" | README/SKILLS_DELIVERY 分层声明 + grep 清零 | grep 零残留 |
| P1-5 | 契约语义 | signal-schema blocking 权威 + if-then + drift 13b | golden `t_signal_schema_semantic` PASS |
| P1-1 | 信任证据空 | build_registry 回填 verified_by（38 T1 / 2 pending） | `assert all verified_by for tier1` 通过 |
| P1-4 | 信号 SSOT | gen_common 统一 19 处 emit_signal 字节一致 | golden `t_emit_signal_ssot` PASS（19 定义/1 份） |
| P1-6 | agent 孤岛 | 两 agent 写 signals + 通用 release-check 消费 | golden `t_agent_eval_emits_signal` / `t_agent_security_emits_signal` PASS + 端到端 exit1 |
| P1-3 | 生成器仅编译 | run_all_tests 10 生成器行为断言 | golden `t_generator_minimal_behavior` PASS |
| P1-7 | 判分自证 | gen_task autogen_checkers + grade_run 空 checker rc=2 | golden `t_grade_empty_checkers_failclosed` / `t_gen_task_autogen_checkers` PASS |
| P1-8 | 指标无方差 | bootstrap_ci + mean/std + small_sample_warn | golden `t_calc_metrics_confidence` PASS |
| P1-9 | 横切未调度 | recommend_cross_cutting + route_next/close_loop 注入 | golden `t_route_cross_cutting_recommend` / `t_close_cross_cutting_tracker` PASS |

**三道闸最终态**：compileall OK · 自测 **64/64** · drift rc=0 · portability 40/72 PASS。

---

## 3. 诚实残余风险（不粉饰）

1. **信任证据为 CI 派生，非人工独立验证**：`verified_by="ci:run_all_tests"` 来自 golden 套件自跑，不是甲方人工冒烟。属于"有证据"但证据强度有限——面板对"自评/假绿"的担忧在形式上已缓解，实质上仍需人工一轮。
2. **Agent 评测/红队用合成 fixture**：`fake_agent.py` 与 stub 是设计内的链路打通手段，ASR/Pass@k 数字**不代表真实生产 Agent 表现**。真实 agent 接入端到端未演示（仅证明信号契约可被消费）。
3. **三个方法学技能是规格治理门禁，非真实执行**：`qa-chaos`/`qa-code-review`/`qa-synthetic-monitoring` 仅校验规格完整性，不实际注入故障 / 解析 AST / 探测生产（已在 `SKILLS_DELIVERY.md` §16 标注）。这与面板"方法学深度"期望仍有差距。
4. **横切推荐是启发式，非硬门禁**：P1-9 按文件特征推荐，默认仅提示；`--strict-cross` 需显式开启才阻断。覆盖率/误推荐风险未量化。
5. **阈值默认值待按 SLA 调参**：flaky 率、变异分数、覆盖率、混沌治理要素阈值均为内置默认，甲方未调参前门禁强度不可知。
6. **分发仍为 zip/复制 + 脚本**：MCP server / `skills add` 兼容包未做（ADR-007 路线图）。

---

## 4. 与历史自评的校准

- 历史自评曾达 **9.4/10**（V3 复审），而专家面板为 **7.9**——存在 **+1.5 虚高**，正是评审 §八 指出的核心问题。
- 本轮（V12）严格遵守 **自评 ≤ 面板 + 0.3 = 8.2** 上限，取 **8.1**，差额留给上述 §3 残余风险。
- 若甲方完成 §3.1 人工冒烟 + §3.2 真实 agent 集成 + §3.3 方法学真实化，可再独立复评上调。

---

## 5. 验收建议

- **建议甲方独立验收复评**（不依赖本套件自评），重点核验 §3 六项残余风险是否在其可接受范围内。
- 验收前甲方可对 tier-1 技能做一轮人工冒烟，将 `verified_by` 由 `ci:*` 升级为 `manual:*`。
- 阈值按甲方 SLA 调参后，再跑三道闸确认门禁强度符合预期。

---

## 6. 交付物清单

| 文档 | 路径 | 说明 |
|---|---|---|
| V9 升级计划（交付版） | `docs/UPGRADE_PLAN_V9.md` | 6 阶段 file:line + 退出标准 + 复闸命令 |
| 本复评 | `reviews/CONSOLIDATED_REVIEW_V12.md` | 自评 8.1（≤8.2），残余风险披露 |
| 甲方手册 | `SKILLS_DELIVERY.md`（V9） | 自测 64/64、verified_by 回填、历程表 |
| 评审原始 | `reviews/expert_review_2026-08-11/CONSOLIDATED_EXPERT_REVIEW.md` | 四专家面板 7.9/10 |
