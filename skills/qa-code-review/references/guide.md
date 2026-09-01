# 代码评审扫描指南 — qa-code-review

## 1. 目的
纯标准库静态扫描源码，在评审期拦下高危反模式，不替代人工 Code Review，而是把「一眼就能看出的雷」先排掉。

## 2. 严重级与阻断
| 反模式 | severity | blocking |
|---|---|---|
| 硬编码密钥/令牌 | critical | ✅ |
| SQL 字符串拼接 | high | ❌ |
| 函数过长（>`--max-func-len`） | medium | ❌ |
| 其他代码异味 | low | ❌ |

- 仅 `critical`（硬编码密钥）触发 `blocking=true` 信号。

## 3. CLI 约定
```bash
python qa-code-review/scripts/review_scan.py --src src/ --out signals --fail-on
# 可选：--max-func-len 80 （默认 80 行）
```

## 4. 误报抑制
- 在疑似密钥行尾加 `# nosec`，扫描器跳过该行（用于测试用 dummy token、文档示例）。
- 示例：`TOKEN = "test_dummy_xxx"  # nosec`

## 5. 常见坑
- 仅做**正则级**识别，无法理解上下文：变量名含 `key`/`secret` 但实为普通字符串可能误报，用 `# nosec` 标注。
- 不解析语法树，跨文件的数据流/污点传播不在范围。
