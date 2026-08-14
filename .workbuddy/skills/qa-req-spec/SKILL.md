---

name: qa-req-spec
description: |-
  当用户手上是零散、非结构化的原始需求材料（PRD 片段、用户故事、会议记录、
  蓝湖/Figma 原型标注文字、或以文字描述的截图），需要转成规范、可直接用于测试的
  需求文档时使用。本技能产出结构统一的 Markdown 需求文档，包含模块划分、交互规则、
  输入与权限约束、异常边界及待确认问题，供下游 qa-* 技能消费。触发词："整理需求"、
  "把原型转成需求文档"、"需求结构化"、"这份需求帮我规范一下"，或当需求刚粘贴进来、
  尚不足以直接做测试分析时使用。
  英文触发词（English triggers）：requirement spec, PRD, requirement structuring.
license: MIT
compatibility: "WorkBuddy / Claude / 通用 Agent（零依赖标准库）"

metadata:
  version: "1.0.0"
  category: traditional
  stage: 01-requirement
  tier: 1
---
# qa-req-spec — 需求结构化

需求散、缺、乱是测试漏测的根源。本技能把**任意原始需求材料**转化为一份结构统一、
可直接喂给 `qa-test-analysis` 的标准需求文档（`requirement.md`）。

## 何时使用

- 用户贴来 PRD 片段、用户故事、会议记录、原型标注文字。
- 用户说「把原型/蓝湖内容转成需求文档」「需求帮我规范一下」。
- 拿到的是截图描述而非结构化文档。

## 输入

- 原始需求文本 / 用户故事 / 原型标注（可引用文件或粘贴）。
- 可选：产品原型链接（蓝湖/Figma 等，若已配 MCP 则先拉取内容）。

## 操作流程

### 步骤 1 — 抽取与归类（对照抽取检查单）

读取 `references/extraction-checklist.md`，逐项从原始材料中抽取：

- 业务背景与目标
- 涉及模块 / 页面
- 每个模块的功能点与交互规则
- 输入约束（格式、长度、必填、枚举）
- 权限 / 角色约束
- 异常与边界处理
- 非功能需求（性能/安全/兼容，若有提及）

### 步骤 2 — 套用标准模板

按 `references/requirement-template.md` 输出 `requirement.md`，固定章节顺序：

1. 背景与目标
2. 测试范围（范围内 / 范围外）
3. 功能模块划分
4. 各模块交互规则与操作细则
5. 特殊约束（输入格式、权限、异常提示）
6. 非功能需求（NFR）
7. 待澄清项（无法从材料确定的，先列出，交 `qa-test-analysis` 对话澄清）

### 步骤 3 — 标注不确定项

凡材料缺失、矛盾、模糊之处，**不要臆测**，统一放进「待澄清项」并标注影响（会阻塞哪些测试设计）。
这些项将在 `qa-test-analysis` 阶段由用户补充。

### 步骤 4 — 落盘

将 `requirement.md` 写入变更工作区的 `01-requirement/` 目录（由 `qa-orchestrator` 建立）。

## 深化能力（V2）

- 需求可追溯矩阵：`scripts/gen_trace_matrix.py` 由需求列表生成
  「需求 → 测试点 → 用例 → 结果」追溯骨架，保证每条需求都被测到。
- NFR 提取模板、验收标准（AC）模板、可追溯矩阵与测试清单见 `references/checklist.md`。

## 质量要求

- **可追溯**：每个功能点都能回溯到原始材料出处（引用原文片段）。
- **可测**：描述用「系统应…」「当用户…则…」的确定性语言，避免「支持」「优化」等模糊词。
- **不臆测**：不确定的写进待澄清项，而非编进需求。

## 与下游衔接

输出后建议立即调用 `qa-test-analysis`，并携带本 `requirement.md` 作为分析输入。

## 阶段产物契约（stages.json artifacts）

本阶段主技能须产出的文件名（与 `qa-orchestrator/stages.json` 契约一致）：

- requirement.md
- reqs.json
