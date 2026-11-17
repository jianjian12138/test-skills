#!/usr/bin/env python3
"""Shared Markdown & Table Formatting Utilities for Universal QA Skills."""

from __future__ import annotations


def format_markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    head_line = "| " + " | ".join(headers) + " |"
    sep_line = "| " + " | ".join(":---" for _ in headers) + " |"
    body_lines = ["| " + " | ".join(str(cell) for cell in row) + " |" for row in rows]
    return "\n".join([head_line, sep_line, *body_lines])
