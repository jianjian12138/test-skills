# 验证/回归输入 Schema（qa-bug-verify）

```json
{
  "bug_id": "BUG-101",
  "title": "下单提交无响应",
  "module": "下单",
  "fix_version": "v2.0.1",
  "affected_modules": ["下单", "购物车"],
  "steps": ["打开下单页", "填地址", "点提交"],
  "acceptance": ["订单创建成功", "页面无报错"],
  "risk": "high|medium|low",
  "related_cases": ["下单-正常", "购物车-结算"]   // 可选，已知关联用例
}
```

## 验证清单（verification）

- 在修复版本 `fix_version` 的对应环境重跑 `steps`。
- 逐条核对 `acceptance`；任一不满足 → 验证失败，打回。

## 回归范围推导

- **直接受影响**：`affected_modules` 全量用例。
- **相邻模块**：与 `module` 有调用/数据关系的模块（如下单依赖购物车、库存）。
- **风险加成**：`risk=high` 时扩大至相邻模块冒烟。

## 准入结论

```
验证：✅ 全过 / ❌ 仍有问题
回归：✅ 无新增失败 / ❌ 引入 N 个新问题
结论：可关闭 / 打回重改
```
