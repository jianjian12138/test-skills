#!/usr/bin/env python3
"""qa-api-runner 的 pytest + Allure 集成（可选）。

仅在安装了 pytest、requests、allure-pytest 后使用，产出可视化 Allure 报告：
    pip install pytest requests allure-pytest
    export QA_SCENARIO=scenario.json
    export QA_ENV_FILE=config/.env
    pytest test_api.py --alluredir=allure-results
    allure serve allure-results

若未安装 allure，本文件仍可被 pytest 运行（已做降级）。
"""
import os
import json


try:
    import allure
except ImportError:
    class _AllureShim:
        def feature(self, *a, **k):
            def d(f): return f
            return d
        def step(self, name):
            class _C:
                def __enter__(self): return self
                def __exit__(self, *a): return False
            return _C()
    allure = _AllureShim()


SCENARIO = os.environ.get("QA_SCENARIO", "scenario.json")
ENV_FILE = os.environ.get("QA_ENV_FILE")


def _load_env(path):
    env = {}
    if not path or not os.path.exists(path):
        return env
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def _build_db_cfg(env):
    if env.get("DB_ASSERT_ENABLED", "false").lower() != "true":
        return None
    return {
        "host": env.get("DB_HOST", "127.0.0.1"),
        "port": int(env.get("DB_PORT", "3306")),
        "user": env.get("DB_USER", ""),
        "password": env.get("DB_PASSWORD", ""),
        "database": env.get("DB_NAME", ""),
    }


def _fail_msg(r):
    msgs = []
    for a in r.get("asserts", []):
        if not a["ok"]:
            msgs.append(f"断言 {a['op']}: {a['detail']}")
    for d in r.get("db_asserts", []):
        if not d["ok"]:
            msgs.append(f"DB {d.get('op')}: {d['detail']}")
    if r.get("error"):
        msgs.append(f"异常: {r['error']}")
    return "; ".join(msgs) or "失败"


@allure.feature("接口自动化")
def test_api_scenario():
    import requests  # 运行期
    from engine import run_scenario
    with open(SCENARIO, encoding="utf-8") as f:
        scenario = json.load(f)
    env = _load_env(ENV_FILE)
    if "BASE_URL" in env and not scenario.get("base_url"):
        scenario["base_url"] = env["BASE_URL"]
    db_cfg = _build_db_cfg(env)
    results, summary, _ = run_scenario(scenario, db_cfg)
    for r in results:
        with allure.step(f"{r.get('id','')} {r.get('name','')} [{r.get('method','')}] -> {r.get('url','')}"):
            assert r.get("passed"), _fail_msg(r)
