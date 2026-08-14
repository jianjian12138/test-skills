# data-testid 命名规则（naming-rules）

## 取值优先级（用于生成语义来源）
1. `name` / `id` 属性值
2. `aria-label`
3. `placeholder`（输入框）
4. `title` / `alt`
5. 以上皆无 → 用标签名（button/input/a…）

## 格式
- `<语义>-<用途>`，全小写下划线/连字符：如 `login-submit`、`username-input`、`order-create-btn`。
- 同文件内重名 → 自动追加 `-2`、`-3`。
- `--prefix` 可加模块前缀：`login-submit` → `uc-login-submit`。

## 唯一性
脚本在**整个扫描范围**内保证 testid 唯一（用全局 used 集合），避免跨页面冲突。

## 团队约定建议
- 存量项目：用本脚本一次性补齐，再纳入规范。
- 新项目：在组件库/规范里要求交互元素默认带 `data-testid`，人工维护即可。
- 禁止用索引、禁止用纯样式 class 当定位依据（见 `qa-ui-kb` 的 selector-rules）。

## 反例
- ❌ `btn1`、`button2` —— 无意义，无法追溯用途。
- ❌ 仅用 CSS `.ant-btn-primary` —— 样式一改就失效。
- ✅ `login-submit`、`search-input`、`pagination-next`。
