# 多环境切换规范（switching-guide）

## 目录结构
```
config/
├── .env.example   # 空模板，可提交仓库
├── .env.dev       # 开发环境（真实值，勿提交）
├── .env.test      # 测试环境
└── .env.staging   # 预发环境
```
`.gitignore` 中加入：`config/.env.*`（仅保留 `.env.example`）。

## 切换方式
- 接口：`python run.py --env-file config/.env.test ...`
- UI：`pytest ... ` 前 `export ENV=test` 或在 conftest 读取 `config/.env.<ENV>`。
- **只换 `--env-file` / 环境变量，绝不改动用例与脚本。**

## 字段约定
| 字段 | 含义 |
|---|---|
| BASE_URL | 接口/UI 基地址 |
| TEST_USER / TEST_PASSWORD | 测试账号 |
| AUTH_TOKEN | 直填 token（或留空由登录用例 extract） |
| DB_ASSERT_ENABLED / DB_* | 数据库双校验开关与连接 |
| TIMEOUT | 请求超时（秒） |

## 纪律
- 敏感值只存本地 `.env`，不进仓库、不进聊天、报告里不出现明文密码/token。
- 新增环境只需加一个 `.env.<new>` 并在脚手架 `--envs` 补充。
- 同一份用例应在 dev/test 跑通后再上 staging，最后才做生产预发核验。
