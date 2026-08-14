# 缺陷模板（统一格式，喂 qa-bug-report / release 门禁）

```json
{
  "id": "B-xxx",
  "title": "一句话现象",
  "severity": "S1|S2|S3|S4",
  "status": "open|closed",
  "module": "所属模块",
  "root_cause": "根因（闭环三问之『为什么』；缺失则判未闭合）",
  "action": "处置方案/负责人（闭环三问之『可处置』；open S1/S2 缺失则阻断发布）",
  "source": "exploratory|execution|api",
  "repro": "复现步骤"
}
```

> 门禁规则（qa-release-check）：存在未关闭 S1/S2 缺陷 → ❌ 禁止发布（sys.exit(1)）。
> 探索性发现的缺陷由 qa-exploratory 的 debrief 自动产出此格式。
