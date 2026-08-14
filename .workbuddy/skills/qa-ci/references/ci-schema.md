# CI 配置输入 Schema（qa-ci）

```json
{
  "project": "order-svc",
  "python_version": "3.13",
  "providers": ["github", "gitlab", "jenkins"],
  "test_cmd": "pytest -q",
  "lint_cmd": "flake8 .",
  "security_cmd": "semgrep --config auto",
  "services": ["postgres"],
  "branches": ["main"],
  "timeout_min": 30
}
```

## providers 取值

- `github` → `.github/workflows/qa.yml`（GitHub Actions）
- `gitlab` → `.gitlab-ci.yml`
- `jenkins` → `Jenkinsfile`（Declarative Pipeline）

## 阶段映射（所有 provider 一致）

1. install：恢复依赖（pip install）
2. lint：`lint_cmd`（默认 flake8）
3. test：`test_cmd`（默认 pytest）
4. security：`security_cmd`（默认 semgrep）

## 服务依赖

`services` 列出需要的容器（postgres / redis / mysql），
生成对应的 service 容器定义。无则跳过。

## 失败策略

任一阶段非零退出 → 流水线红，阻断合并（security 可单独设阈值告警不阻断）。
