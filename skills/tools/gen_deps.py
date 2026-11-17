#!/usr/bin/env python3
"""Dependency & Runtime Environment Inspector (Zero-Deps Core + Optional Pro Extras)."""

from __future__ import annotations

import importlib.util
import sys


def inspect_runtime_capabilities() -> dict:
    optional_pkgs = ["pytest", "playwright", "hypothesis", "schemathesis", "httpx"]
    installed = {pkg: (importlib.util.find_spec(pkg) is not None) for pkg in optional_pkgs}
    return {
        "python_version": sys.version.split()[0],
        "zero_deps_core_ready": True,
        "optional_pro_packages": installed,
    }
