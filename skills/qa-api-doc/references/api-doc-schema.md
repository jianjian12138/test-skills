# 标准接口文档结构（api-doc-schema）

无论来自 Swagger 拉取还是源码扫描，最终接口文档应覆盖以下要素，便于 `qa-api-runner`
直接消费。swagger_fetch.py 已按此结构输出 Markdown。

## 单接口记录字段
| 字段 | 说明 | 示例 |
|---|---|---|
| method + path | HTTP 方法 + 路径 | `POST /api/v1/login` |
| summary | 一句话说明 | 用户登录 |
| auth | 鉴权方式 | Bearer / Cookie / 无 |
| path params | 路径参数 | `id`(long, 必填) |
| query params | 查询参数 | `page`(int, 可选) |
| body | 请求体字段（名称/类型/必填/说明） | `{username:string 必填, password:string 必填}` |
| responses | 主要响应码与含义 | `200 成功` / `401 未登录` |
| depends | 依赖的前置接口 / 数据 | 需先 `POST /login` 拿 token |

## 机器可读格式（api-doc.json）
保留原始 OpenAPI JSON 即可；`qa-api-runner` 可直接解析 paths 生成用例与执行骨架。

## 质量要求
- 每个接口至少包含：方法、路径、必填参数、成功/失败响应。
- 鉴权与依赖必须标注，否则自动化无法串联。
- 不遗漏错误码（401/403/404/500 等）对应的业务含义。
