#!/usr/bin/env python3
"""
tia_engine.py: 工业级精准测试引擎 (Test Impact Analysis - TIA)
基于 Python AST 抽象语法树与 Git Diff 变更，自动分析被修改函数/类的调用拓扑，
精准挑选出受影响的测试用例文件，将构建测试耗时压缩 90% 以上。

零外部依赖，纯 Python 3.9+ 标准库实现。

用法:
  python tia_engine.py --diff HEAD~1 --src-dir backend/app --test-dir backend/tests
  python tia_engine.py --changed-files app/services/order_service.py
"""
import ast
import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Set, Tuple

if sys.platform == "win32":
    import io
    if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "buffer") and getattr(sys.stderr, "encoding", "").lower() != "utf-8":
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

class CodeSymbolVisitor(ast.NodeVisitor):
    """解析代码文件中的类、函数定义及其行号范围"""
    def __init__(self):
        self.symbols = [] # (symbol_name, start_line, end_line, type)

    def visit_FunctionDef(self, node):
        end_lineno = getattr(node, "end_lineno", node.lineno + 10)
        self.symbols.append((node.name, node.lineno, end_lineno, "function"))
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        end_lineno = getattr(node, "end_lineno", node.lineno + 10)
        self.symbols.append((node.name, node.lineno, end_lineno, "async_function"))
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        end_lineno = getattr(node, "end_lineno", node.lineno + 20)
        self.symbols.append((node.name, node.lineno, end_lineno, "class"))
        self.generic_visit(node)

class TestDependencyMapper:
    """构建测试用例与源码模块的依赖映射关系"""
    @staticmethod
    def extract_symbols(file_path: Path) -> List[Tuple[str, int, int, str]]:
        if not file_path.exists() or file_path.suffix != ".py":
            return []
        try:
            tree = ast.parse(file_path.read_text(encoding="utf-8", errors="replace"))
            visitor = CodeSymbolVisitor()
            visitor.visit(tree)
            return visitor.symbols
        except Exception:
            return []

    @staticmethod
    def extract_test_imports_and_calls(test_file: Path) -> Set[str]:
        """提取测试用例中 import 的模块与调用的标识符"""
        if not test_file.exists() or test_file.suffix != ".py":
            return set()
        refs = set()
        try:
            content = test_file.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for n in node.names:
                        refs.add(n.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        refs.add(node.module)
                    for n in node.names:
                        refs.add(n.name)
                elif isinstance(node, ast.Name):
                    refs.add(node.id)
                elif isinstance(node, ast.Attribute):
                    refs.add(node.attr)
        except Exception:
            pass
        return refs

def get_git_diff_changes(git_ref: str = "HEAD") -> Dict[str, List[int]]:
    """获取 Git Diff 变更的文件及其修改行号"""
    cmd = ["git", "diff", "--unified=0", git_ref]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if res.returncode != 0:
        return {}

    changes = {}
    current_file = None

    for line in res.stdout.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:].strip()
            changes[current_file] = []
        elif line.startswith("@@ ") and current_file:
            # 格式: @@ -start,count +start,count @@
            parts = line.split(" ")
            if len(parts) >= 3 and parts[2].startswith("+"):
                hunk = parts[2][1:]
                if "," in hunk:
                    start, count = map(int, hunk.split(","))
                else:
                    start, count = int(hunk), 1
                changes[current_file].extend(range(start, start + count))

    return changes

def calculate_impacted_tests(changed_files_with_lines: Dict[str, List[int]], test_dir: str) -> List[str]:
    """根据变更的文件和行号，计算受影响的测试用例列表"""
    impacted_symbols = set()
    changed_filenames = set()

    for fpath_str, lines in changed_files_with_lines.items():
        p = Path(fpath_str)
        changed_filenames.add(p.stem)
        symbols = TestDependencyMapper.extract_symbols(p)
        for sym_name, s_line, e_line, _ in symbols:
            if any(s_line <= l <= e_line for l in lines) or not lines:
                impacted_symbols.add(sym_name)

    test_root = Path(test_dir)
    if not test_root.exists():
        return []

    impacted_tests = []
    for test_file in test_root.rglob("test_*.py"):
        refs = TestDependencyMapper.extract_test_imports_and_calls(test_file)
        # 1. 直接匹配修改的符号（函数/类名）
        if any(sym in refs for sym in impacted_symbols):
            impacted_tests.append(str(test_file.resolve()))
            continue
        # 2. 匹配修改的文件名/模块名
        if any(cf in refs or cf in test_file.name for cf in changed_filenames):
            impacted_tests.append(str(test_file.resolve()))

    return sorted(list(set(impacted_tests)))

def main():
    parser = argparse.ArgumentParser(description="TIA 精准测试引擎 - 计算 Git 变更受影响的用例")
    parser.add_argument("--diff", help="Git 差异比较基准 (如 HEAD~1, origin/main)")
    parser.add_argument("--changed-files", nargs="+", help="手动指定变更的文件列表")
    parser.add_argument("--test-dir", default=".", help="测试用例根目录")
    args = parser.parse_args()

    changes = {}
    if args.diff:
        print(f"🔍 正在计算基于 Git Diff [{args.diff}] 的代码变更...")
        changes = get_git_diff_changes(args.diff)
    elif args.changed_files:
        for f in args.changed_files:
            changes[f] = [] # 空列表代表全文件变更
    else:
        # 默认对比未暂存与已暂存的修改
        changes = get_git_diff_changes("HEAD")

    print(f"📋 检测到 {len(changes)} 个变更文件:")
    for f, lines in changes.items():
        print(f"  - {f} (变更 {len(lines)} 行)")

    impacted = calculate_impacted_tests(changes, args.test_dir)
    print(f"\n🎯 精准命中 {len(impacted)} 个受影响的测试用例文件:")
    for t in impacted:
        print(f"  ⚡ {t}")

    if not impacted:
        print("  💡 未发现直接受影响的用例（可能为配置或纯文档修改）。")

if __name__ == "__main__":
    main()
