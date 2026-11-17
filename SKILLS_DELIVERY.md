# 40 项原子 QA 技能全景交付矩阵 (SKILLS_DELIVERY.md — v12.0.0 L6.0)

| 序号 | 技能 ID | 技能名称 | 生命周期阶段 | 架构层级 | 绑定 MCP 原生工具 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 01 | `qa-req-spec` | 非结构化 PRD 智能结构化与提取 | `requirements` | `L1` | `route_qa_skills` |
| 02 | `qa-test-analysis` | 需求细化拆解与全维度风险识别 | `requirements` | `L1` | `route_qa_skills` |
| 03 | `qa-test-case-gen` | 标准测试用例集生成与多格式导出 | `tdm_cases` | `L1` | `route_qa_skills` |
| 04 | `qa-test-data` | 本土化合规测试数据工厂与状态机关联造数 | `tdm_cases` | `L2` | `generate_test_data` |
| 05 | `qa-env-config` | 多环境配置隔离与 Base URL 安全映射 | `tdm_cases` | `L1` | `run_quality_gate` |
| 06 | `qa-api-doc` | 接口规范文档生成与静态合规校验 | `api_testing` | `L1` | `route_qa_skills` |
| 07 | `qa-api-contract` | OpenAPI 3.0/3.1 破坏性变更检测与 3D BOLA 契约模糊测试 | `api_testing` | `L2` | `run_quality_gate` |
| 08 | `qa-api-runner` | 接口自动化测试真实执行与多维断言 | `api_testing` | `L2` | `run_quality_gate` |
| 09 | `qa-graphql-grpc` | GraphQL 与 gRPC 协议契约及深度嵌套查询测试 | `api_testing` | `L2` | `route_qa_skills` |
| 10 | `qa-ui-automation` | Playwright UI 自动化与 ARIA 无障碍树快照自愈 | `ui_mobile` | `L2` | `heal_ui_locator_aria` |
| 11 | `qa-ui-kb` | UI 页面对象知识库与来源签名防投毒 | `ui_mobile` | `L2` | `heal_ui_locator_aria` |
| 12 | `qa-ui-testid` | 前端 AST 扫描与 data-testid / ARIA 属性自动注入 | `ui_mobile` | `L1` | `heal_ui_locator_aria` |
| 13 | `qa-mobile-autotest` | 移动端 App 跨平台自动化测试流水线 | `ui_mobile` | `L2` | `route_qa_skills` |
| 14 | `qa-compat-matrix` | OS × 浏览器 × 设备跨端正交兼容性矩阵 | `ui_mobile` | `L1` | `route_qa_skills` |
| 15 | `qa-exploratory` | 探索性测试章程（Charter）与启发式引导 | `ui_mobile` | `L1` | `route_qa_skills` |
| 16 | `qa-perf-design` | 性能压测全生命周期方案与容量评估模型 | `performance` | `L2` | `route_qa_skills` |
| 17 | `qa-perf-locust` | Locust 分布式协程压测脚本与实时退化熔断 | `performance` | `L2` | `route_qa_skills` |
| 18 | `qa-perf-jmeter` | JMeter 高并发压测计划与线程组编排 | `performance` | `L2` | `route_qa_skills` |
| 19 | `qa-db-benchmark` | 数据库慢查询剖析、索引验证与死锁压测 | `performance` | `L2` | `route_qa_skills` |
| 20 | `qa-security-scan` | OWASP Top 10 安全核查、SAST/DAST 与敏感凭据扫描 | `security` | `L2` | ` sanitize_sensitive_data` |
| 21 | `qa-privacy-compliance` | 个人信息保护法（PIPL）与 GDPR 数据合规审计 | `security` | `L1` | `sanitize_sensitive_data` |
| 22 | `qa-report` | 执行结果多维度聚合诊断与上线质量评估报告 | `release_ops` | `L1` | `run_quality_gate` |
| 23 | `qa-bug-report` | 高复现率结构化缺陷单生成与根因定位辅助 | `release_ops` | `L1` | `route_qa_skills` |
| 24 | `qa-bug-verify` | 缺陷修复回归验证与防逃逸变体测试扩散 | `release_ops` | `L1` | `run_tia_analysis` |
| 25 | `qa-release-check` | 生产发布多重上线红线门禁核查（Go/No-Go） | `release_ops` | `L2` | `run_quality_gate` |
| 26 | `qa-archive` | 测试资产全量版本化归档与基线快照锁定 | `release_ops` | `L1` | `route_qa_skills` |
| 27 | `qa-risk-based` | 基于代码复杂度与变更热度的风险驱动测试排序 | `quality_gates_agent` | `L2` | `run_tia_analysis` |
| 28 | `qa-flaky-detect` | 不稳定用例（Flaky Test）根因识别与隔离治理 | `quality_gates_agent` | `L2` | `run_quality_gate` |
| 29 | `qa-mutation` | AST 算子变异测试与测试集有效性度量（MSI） | `quality_gates_agent` | `L2` | `run_red_blue_swarm` |
| 30 | `qa-a11y` | WCAG 2.2 无障碍合规审计与键盘焦点遍历测试 | `quality_gates_agent` | `L1` | `heal_ui_locator_aria` |
| 31 | `qa-visual-regression` | 多分辨率视觉回归对比与动态区域掩码防噪 | `quality_gates_agent` | `L1` | `route_qa_skills` |
| 32 | `qa-unit-tdd` | 高价值边界单元测试生成与属性测试（PBT）引导 | `quality_gates_agent` | `L2` | `route_qa_skills` |
| 33 | `qa-chaos` | 分布式混沌工程故障注入与韧性逃生演练 | `quality_gates_agent` | `L2` | `route_qa_skills` |
| 34 | `qa-ci` | GitHub Actions / GitLab CI 质量门禁流水线编排 | `quality_gates_agent` | `L1` | `run_quality_gate` |
| 35 | `qa-synthetic-monitoring` | 生产环境合成拨测（Synthetic Monitoring）与金丝雀巡检 | `quality_gates_agent` | `L1` | `route_qa_skills` |
| 36 | `qa-log-triage` | 分布式链路日志智能聚类与异常堆栈根因定位 | `quality_gates_agent` | `L1` | `route_qa_skills` |
| 37 | `qa-data-reconcile` | 分布式账务与跨库数据一致性核对（Reconciliation） | `quality_gates_agent` | `L2` | `generate_test_data` |
| 38 | `qa-shadow-replay` | 流量镜像基准快照沉淀与零代码 Diff 断言（Shadow QA） | `quality_gates_agent` | `L2` | `run_quality_gate` |
| 39 | `qa-agent-eval` | 被测 AI Agent 能力、τ-bench pass^k 一致性与轨迹可靠性评估 | `quality_gates_agent` | `L2` | `run_quality_gate` |
| 40 | `qa-agent-security` | OWASP Agentic Top 10 (ASI:2026) 与 AST10 技能层红蓝对抗测试 | `quality_gates_agent` | `L2` | `run_red_blue_swarm` |
