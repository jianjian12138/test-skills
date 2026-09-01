#!/usr/bin/env python3
"""qa-code-review: 代码评审启发式门禁（轻量 linter）。
纯标准库扫描源码，识别评审期高危反模式：硬编码密钥(critical/blocking)、SQL 拼接(high)、
超长函数(high)、无单的 TODO/FIXME(medium)、遗留调试打印(low)。
诚实边界：本技能是启发式静态检查，不是完整 SAST（不理解语义/数据流）；与 qa-security-scan 互补。
"""
import argparse
import os
import re
import sys

try:
    from _common import emit_signal, read_text
except ImportError as _imp_err:
    import sys as _sys
    _sys.stderr.write(
        "FATAL: _common.py 缺失/损坏，技能不可用（fail-closed）\n")
    _sys.exit(2)


EXTS = {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rb", ".php", ".cs"}
FUNC_RE = re.compile(r'^\s*(def\s+\w+|function\s+\w+|\w+\s*\([^)]*\)\s*\{|\w+\s*=>|func\s+\w+|public\s+\w+\s+\w+\s*\()')
SECRET_RE = re.compile(r'(?i)(password|passwd|pwd|secret|api[_-]?key|token|access[_-]?key)\s*[:=]\s*["\'][^"\']{6,}["\']')
SQLCONCAT_RE = re.compile(r'(?i)(select|insert|update|delete)\s+[\w\*,\s\(\)\.=`\'"]+(\+|\%|\.format|f["\'])')
TODO_RE = re.compile(r'(?i)\b(TODO|FIXME|XXX)\b\s*(?!(\(#?\d+\)?|#\d+))')
DEBUG_RE = re.compile(r'(?i)\b(print|console\.log|debugger)\s*\(')
# 抑制注释：行尾 `# nosec` / `# noqa`（可带原因），与 Bandit/flake8 约定一致
SUPPRESS_RE = re.compile(r'#\s*(nosec|noqa)\b')


def scan_file(path, max_func_len):
    findings = []
    text = read_text(path)
    lines = text.splitlines()
    for i, ln in enumerate(lines, 1):
        if SUPPRESS_RE.search(ln):
            continue  # 整行被安全审查/风格工具抑制，跳过启发式告警
        if SECRET_RE.search(ln):
            findings.append({"file": os.path.basename(path), "line": i, "severity": "critical",
                             "rule": "CR-HARDCODED-SECRET", "detail": "疑似硬编码密钥/凭据: " + ln.strip()[:80]})
        if SQLCONCAT_RE.search(ln):
            findings.append({"file": os.path.basename(path), "line": i, "severity": "high",
                             "rule": "CR-SQL-CONCAT", "detail": "疑似 SQL 字符串拼接: " + ln.strip()[:80]})
        if TODO_RE.search(ln):
            findings.append({"file": os.path.basename(path), "line": i, "severity": "medium",
                             "rule": "CR-TODO-NO-TICKET", "detail": "TODO/FIXME 未关联工单: " + ln.strip()[:80]})
        if DEBUG_RE.search(ln):
            findings.append({"file": os.path.basename(path), "line": i, "severity": "low",
                             "rule": "CR-DEBUG-PRINT", "detail": "遗留调试打印: " + ln.strip()[:80]})
    # 超长函数启发式
    decl_lines = [i for i, ln in enumerate(lines) if FUNC_RE.match(ln)]
    for idx, start in enumerate(decl_lines):
        end = decl_lines[idx + 1] if idx + 1 < len(decl_lines) else len(lines)
        span = end - start
        if span > max_func_len:
            findings.append({"file": os.path.basename(path), "line": start + 1, "severity": "high",
                             "rule": "CR-LONG-FUNC", "detail": "函数/方法过长({} 行 > {})".format(span, max_func_len)})
    return findings


def collect_files(src):
    if os.path.isfile(src):
        return [src] if os.path.splitext(src)[1] in EXTS else []
    out = []
    for root, _, files in os.walk(src):
        for f in files:
            if os.path.splitext(f)[1] in EXTS:
                out.append(os.path.join(root, f))
    return sorted(out)


def main():
    ap = argparse.ArgumentParser(description="代码评审启发式门禁")
    ap.add_argument("--src", required=True, help="源码文件或目录")
    ap.add_argument("--out", required=True, help="signals/ 输出目录")
    ap.add_argument("--max-func-len", type=int, default=80)
    ap.add_argument("--fail-on", action="store_true", help="存在评审阻断项(硬编码密钥)时 sys.exit(1)")
    args = ap.parse_args()
    # AR-01：--out 绝对化，确保信号落点不依赖调用方 CWD（fail-closed 确定性）。
    args.out = os.path.abspath(args.out)

    files = collect_files(args.src)
    findings = []
    for fp in files:
        findings.extend(scan_file(fp, args.max_func_len))

    blocking = [f for f in findings if f["severity"] == "critical"]
    if blocking:
        emit_signal("qa-code-review", [{
            "signal": "code_review_blocker",
            "severity": "critical",
            "count": len(blocking),
            "blocking": True,
            "detail": "{} 处评审阻断项(硬编码密钥等)".format(len(blocking)),
        }], args.out)
        print("qa-code-review: BLOCKING — {} blockers".format(len(blocking)))
        if args.fail_on:
            sys.exit(1)
    elif findings:
        emit_signal("qa-code-review", [{
            "signal": "code_review_findings",
            "severity": "high",
            "count": len(findings),
            "blocking": False,
            "detail": "{} 条待处理项(非阻断)".format(len(findings)),
        }], args.out)
        print("qa-code-review: OK — findings={}".format(len(findings)))
    else:
        print("qa-code-review: OK — 无评审阻断项")
    sys.exit(0)


if __name__ == "__main__":
    main()
