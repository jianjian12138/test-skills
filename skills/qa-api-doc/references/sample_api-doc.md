# 接口文档（自动生成）
- 标题：Demo API
- 版本：1.0.0  | OpenAPI/Swagger：3.0.1
- 接口总数：2

## 接口清单

### `POST /api/v1/login`
- 说明：用户登录
- 参数：
  - `X-Trace` (header, 可选)：链路ID
- 请求体：
  - username：string（必填）：手机号
  - password：string（必填）：密码
- 主要响应：
  - `200`：成功
  - `401`：未授权

### `GET /api/v1/user/{id}`
- 说明：获取用户
- 参数：
  - `id` (path, 必填)：用户ID
- 主要响应：
  - `200`：OK
  - `404`：不存在
