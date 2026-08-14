# 用例 JSON Schema（cases-schema）

`gen_case.py` 的输入格式。AI 从测试点整理为此结构，脚本据此稳定产出 Excel / Xmind。

```json
{
  "title": "登录模块测试用例",
  "cases": [
    {
      "id": "TC-LOGIN-001",
      "module": "登录",
      "name": "正确账号密码登录",
      "type": "正向",
      "priority": "P0",
      "precondition": "已注册且未登录的用户",
      "steps": [
        "打开登录页",
        "输入正确的手机号",
        "输入正确的密码",
        "点击「登录」按钮"
      ],
      "expected": "登录成功，跳转至首页，右上角显示用户头像"
    },
    {
      "id": "TC-LOGIN-002",
      "module": "登录",
      "name": "密码错误锁定",
      "type": "负向",
      "priority": "P0",
      "precondition": "已注册用户",
      "steps": [
        "打开登录页",
        "输入正确账号",
        "连续 5 次输入错误密码",
        "第 6 次输入正确密码并点击登录"
      ],
      "expected": "账号被锁定，提示「密码错误次数过多，请 30 分钟后重试」"
    }
  ]
}
```

## 字段说明
- `title`：用例集标题（Xmind 根节点名）。
- `cases[].id`：用例编号，缺省时脚本按序号补 `TC-xxx`。
- `cases[].covers`：（可选）归属测试点 ID（如 `TP-001`）。用于 `scripts/trace_matrix.py` 构建 **用例→测试点→需求** 三级追溯矩阵；缺省时工具退化从用例正文抽取 `TP-` 提及。建议显式填写以闭合追溯链。
- `cases[].module`：所属模块（Xmind 二级节点；Excel「模块」列）。
- `cases[].type`：正向 / 负向 / 边界 / 专项。
- `cases[].priority`：P0–P3。
- `cases[].steps`：字符串数组，脚本自动编号。
- `cases[].expected`：可观测的预期结果。

## 编写纪律
- 步骤必须能从「前置条件」走到「预期结果」，否则是无效用例。
- 一条用例只验证一个核心断言，避免「顺手多测」导致失败难定位。
- 高风险模块（支付、权限）负向 / 边界用例密度应更高。
