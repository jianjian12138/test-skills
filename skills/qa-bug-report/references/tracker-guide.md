# 缺陷平台对接指南（qa-bug-report）

`gen_bug.py --tracker <tapd|zentao|jira>` 会输出字段映射 JSON，按平台投递。

## TAPD

- 缺陷 API：`POST https://api.tapd.cn/bugs`
- 字段映射：title→title，severity(S1-S4)→severity(1致命~4建议)，priority(P0-P3)→priority，
  module→module，steps/expected/actual→description（合并），env→custom_field，
  reporter→current_owner 之外由创建人决定，assignee→assigned。
- 鉴权：TAPD API 账号 + 密码的 Basic Auth（写在环境变量，勿硬编码）。

## 禅道（ZenTao）

- 接口：`POST /zentao/index.php?m=bug&f=create` 或 API 模块。
- 字段映射：title→title，severity→severity(1~4)，priority→pri(1~4 反向要注意)，
  module→module，steps→steps，type→type(bug/feature等)。
- 注意：禅道 severity 数字越大越轻，与本项目 S1 最重相反，映射时反转。

## Jira

- 创建 Issue：`POST /rest/api/2/issue`，issuetype=Bug。
- 字段映射：title→fields.summary，severity→自定义字段或 Priority 枚举，
  priority→fields.priority，steps/expected/actual→fields.description，
  assignee→fields.assignee.accountId，reporter→fields.reporter。
- 鉴权：API Token（Bearer）或邮箱+Token Basic。

## 通用建议

- 凭据一律走环境变量 / 密钥管理，禁止写进 bug JSON 或脚本。
- 批量提交用 `gen_bug.py` 生成的 payload 数组循环调用平台 API。
- 安全类缺陷（来自 qa-security-report）建议单独标记为 confidential / 安全标签。
