# CI 发布门禁工作流（qa-gate）

把「数据驱动发布门禁」接入 CI，保证带 High 漏洞 + S2 缺陷 + SLA 不达标 **绝不会自动发布**。

## 阶段

```
1. 测试执行（qa-api-runner / qa-ui-automation / qa-perf-locust / qa-security-scan）
   → 产出 test-report.json / security_findings.json / perf 指标
2. 缺陷登记（qa-bug-report）→ bug_report.json
3. 追溯回写（qa-req-spec/update_trace.py）→ trace_matrix，覆盖率纳入门禁
4. 数据门禁（qa-release-check/gen_release_checklist.py --fail-on）
   → 消费 4 份产物，硬门禁，任一不过 sys.exit(1)
5. 契约校验（qa-api-contract/contract_diff.py --fail-on）→ 接口破坏性变更拦截
6. 质量闭合（qa-orchestrator/close_loop.py --strict）→ 未闭合 sys.exit(1)
```

## CI 配置要点（gen_ci.py 已生成 qa-gate job）

- 门禁步骤设为 `allow-failure: false`；非零退出码即中断流水线。
- 门禁产物（release_check.md / trace_matrix / contract_report）作为构建产物留存，供审计。
- 人工确认项（build_ok / rollback_plan）仍由人拍板，不与数据门禁混淆。

## 闭环三问（质量闭合判定）

| 问 | 含义 | 不过的后果 |
|---|---|---|
| 是谁 | 定位到具体失败/缺陷 | 视为未闭合 |
| 为什么 | 现象→根因因果链 | 判未闭合（归因缺失） |
| 可处置 | 高优缺陷有方案/负责人 | 阻断发布 |

> 范式来源：多 Skill 协作的测试助手（Leader + Skills，三层质量门：质疑→审查→闭合三问）。
