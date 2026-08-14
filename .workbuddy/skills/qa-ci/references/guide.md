# CI/CD 流水线配置生成指南 — qa-ci

## 1. 生成范围
- 输入：一份配置 JSON，声明 `project` / `python_version` / `providers`（github/gitlab/jenkins 选一或多）/ `test_cmd` / `lint_cmd` / `security_cmd` / `services`（如 postgres）/ `branches`。
- 输出：`--outdir` 下生成 `.github/workflows/qa.yml` / `.gitlab-ci.yml` / `Jenkinsfile`（按 providers 选择），默认串起 **install → lint → test → security** 四阶段，缺省失败即阻断合并。

## 2. 阻断规则
- 各阶段非零退出即阻断流水线（security 阶段可下调为警告阈值，见配置）。
- 本技能**不产出质量信号**；真正的信号门禁在 `qa-release-check` 聚合。

## 3. CLI 约定
```bash
python qa-ci/scripts/gen_ci.py --config ci.json --outdir ./ci_out
```
- `--config`：配置 JSON（必填）。
- `--outdir`：生成目录（必填，自动创建）。

## 4. 常见坑（诚实边界）
- `security_cmd` 缺省为空时不会生成安全阶段——不要把"无安全扫描"误当"已扫描通过"。
- `services` 仅声明依赖（如 postgres），需在生成后于平台侧配置对应 Service Container，否则 install/test 会因连不上依赖而失败。
- GitHub Actions 默认只在 `branches` 上触发；保护分支规则需另行在仓库设置，本技能不代管分支保护。
