---

name: qa-ui-testid
description: |-
  当用户希望通过给前端代码批量补加稳定的 data-testid 属性来让 UI 自动化选择器更耐用，
  或苦于页面每次重构脚本就大面积失效时使用。本技能扫描 React/Vue/HTML 源码，找出缺少
  data-testid 的交互元素，按命名规则生成唯一标识，并以预览（dry-run）或写入（write）
  方式输出清单 manifest。触发词："补 data-testid"、"扫描前端加测试属性"、
  "选择器不稳定"、"UI 自动化定位痛点"，或在 qa-ui-automation 之前用于稳定选择器。
  英文触发词（English triggers）：data-testid, selector stability, test attribute.
license: MIT
compatibility: "WorkBuddy / Claude / 通用 Agent（零依赖标准库）"

metadata:
  version: "1.0.0"
  category: traditional
  stage: 06-execution
  tier: 1
---
# qa-ui-testid — 前端扫描注入 data-testid

UI 自动化脚本脆弱的根因是依赖 CSS/XPath。给交互元素统一加 `data-testid`，选择器与
DOM 结构/样式解耦，前端怎么重构只要标识不变脚本就无需改。本技能用脚本批量补，省去
人工逐行添加。

## 何时使用

- 启动 UI 自动化，希望脚本长期稳定。
- 存量老项目页面量大，逐一手动加 testid 工作量大。
- 用户说「补 data-testid」「扫描前端加测试属性」「选择器不稳定」。

## 操作流程

### 步骤 1 — 预览（默认，不改文件）

```bash
python scripts/scan_testid.py --project <前端源码目录> --dry-run --out <变更>/ui-kb/testid-manifest.md
```

脚本扫描 `.tsx/.jsx/.vue/.html` 等，找出「交互元素但缺 data-testid」的标签
（button/a/input/select/textarea 或带 onClick 等事件处理器），按命名规则生成唯一 testid，
输出清单 **不修改源码**。

### 步骤 2 — 确认清单

检查 `testid-manifest.md`：覆盖的界面/元素是否完整，命名是否符合团队规范
（详见 `references/naming-rules.md`）。清单里有「待确认」项可先回答再写。

### 步骤 3 — 写入代码

```bash
python scripts/scan_testid.py --project <前端源码目录> --write --out <变更>/ui-kb/testid-manifest.md
```

脚本直接改源码插入 `data-testid`。写入后建议提交代码让前端 review；
也可把这步交给前端同学在他们仓库执行。

### 步骤 4 — 衔接自动化

补完 testid 后，元素即可被 Playwright `getByTestId()` 稳定捕获。配合 `qa-ui-kb`
沉淀知识库、`qa-ui-automation` 生成页面对象与用例。

## 命名规则（references/naming-rules.md）
- 格式：`<语义来源>-<用途>`，语义取自 name/id/aria-label/placeholder/title，否则取标签名。
- 同文件冲突自动追加 `-2/-3`。
- 可选 `--prefix` 加模块前缀（如 `login-`）。

## 注意
- 默认 dry-run 安全；write 前务必 review 清单。
- 正则扫描对极端写法（属性值含 `>`、动态拼接标签）可能漏判，属预期，人工复核即可。
- 自闭合 `input type="hidden"` 等纯隐藏元素自动跳过。
