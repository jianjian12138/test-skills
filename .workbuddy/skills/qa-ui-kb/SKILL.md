---

name: qa-ui-kb
description: |-
  当用户启动或维护 UI 自动化，需要沉淀一份稳定、可供 AI 读取的被测页面知识库，
  让生成的 Playwright/Cypress 脚本使用正确且耐用的选择器而不是靠猜时使用。本技能
  定义三层知识库（元素描述 / 操作模式 / 选择器规则）、四层代码架构，以及选择器
  优先级规范。触发词："建 UI 知识库"、"UI 自动化怎么组织"、"页面结构怎么沉淀"，
  或在 qa-ui-automation 之前使用。
  英文触发词（English triggers）：UI knowledge base, selector, page structure.
license: MIT
compatibility: "WorkBuddy / Claude / 通用 Agent（零依赖标准库）"

metadata:
  version: "1.0.0"
  category: traditional
  stage: 06-execution
  tier: 3
---
# qa-ui-kb — UI 自动化知识库

UI 自动化的头号成本是**选择器调试**，不是写脚本。解决方法是沉淀一份给 AI 读的知识库，
让生成的脚本「看着地图走路」。本技能定义知识库怎么建、怎么用、怎么维护。

## 何时使用

- 启动 UI 自动化，或脚本因页面重构大面积失效。
- 用户说「建 UI 知识库」「页面结构怎么沉淀」。
- 在 `qa-ui-automation` 生成脚本之前，应先有知识库。

## 三层知识库（详见 references/kb-template.md）

1. **元素描述**：存「这个元素是什么、做什么」，不存选择器本身。选择器变了，描述不变。
2. **操作模式**：某模块典型操作流（如「新增配置：点新增→填名称→选分类→保存→校验列表多一条」）。固化流程，不固化代码。
3. **选择器规则**：项目命名规范（如按钮用 `data-testid`，表格用 `.grid-row`）。新页面按规则直接定位。

## 四层代码架构（详见 references/four-layer-arch.md）

用例层 / 页面层（Page Object）/ 元素层（选择器集中管理）/ 工具层。选择器集中在元素层，改一处全局生效。
知识库（输入）→ AI 读取 → 生成代码 → 四层架构（输出），二者是输入与输出的关系，缺一不可。

## 选择器优先级规范（references/selector-rules.md）

```
getByRole > getByText > getByLabel > getByPlaceholder > CSS selector
```
- 优先语义化定位（role/text/label），CSS 仅兜底（自定义组件无语义属性时）。
- 禁止用索引定位（`.first()`/`.nth(i)`/`.last()`）。

## 维护触发条件

前端重构、组件库升级、动态 class 变更 → 需更新知识库；普通业务迭代（加字段/改文案）不影响。
**每个写入知识库的选择器必须经过实际验证**（至少跑通一次），否则 AI 会基于错误信息生成大量错误脚本。

## 操作流程

1. 对每个核心页面，探查后填写知识库三件套（结构树 + 关键元素表 + 陷阱笔记）。
2. 把结构树与元素表存入变更工作区（或独立 `ui-kb/` 目录），供 `qa-ui-automation` 读取。
3. 每次探查新页面顺手更新，每次踩坑补一条注意事项（增量维护，不推倒重来）。

## 与上下游衔接

- 输入：来自 `qa-test-analysis` 的 UI 相关测试点。
- 输出：供 `qa-ui-testid`（补 testid）、`qa-ui-automation`（生成稳定脚本）消费。
