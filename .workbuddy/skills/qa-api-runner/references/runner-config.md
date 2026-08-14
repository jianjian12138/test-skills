# 接口执行框架配置（runner-config）

## 1. 依赖安装
```bash
pip install requests
# 可选（DB 断言）：
pip install mysql-connector-python
# 可选（Allure 可视化报告）：
pip install pytest allure-pytest
```

## 2. 环境配置（config/.env）
复制示例并填写。未开启 DB 断言时，相关字段可留空。

```ini
# 基础地址（覆盖场景里的 base_url）
BASE_URL=https://api.example.com

# DB 断言开关：true 才启用
DB_ASSERT_ENABLED=false
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=test_user
DB_PASSWORD=test_pwd
DB_NAME=app_db
```

> 注意：含密码的 .env 不要提交到公开仓库；建议加入 .gitignore。

## 3. 两种运行方式
### 方式 A — 轻量运行（无需 pytest）
```bash
python scripts/run.py --scenario scenario.json --env-file config/.env --outdir <变更>/06-execution
```
产出 `results.json` + `report.md`（通过率 / 失败点）。

### 方式 B — Allure 可视化报告
```bash
export QA_SCENARIO=scenario.json
export QA_ENV_FILE=config/.env
pytest scripts/test_api.py --alluredir=allure-results
allure serve allure-results
```

## 4. 串联与双校验要点
- 串联：把业务链按序写成 cases，前一步 `extract` 的变量用 `${var}` 注入后一步请求头/体。
- DB 断言：开启 `DB_ASSERT_ENABLED=true` 并填写连接信息；接口返回成功不代表数据正确入库，
  用 `db_assert` 校验库表落地，避免「假成功」。
- 失败中断：单个用例异常或断言失败会标记为失败并继续后续用例（不会中断整轮），
  但串联场景下游若依赖其变量，需人工确认下游影响。

## 5. 与上游衔接
- 场景 JSON 可由 `qa-api-doc` 的 `api-doc.json` + 业务链描述，由 AI 生成。
- 执行结果（results.json / report.md）交给 `qa-report` 汇总，失败用例转 `qa-bug-report`（Phase 4）。
