---

name: qa-api-doc
description: |-
  当用户需要一份可用的接口规范来驱动接口测试或自动化，却缺少规范文档，或已有的
  Swagger/Yapi 靠手工复制、每次变更就过期时使用。本技能把 Swagger / OpenAPI 动态
  拉取（或读取本地 JSON）为标准化的 Markdown/JSON 接口文档；在没有文档服务器时，
  指导从源码（Java/Go/Python/Node）扫描提取接口清单。触发词："获取接口文档"、
  "拉取 Swagger"、"没有接口文档怎么办"、"从代码生成接口文档"，或在
  qa-api-runner / qa-test-case-gen 之前使用。
  英文触发词（English triggers）：API documentation, Swagger, OpenAPI, API spec.
license: MIT
compatibility: "WorkBuddy / Claude / 通用 Agent（零依赖标准库）"

metadata:
  version: "1.0.0"
  category: traditional
  stage: 05-api
  tier: 1
---
# qa-api-doc — 接口文档获取

接口自动化、接口用例生成都依赖一份**可信的接口清单**。本技能提供两条路径：
① 有 Swagger/OpenAPI/Yapi → 用脚本动态拉取，告别手抄与过期；② 无文档服务器 →
按 `references/code-scan-guide.md` 从源码扫描提取。

## 何时使用

- 要做接口测试 / 自动化，但缺规范接口文档。
- 已有 Swagger 但每次手动复制、易过期。
- 用户说「获取接口文档」「拉取 Swagger」「从代码生成接口文档」。

## 路径 A — 从 Swagger / OpenAPI 拉取（推荐）

运行内置脚本（混合深度：拉取与格式化交给脚本，稳定且可复现）：

```bash
python scripts/swagger_fetch.py --url <OpenAPI JSON 地址> \
    --token "<JWT或Bearer>" --output <变更目录>/05-api/api-doc.md \
    --save-json <变更目录>/05-api/api-doc.json
```

- 支持 `--token`（Bearer）或 `--username/--password`（Basic）。
- 本地 JSON 用 `--file openapi.json`。
- 只看部分接口加 `--filter "user,order"`。
- 产出：`api-doc.md`（人读）+ `api-doc.json`（供 `qa-api-runner` 直接消费）。

## 路径 B — 从源码扫描（无文档服务器）

按 `references/code-scan-guide.md` 针对技术栈定位路由注解，提取：
URL、方法、参数、请求体、响应。整理为标准接口清单（Markdown/JSON）。
可让开发执行或自行扫描，产出同样落入 `05-api/`。

## 输出规范（references/api-doc-schema.md）

无论哪条路径，最终文档应包含每项接口的：
- 方法 + 路径
- 鉴权方式
- 路径/查询/请求体参数（名称、类型、必填、说明）
- 主要响应码与含义
- 依赖（登录态、前置接口）

## 落盘与衔接

- 文档写入变更工作区 `05-api/`。
- 立即衔接：`qa-test-case-gen`（接口用例）/ `qa-api-runner`（自动化执行）。
- 接口变更后重新拉取即可，无需手写维护。

## 注意

- 含密码 / Token 的文档，生成后建议把敏感值替换为占位符再入库。
- 拉取失败多为鉴权或地址问题，先用浏览器 F12 拿到真实 OpenAPI JSON 地址与请求头。

## 阶段产物契约（stages.json artifacts）

本阶段主技能须产出的文件名（与 `qa-orchestrator/stages.json` 契约一致）：

- api-doc.md
- api-doc.json
- openapi.json
