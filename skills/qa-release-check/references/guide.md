# 上线验证与发布后核对指南 — qa-release-check

## 1. 门禁范围
- 生成三类清单：**上线门禁**（构建/DB 迁移/配置/依赖/回滚方案）、**上线冒烟**（核心链路最小验证）、**发布后监控**（错误率/延迟/资源/业务指标）。
- 信号门禁：扫描 `--signals-dir` 下各技能产出的 `*.json`，按 `blocking`/`severity`/`verified` 判定是否具备上线条件。

## 2. 阻断规则（fail-closed）
- 以下任一 → 门禁不过（配合 `--fail-on` 时 `sys.exit(1)`）：
  - 缺失默认必需信号来源（S-01；`--skip-required` 可关闭，仅限非发布场景）；
  - 任一信号 `blocking=true`（如安全命中、SLA 不达标）；
  - 信号文件损坏（R-01，损坏即 fail-closed）；
  - 信号缺新鲜度戳或超阈判陈旧（R-06）。
- 干净运行（三方 verified 齐备、无 blocking）默认通过。

## 3. CLI 约定
```bash
python qa-release-check/scripts/gen_release_checklist.py \
  --release release.json --signals-dir signals --out release_check.md --fail-on
```
- `--release`：发布元数据 JSON（必填）。
- `--signals-dir`：质量信号目录（默认 `./signals`）。
- `--fail-on`：门禁不过时退出 1（默认**关**，需显式开启以在 CI 真阻断）。
- `--skip-required`：关闭默认必需信号强制（仅非发布探索场景）。

## 4. 常见坑（诚实边界）
- 默认 `--fail-on` 为关——若只在本地看清单、未加 `--fail-on`，CI 不会因门禁不过而红，属"假绿"风险。
- `verified` 信号需 `qa-security-scan`/`qa-a11y`/`qa-unit-tdd` 三方齐备才视为默认门禁通过，缺一则阻断。
- 本技能只核验"证据是否齐备且未标红"，不替你跑实际冒烟/监控——发布后监控仍需人工/平台侧落地。
