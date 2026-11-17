#!/usr/bin/env python3
"""Hybrid Static (Python AST) + Dynamic (coverage.py SQLite Context) Test Impact Analysis Engine."""

from __future__ import annotations

import ast
import re
import sqlite3
import subprocess
from pathlib import Path
from typing import Any

from .router import get_trace_id


def parse_unified_diff_lines(diff_text: str) -> dict[str, set[int]]:
    """Extract modified target file paths and exact modified line numbers from unified git diff."""
    changed: dict[str, set[int]] = {}
    current_file: str | None = None
    current_line = 0

    for raw_line in diff_text.splitlines():
        if raw_line.startswith("+++ b/"):
            current_file = raw_line[6:].strip()
            changed.setdefault(current_file, set())
        elif raw_line.startswith("@@ ") and current_file:
            m = re.search(r"\+(\d+)(?:,(\d+))?", raw_line)
            if m:
                current_line = int(m.group(1))
        elif current_file and not raw_line.startswith("---"):
            if raw_line.startswith("+") and not raw_line.startswith("+++"):
                changed[current_file].add(current_line)
                current_line += 1
            elif raw_line.startswith(" "):
                current_line += 1
    return changed


def analyze_static_ast_call_graph(repo_root: Path, changed_files: dict[str, set[int]]) -> dict[str, Any]:
    """Parse Python AST in repo to map modified functions/classes to test files."""
    modified_symbols: set[str] = set()
    impacted_tests: set[str] = set()

    for rel_path, lines in changed_files.items():
        full_path = repo_root / rel_path
        if not full_path.exists() or full_path.suffix != ".py":
            continue
        try:
            tree = ast.parse(full_path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                start = getattr(node, "lineno", 0)
                end = getattr(node, "end_lineno", start + 15)
                if not lines or any(start <= ln <= end for ln in lines):
                    modified_symbols.add(node.name)

    # Scan test files for references to modified symbols or modules
    test_dir = repo_root / "tests"
    test_files = list(test_dir.rglob("test_*.py")) if test_dir.exists() else list(repo_root.rglob("test_*.py"))
    for tf in test_files:
        try:
            src = tf.read_text(encoding="utf-8")
            tree = ast.parse(src)
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                segment = ast.get_source_segment(src, node) or ""
                if any(sym in segment for sym in modified_symbols) or not modified_symbols:
                    rel_tf = tf.relative_to(repo_root).as_posix()
                    impacted_tests.add(f"{rel_tf}::{node.name}")

    return {
        "modified_symbols": sorted(modified_symbols),
        "static_impacted_tests": sorted(impacted_tests),
    }


def query_dynamic_coverage_contexts(cov_db_path: Path, changed_files: dict[str, set[int]]) -> list[str]:
    """Query coverage.py SQLite database (or context table) to resolve exact runtime test contexts."""
    if not cov_db_path.exists():
        return []
    impacted: set[str] = set()
    try:
        db_handle = sqlite3.connect(str(cov_db_path))
        cursor = db_handle.cursor()
        tables = {r[0] for r in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}

        if {"file", "context", "line_map"}.issubset(tables):
            for rel_path, lines in changed_files.items():
                rows = cursor.execute(
                    "SELECT context.context, line_map.lines FROM line_map "
                    "JOIN file ON line_map.file_id = file.id "
                    "JOIN context ON line_map.context_id = context.id "
                    "WHERE file.path LIKE ?",
                    (f"%{rel_path}",),
                ).fetchall()
                for ctx_name, lines_csv in rows:
                    covered_lines = {int(x) for x in str(lines_csv).split(",") if x.strip().isdigit()}
                    if not lines or (covered_lines & lines):
                        if ctx_name and ctx_name != "":
                            impacted.add(str(ctx_name))
        elif {"file", "context", "line_bits"}.issubset(tables):
            for rel_path, lines in changed_files.items():
                rows = cursor.execute(
                    "SELECT context.context, line_bits.numbits FROM line_bits "
                    "JOIN file ON line_bits.file_id = file.id "
                    "JOIN context ON line_bits.context_id = context.id "
                    "WHERE file.path LIKE ?",
                    (f"%{rel_path}",),
                ).fetchall()
                for ctx_name, numbits in rows:
                    if not ctx_name:
                        continue
                    if isinstance(numbits, (bytes, bytearray)):
                        covered = set()
                        for byte_idx, byte_val in enumerate(numbits):
                            for bit_idx in range(8):
                                if byte_val & (1 << bit_idx):
                                    covered.add(byte_idx * 8 + bit_idx)
                        if not lines or (covered & lines):
                            impacted.add(str(ctx_name))
        db_handle.close()
    except Exception:
        return []
    return sorted(impacted)


def run_hybrid_tia(
    repo_root: Path | None = None,
    diff_target: str = "HEAD~1",
    raw_diff_override: str | None = None,
    cov_db_path: Path | None = None,
) -> dict[str, Any]:
    """Execute L6.0 Hybrid Static-Dynamic Test Impact Analysis."""
    root = repo_root or Path(__file__).resolve().parents[2]
    cov_db = cov_db_path or (root / ".coverage")

    if raw_diff_override is not None:
        diff_text = raw_diff_override
    else:
        try:
            proc = subprocess.run(
                ["git", "diff", diff_target, "--unified=0"],
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            diff_text = proc.stdout or ""
        except Exception:
            diff_text = ""

    changed_files = parse_unified_diff_lines(diff_text)
    if not changed_files:
        # Fallback synthetic diff on router.py for zero-git demo environments
        changed_files = {"skills/tools/router.py": {58, 59, 60}}

    static_res = analyze_static_ast_call_graph(root, changed_files)
    dynamic_tests = query_dynamic_coverage_contexts(cov_db, changed_files)

    merged_tests = sorted(set(static_res["static_impacted_tests"]) | set(dynamic_tests))
    engine_mode = "HYBRID_AST_PLUS_COVERAGE_SQLITE" if dynamic_tests else "STATIC_AST_FALLBACK"
    blast_radius = min(100.0, round(len(changed_files) * 18.5 + len(merged_tests) * 8.2, 1))

    return {
        "trace_id": get_trace_id(),
        "engine_mode": engine_mode,
        "changed_files": {k: sorted(v) for k, v in changed_files.items()},
        "modified_symbols": static_res["modified_symbols"],
        "static_ast_tests": static_res["static_impacted_tests"],
        "dynamic_coverage_tests": dynamic_tests,
        "recommended_tests": merged_tests,
        "blast_radius_score": blast_radius,
        "pytest_command": f"pytest {' '.join(merged_tests)}" if merged_tests else "pytest tests/test_v12_suite.py",
    }
