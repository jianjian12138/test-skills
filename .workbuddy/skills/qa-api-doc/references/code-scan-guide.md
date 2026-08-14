# 源码扫描提取接口指南（code-scan-guide）

当没有 Swagger / Yapi 文档服务器时，按技术栈定位路由定义，人工或借助 grep/脚本提取接口。
目标产出与 api-doc-schema.md 一致的标准接口清单。

## 通用步骤
1. 确认后端技术栈与路由注册方式（见下）。
2. 全局搜索路由注解 / 注册调用，收集 `method + path`。
3. 对每个接口读取入参（DTO / 请求体结构）与出参（返回对象）。
4. 标注鉴权注解（如 `@PreAuthorize`、`JWT`、`LoginRequired`）。
5. 整理为标准接口清单（Markdown/JSON），落到 `05-api/`。

## 各技术栈路由特征
| 技术栈 | 路由注解 / 注册 | 入参特征 |
|---|---|---|
| Spring Boot (Java) | `@GetMapping`/`@PostMapping`/`@RequestMapping` 类+方法 | `@RequestBody` DTO、`@RequestParam`、`@PathVariable` |
| Go (Gin) | `r.GET("/x", handler)`、`gin.Default()` | `c.Query()`、`c.Param()`、`c.ShouldBindJSON()` |
| Go (Echo) | `e.POST("/x", h)` | `c.Bind()` |
| Python (FastAPI) | `@app.get("/x")` / 装饰器 | 函数参数 + Pydantic 模型 |
| Python (Flask) | `@app.route("/x", methods=[...])` | `request.json` / `request.args` |
| Node (Express) | `app.get("/x", ...)` / 路由文件 | `req.body` / `req.params` / `req.query` |
| Node (NestJS) | `@Controller()` + `@Get()`/`@Post()` | DTO 类 + 装饰器 |

## 提取技巧
- 用 grep 批量找注解：`grep -rn "@PostMapping\|@GetMapping" src/`。
- 关注统一响应包装（如 `{code,msg,data}`），记录 data 结构。
- 关注全局异常处理器，映射错误码到业务含义。
- 若有 DTO 类，优先读字段注释与校验注解（@NotBlank、@Size）判断必填与边界。

## 产出清单示例
```
POST /api/v1/login        用户登录        Bearer无(公开)   body:{username必填,password必填}  200/401
GET  /api/v1/user/{id}    获取用户详情    Bearer           path:id(long必填)                  200/401/404
```
