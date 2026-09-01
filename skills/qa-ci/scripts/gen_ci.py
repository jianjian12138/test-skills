#!/usr/bin/env python3
"""Generate CI/CD pipeline configs (GitHub Actions / GitLab CI / Jenkinsfile).

Usage:
    python scripts/gen_ci.py --config ci.json --outdir ./ci_out
"""
import argparse
import json
import os
import sys


def github_actions(c: dict) -> str:
    py = c.get("python_version", "3.13")
    branches = c.get("branches", ["main"])
    test = c.get("test_cmd", "pytest -q")
    lint = c.get("lint_cmd", "flake8 .")
    sec = c.get("security_cmd", "semgrep --config auto")
    timeout = c.get("timeout_min", 30)
    services_block = ""
    if c.get("services"):
        svcs = "\n".join(f"      {s}:\n        image: {s}:latest" for s in c["services"])
        services_block = f"    services:\n{svcs}\n"
    br = "\n".join(f"      - {b}" for b in branches)
    return f"""name: QA

on:
  push:
    branches:
{br}
  pull_request:
    branches:
{br}

jobs:
  qa:
    runs-on: ubuntu-latest
    timeout-minutes: {timeout}
{services_block}    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "{py}"
      - name: Install
        run: pip install -r requirements.txt || true
      - name: Lint
        run: {lint}
      - name: Test
        run: {test}
      - name: Security
        run: {sec}
"""


def jenkinsfile(c: dict) -> str:
    py = c.get("python_version", "3.13")
    test = c.get("test_cmd", "pytest -q")
    lint = c.get("lint_cmd", "flake8 .")
    sec = c.get("security_cmd", "semgrep --config auto")
    return f"""pipeline {{
    agent any
    tools {{ python "{py}" }}
    stages {{
        stage('Install') {{
            steps {{ sh 'pip install -r requirements.txt || true' }}
        }}
        stage('Lint') {{
            steps {{ sh '{lint}' }}
        }}
        stage('Test') {{
            steps {{ sh '{test}' }}
        }}
        stage('Security') {{
            steps {{ sh '{sec}' }}
        }}
    }}
}}
"""


def render_gitlab(c: dict) -> str:
    # gitlab_ci above had a stray expression; rebuild cleanly
    py = c.get("python_version", "3.13")
    test = c.get("test_cmd", "pytest -q")
    lint = c.get("lint_cmd", "flake8 .")
    sec = c.get("security_cmd", "semgrep --config auto")
    services = c.get("services", [])
    svc_block = ""
    if services:
        svc_block = "services:\n" + "\n".join(f"  {s}:\n    image: {s}:latest" for s in services) + "\n"
    return f"""stages:
  - qa

image: python:{py}

{svc_block}lint:
  stage: qa
  script:
    - pip install -r requirements.txt || true
    - {lint}

test:
  stage: qa
  script:
    - pip install -r requirements.txt || true
    - {test}

security:
  stage: qa
  script:
    - {sec}
"""


GENERATORS = {
    "github": (".github/workflows/qa.yml", github_actions),
    "gitlab": (".gitlab-ci.yml", render_gitlab),
    "jenkins": ("Jenkinsfile", jenkinsfile),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()
    try:
        with open(args.config, "r", encoding="utf-8") as f:
            c = json.load(f)
    except Exception as e:
        print(f"[ERROR] 读取 config 失败: {e}", file=sys.stderr)
        return 2

    providers = c.get("providers", ["github"])
    os.makedirs(args.outdir, exist_ok=True)
    written = []
    for p in providers:
        if p not in GENERATORS:
            print(f"[WARN] 未知 provider: {p}，跳过")
            continue
        rel, fn = GENERATORS[p]
        content = fn(c)
        full = os.path.join(args.outdir, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)
        written.append(full)
    if not written:
        print("[ERROR] 未生成任何文件，检查 providers", file=sys.stderr)
        return 2
    print("[OK] 已生成 CI 配置：" + ", ".join(written))
    return 0


if __name__ == "__main__":
    sys.exit(main())
