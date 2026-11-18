# Universal QA Skills (v12.1.0 — L6.0) 详细使用手册 (USAGE.md)

## 0. “骨·肉·尺”三步标准工作流 (v12.1.0 核心准则)
1. **立骨（套用场景模板）**：运行 `python3 qaskills.py templates --id SCEN-MASTER` 获取通用场景骨架模板，定义状态流转与业务守恒律。
2. **填肉（挂载通用技能）**：沿场景每个节点调用 `python3 qaskills.py route` 挂载 49 个纯通用原子技能打穿边界、权限（3D BOLA）、性能与异常。
3. **量尺（双轴门禁验收）**：联合校验场景连通率（必要条件）与节点代码覆盖率/`pass^5` 门禁（充分条件）。

## 1. L1/L2 渐进式技能路由与按需加载
避免一次性将 49 个技能全量塞入上下文，通过两阶段加载节省 **85%+** Prompt Tokens：

```bash
# 第一阶段 (L1 Router)：按意图检索 <= 4 个候选技能摘要及 Token 账本
python3 qaskills.py route "Playwright ARIA 无障碍树选择器自愈"

# 第二阶段 (L2 Loader)：按需加载目标技能的完整 SKILL.md SOP 规约
python3 qaskills.py load qa-ui-automation
```

## 2. 双模 MCP Server 挂载指南 (stdio + Streamable HTTP)

### 方式 A：本地 IDE (`stdio` 零依赖管道)
在 Cursor / Claude Code / Antigravity 的 `mcp_config.json` 中配置：

```json
{
  "mcpServers": {
    "universal-qa-skills-l6": {
      "command": "python3",
      "args": ["/path/to/test-skills/skills/tools/mcp_server.py", "--transport", "stdio"]
    }
  }
}
```

### 方式 B：团队/CI 远程共享网关 (`Streamable HTTP` 传输)
符合 MCP `2025-11-25` / `2026` 规范，单端点 `/mcp` 支持双向 JSON-RPC、批处理、`Mcp-Session-Id` 会话保持与 `X-Trace-Id` 链路追踪：

```bash
python3 qaskills.py serve-mcp --transport http --host 0.0.0.0 --port 8765
```

## 3. 核心测试引擎 CLI 速查

```bash
# ① 生成中国大陆合规身份证/手机号/跨表关联订单状态机数据 (Users -> Orders -> Payments -> Inventory)
python3 qaskills.py data --type order_chain --count 3

# ② 主动清洗文本中的大陆身份证、手机号与 API 密钥
python3 qaskills.py sanitize "测试客户身份证 11010119900307251X，手机 13812345678，密钥 sk-1234567890abcdef"

# ③ 动静融合 TIA 精准测试分析 (Git Diff + Python AST + .coverage SQLite 动态行级上下文)
python3 qaskills.py tia --diff HEAD~1

# ④ 基于 Playwright MCP ARIA 快照 (200-400 Tokens) 的 UI 定位器自愈
python3 qaskills.py aria-heal --selector "#legacy-pay-btn" --intent "立即提交并支付"

# ⑤ 生成 3D BOLA/IDOR 有状态接口越权测试矩阵 (4 角色 × 3 动作 × 3 状态 = 36 向量)
python3 qaskills.py bola-fuzz --endpoint "/api/v1/orders/{order_id}"

# ⑥ 运行 OWASP Agentic Top 10 (ASI:2026) & AST10 红蓝对抗自主进化飞轮
python3 qaskills.py swarm --rounds 6

# ⑦ 运行 3D 黄金数据集与 τ-bench pass^k (k=5) 自动化评测门禁
python3 qaskills.py eval
```
