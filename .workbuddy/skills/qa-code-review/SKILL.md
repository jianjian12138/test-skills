---

name: qa-code-review
description: 代码评审启发式门禁技能：纯标准库扫描源码，识别评审期高危反模式——硬编码密钥(critical/阻断)、SQL 拼接、超长函数、无工单的 TODO/FIXME、遗留调试打印；存在硬编码密钥时产出阻断信号。触发词："代码评审", "code review", "CR", "评审门禁", "静态检查", "代码质量", or after qa-unit-tdd. 英文触发词（English triggers）：code review, CR, static analysis, lint.
license: MIT
metadata:
  version: "1.0.0"
  category: traditional
  stage: cross_cutting
  tier: 2
compatibility: "WorkBuddy / Claude / 通用 Agent（零依赖标准库）"
---
# qa-code-review 代码评审启发式门禁

在合并 / 发布前，用轻量静态扫描兜底**评审容易漏掉的反模式**。本技能是启发式 linter，与 `qa-security-scan`（完整 SAST/DAST 指引）互补：前者查"评审纪律"，后者查"安全漏洞"。

> ⚠️ **治理门禁 · 不执行外部工具**：本技能是纯标准库静态扫描，不调用任何外部 SAST/DAST 工具、不发起网络请求、不对目标系统做任何改动；仅基于源码文本做启发式规则匹配。

## 何时使用
- PR / 合并请求提交后，作为 CI 评审门禁的一环。
- 想快速兜底硬编码密钥、SQL 拼接、超长函数等明显坏味道。
- 在 `qa-unit-tdd` 之后，或作为发布前代码质量保障的一环。

## 规则
| 规则 | 反模式 | 严重度 |
|---|---|---|
| CR-HARDCODED-SECRET | 硬编码密码 / 密钥 / token | critical / **blocking** |
| CR-SQL-CONCAT | SQL 字符串拼接（注入风险） | high |
| CR-LONG-FUNC | 函数 / 方法过长（>阈值行） | high |
| CR-TODO-NO-TICKET | TODO/FIXME 未关联工单 | medium |
| CR-DEBUG-PRINT | 遗留调试打印（print/console.log） | low |

存在 `critical`（`CR-HARDCODED-SECRET`）→ 产出 `blocking=true` 信号，门禁失败。

## 使用方式
```bash
python qa-code-review/scripts/review_scan.py --src ./src --out signals
python qa-code-review/scripts/review_scan.py --src app.py --out signals --max-func-len 60
```

## 诚实边界（重要）
- 本技能是**启发式静态检查**，不解析 AST、不理解数据流 / 语义，误报与漏报均可能存在。
- 它**不替代** `qa-security-scan`（ZAP/Semgrep/Trivy）的安全深度扫描；密钥类问题建议两者并用。
- 超长函数判定基于"声明到下一声明"的行距启发式，跨语言的精确 cyclomatic 复杂度需专用工具。

## 参考资料

- 检查项、阈值、CLI 用法与常见坑：见 [`references/guide.md`](references/guide.md)。
