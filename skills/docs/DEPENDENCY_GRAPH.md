# 技能依赖图（由 stages.json 自动生成）

> 阶段纵向串联，主技能 + 备选技能隶属各阶段；横切关注点以虚线贯穿全程。

```mermaid
flowchart TD
    01["需求结构化"]
    01_qa_req_spec["qa-req-spec"]
    01 --> 01_qa_req_spec
    02["需求分析 + 测试点"]
    02_qa_test_analysis["qa-test-analysis"]
    02 --> 02_qa_test_analysis
    01 --> 02
    03["测试用例设计"]
    03_qa_test_case_gen["qa-test-case-gen"]
    03 --> 03_qa_test_case_gen
    02 --> 03
    04["测试数据 + 环境"]
    04_qa_test_data["qa-test-data"]
    04 --> 04_qa_test_data
    04_qa_env_config["qa-env-config"]
    04 --> 04_qa_env_config
    03 --> 04
    05["接口文档"]
    05_qa_api_doc["qa-api-doc"]
    05 --> 05_qa_api_doc
    04 --> 05
    06["执行（接口/UI/性能/安全/探索/兼容）"]
    06_qa_api_runner["qa-api-runner"]
    06 --> 06_qa_api_runner
    06_qa_ui_automation["qa-ui-automation"]
    06 --> 06_qa_ui_automation
    06_qa_perf_locust["qa-perf-locust"]
    06 --> 06_qa_perf_locust
    06_qa_perf_jmeter["qa-perf-jmeter"]
    06 --> 06_qa_perf_jmeter
    06_qa_security_scan["qa-security-scan"]
    06 --> 06_qa_security_scan
    06_qa_exploratory["qa-exploratory"]
    06 --> 06_qa_exploratory
    06_qa_compat_matrix["qa-compat-matrix"]
    06 --> 06_qa_compat_matrix
    06_qa_api_contract["qa-api-contract"]
    06 --> 06_qa_api_contract
    06_qa_mobile_autotest["qa-mobile-autotest"]
    06 --> 06_qa_mobile_autotest
    06_qa_perf_design["qa-perf-design"]
    06 --> 06_qa_perf_design
    06_qa_ui_testid["qa-ui-testid"]
    06 --> 06_qa_ui_testid
    06_qa_ui_kb["qa-ui-kb"]
    06 --> 06_qa_ui_kb
    06_qa_execution["qa-execution"]
    06 --> 06_qa_execution
    05 --> 06
    07["报告 + 缺陷 + 上线"]
    07_qa_report["qa-report"]
    07 --> 07_qa_report
    07_qa_perf_analysis["qa-perf-analysis"]
    07 --> 07_qa_perf_analysis
    07_qa_security_report["qa-security-report"]
    07 --> 07_qa_security_report
    07_qa_bug_report["qa-bug-report"]
    07 --> 07_qa_bug_report
    07_qa_bug_verify["qa-bug-verify"]
    07 --> 07_qa_bug_verify
    07_qa_release_check["qa-release-check"]
    07 --> 07_qa_release_check
    06 --> 07
    08["归档 + CI + 策略"]
    08_qa_archive["qa-archive"]
    08 --> 08_qa_archive
    07 --> 08
    CC_qa_risk_based["qa-risk-based<br/>· 横切门禁"]
    CC_qa_test_strategy["qa-test-strategy<br/>· 横切门禁"]
    CC_qa_ci["qa-ci<br/>· 横切门禁"]
    CC_qa_mutation["qa-mutation<br/>· 横切门禁"]
    CC_qa_flaky_detect["qa-flaky-detect<br/>· 横切门禁"]
    CC_qa_a11y["qa-a11y<br/>· 横切门禁"]
    CC_qa_visual_regression["qa-visual-regression<br/>· 横切门禁"]
    CC_qa_unit_tdd["qa-unit-tdd<br/>· 横切门禁"]
    CC_qa_chaos["qa-chaos<br/>· 横切门禁"]
    CC_qa_code_review["qa-code-review<br/>· 横切门禁"]
    CC_qa_synthetic_monitoring["qa-synthetic-monitoring<br/>· 横切门禁"]
    CC_qa_risk_based -.-> 01
    CC_qa_risk_based -.-> 02
    CC_qa_risk_based -.-> 03
    CC_qa_risk_based -.-> 04
    CC_qa_risk_based -.-> 05
    CC_qa_risk_based -.-> 06
    CC_qa_risk_based -.-> 07
    CC_qa_risk_based -.-> 08
    CC_qa_test_strategy -.-> 01
    CC_qa_test_strategy -.-> 02
    CC_qa_test_strategy -.-> 03
    CC_qa_test_strategy -.-> 04
    CC_qa_test_strategy -.-> 05
    CC_qa_test_strategy -.-> 06
    CC_qa_test_strategy -.-> 07
    CC_qa_test_strategy -.-> 08
    CC_qa_ci -.-> 01
    CC_qa_ci -.-> 02
    CC_qa_ci -.-> 03
    CC_qa_ci -.-> 04
    CC_qa_ci -.-> 05
    CC_qa_ci -.-> 06
    CC_qa_ci -.-> 07
    CC_qa_ci -.-> 08
    CC_qa_mutation -.-> 01
    CC_qa_mutation -.-> 02
    CC_qa_mutation -.-> 03
    CC_qa_mutation -.-> 04
    CC_qa_mutation -.-> 05
    CC_qa_mutation -.-> 06
    CC_qa_mutation -.-> 07
    CC_qa_mutation -.-> 08
    CC_qa_flaky_detect -.-> 01
    CC_qa_flaky_detect -.-> 02
    CC_qa_flaky_detect -.-> 03
    CC_qa_flaky_detect -.-> 04
    CC_qa_flaky_detect -.-> 05
    CC_qa_flaky_detect -.-> 06
    CC_qa_flaky_detect -.-> 07
    CC_qa_flaky_detect -.-> 08
    CC_qa_a11y -.-> 01
    CC_qa_a11y -.-> 02
    CC_qa_a11y -.-> 03
    CC_qa_a11y -.-> 04
    CC_qa_a11y -.-> 05
    CC_qa_a11y -.-> 06
    CC_qa_a11y -.-> 07
    CC_qa_a11y -.-> 08
    CC_qa_visual_regression -.-> 01
    CC_qa_visual_regression -.-> 02
    CC_qa_visual_regression -.-> 03
    CC_qa_visual_regression -.-> 04
    CC_qa_visual_regression -.-> 05
    CC_qa_visual_regression -.-> 06
    CC_qa_visual_regression -.-> 07
    CC_qa_visual_regression -.-> 08
    CC_qa_unit_tdd -.-> 01
    CC_qa_unit_tdd -.-> 02
    CC_qa_unit_tdd -.-> 03
    CC_qa_unit_tdd -.-> 04
    CC_qa_unit_tdd -.-> 05
    CC_qa_unit_tdd -.-> 06
    CC_qa_unit_tdd -.-> 07
    CC_qa_unit_tdd -.-> 08
    CC_qa_chaos -.-> 01
    CC_qa_chaos -.-> 02
    CC_qa_chaos -.-> 03
    CC_qa_chaos -.-> 04
    CC_qa_chaos -.-> 05
    CC_qa_chaos -.-> 06
    CC_qa_chaos -.-> 07
    CC_qa_chaos -.-> 08
    CC_qa_code_review -.-> 01
    CC_qa_code_review -.-> 02
    CC_qa_code_review -.-> 03
    CC_qa_code_review -.-> 04
    CC_qa_code_review -.-> 05
    CC_qa_code_review -.-> 06
    CC_qa_code_review -.-> 07
    CC_qa_code_review -.-> 08
    CC_qa_synthetic_monitoring -.-> 01
    CC_qa_synthetic_monitoring -.-> 02
    CC_qa_synthetic_monitoring -.-> 03
    CC_qa_synthetic_monitoring -.-> 04
    CC_qa_synthetic_monitoring -.-> 05
    CC_qa_synthetic_monitoring -.-> 06
    CC_qa_synthetic_monitoring -.-> 07
    CC_qa_synthetic_monitoring -.-> 08
    subgraph AT["agent_testing 维度（独立，不接入 8 阶段路由）"]
        AT_qa_agent_eval["qa-agent-eval"]
        AT --> AT_qa_agent_eval
        AT_qa_agent_security["qa-agent-security"]
        AT --> AT_qa_agent_security
    end
    qa_release_check["qa-release-check<br/>· 信号消费/发布门禁"]
    qa_a11y -->|signals| qa_release_check
    qa_agent_eval -->|signals| qa_release_check
    qa_agent_security -->|signals| qa_release_check
    qa_api_contract -->|signals| qa_release_check
    qa_bug_report -->|signals| qa_release_check
    qa_chaos -->|signals| qa_release_check
    qa_code_review -->|signals| qa_release_check
    qa_flaky_detect -->|signals| qa_release_check
    qa_mobile_autotest -->|signals| qa_release_check
    qa_mutation -->|signals| qa_release_check
    qa_orchestrator -->|signals| qa_release_check
    qa_perf_analysis -->|signals| qa_release_check
    qa_perf_jmeter -->|signals| qa_release_check
    qa_risk_based -->|signals| qa_release_check
    qa_security_scan -->|signals| qa_release_check
    qa_synthetic_monitoring -->|signals| qa_release_check
    qa_ui_automation -->|signals| qa_release_check
    qa_unit_tdd -->|signals| qa_release_check
    qa_visual_regression -->|signals| qa_release_check
```

> **维度说明**：上图含 8 个生命周期阶段（stages.json）+ 横切关注点（虚线贯穿）+ 信号数据依赖边。 `agent_testing` 为**独立维度**，含 `qa-agent-eval`、`qa-agent-security` 两个 Agent 测试技能，不接入 8 阶段路由、独立于阶段流之外，详见 `REGISTRY.json`（`category=agent`）与 `stages.json`（`agent_testing` 维度）。
