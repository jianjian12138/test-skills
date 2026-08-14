# 一键归档指南 — qa-archive

## 1. 归档范围
- 输入：由 `qa-orchestrator` 的 `init_change.py` 创建的变更目录（`changes/<名>/`，含 01-requirement … 08-archive 各阶段产物）。
- 输出：`archives/<变更名>_<时间戳>.zip`（全部产物，自动排除 `__pycache__`/`.tmp`/`.workbuddy` 等缓存与敏感目录）+ `<变更名>_<时间戳>_manifest.md`（目录树 + 文件数 + 总大小 + 关键结论摘要）。

## 2. 阻断规则
- 本技能**不产出质量信号**（纯交付/审计动作），无 `blocking` 门禁。
- 失败即 `sys.exit(1)` 的情形：`--change` 指向的目录不存在，或 `--out` 不可写。

## 3. CLI 约定
```bash
python qa-archive/scripts/archive_change.py --change changes/登录模块v2 --out ./archives
```
- `--change`：待归档的变更目录（必填）。
- `--out`：归档落盘目录（必填，自动创建）。

## 4. 常见坑（诚实边界）
- 归档前确保 `qa-release-check` 已通过——归档是生命周期最后一环，先有上线结论再打包，否则证据链缺门禁结论。
- 清单 `manifest.md` 为摘要占位，不替代真实报告；如需完整证据，保留原始目录而非仅依赖 zip。
- 中文变更名会进入 zip 文件名，跨平台解压注意编码（zip 用 UTF-8 文件名）。
