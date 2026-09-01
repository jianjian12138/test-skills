# 上线检查输入 Schema（qa-release-check）

```json
{
  "version": "v2.0.0",
  "env": "prod",
  "services": ["order", "pay"],
  "smoke": ["下单冒烟", "支付冒烟"],
  "db_migrations": true,
  "config_ok": true,
  "deps_ok": true,
  "rollback_plan": true,
  "monitoring": ["错误率告警", "核心接口SLA", "CPU/内存"]
}
```

## 上线门禁（Gate）红线

任一不过，**禁止发布**：

- 构建产物版本与发布单一致
- DB 迁移脚本已评审且可回滚
- 配置（含密钥）已就位、无硬编码
- 三方依赖/限流/配额已确认
- 回滚方案明确且演练过

## 发布后监控窗口

- 灰度（5%~10%）观察 30 分钟：错误率、P95、核心转化率。
- 全量后观察 2 小时 + 次日早高峰。
- 异常 → 触发回滚，重开缺陷，复盘。
