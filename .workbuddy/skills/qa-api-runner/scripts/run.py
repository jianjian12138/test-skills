#!/usr/bin/env python3
"""qa-api-runner 轻量执行器：运行场景文件，输出结果 JSON + Markdown 摘要。

无需 pytest 即可跑；如需 Allure 可视化报告，请用 scripts/test_api.py（pytest + allure-pytest）。

用法:
    python run.py --scenario scenario.json --env-file config/.env --outdir <变更>/06-execution

.env 配置（可选，启用 DB 断言时填写）:
    BASE_URL=https://api.example.com
    DB_ASSERT_ENABLED=false
    DB_HOST=127.0.0.1
    DB_PORT=3306
    DB_USER=test
    DB_PASSWORD=test
    DB_NAME=app
"""
import argparse
import json
import os


def load_env(path):
    env = {}
    if not path or not os.path.exists(path):
        return env
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def build_db_cfg(env):
    if env.get("DB_ASSERT_ENABLED", "false").lower() != "true":
        return None
    return {
        "host": env.get("DB_HOST", "127.0.0.1"),
        "port": int(env.get("DB_PORT", "3306")),
        "user": env.get("DB_USER", ""),
        "password": env.get("DB_PASSWORD", ""),
        "database": env.get("DB_NAME", ""),
    }


def render_report(results, summary, scenario_name):
    lines = [
        f"# 接口自动化执行报告：{scenario_name}",
        "",
        f"- 总数：{summary['total']}　通过：{summary['passed']}　失败：{summary['failed']}",
        f"- 通过率：{summary['passed']/summary['total']*100:.1f}%" if summary['total'] else "",
        "",
        "## 用例结果",
        "",
        "| 用例ID | 名称 | 方法 | 状态 | 失败点 |",
        "|---|---|---|---|---|",
    ]
    for r in results:
        fails = []
        for a in r.get("asserts", []):
            if not a["ok"]:
                fails.append(f"断言 {a['op']}: {a['detail']}")
        for d in r.get("db_asserts", []):
            if not d["ok"]:
                fails.append(f"DB {d.get('op')}: {d['detail']}")
        if r.get("error"):
            fails.append(f"异常: {r['error']}")
        status = "✅通过" if r.get("passed") else "❌失败"
        lines.append(f"| {r.get('id','')} | {r.get('name','')} | {r.get('method','')} | {status} | {'; '.join(fails)} |")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="运行接口自动化场景")
    ap.add_argument("--scenario", required=True, help="场景 JSON 文件")
    ap.add_argument("--env-file", help=".env 配置文件（含 BASE_URL / DB 配置）")
    ap.add_argument("--outdir", default=".", help="结果输出目录")
    args = ap.parse_args()

    with open(args.scenario, "r", encoding="utf-8") as f:
        scenario = json.load(f)
    env = load_env(args.env_file)
    if "BASE_URL" in env and not scenario.get("base_url"):
        scenario["base_url"] = env["BASE_URL"]
    db_cfg = build_db_cfg(env)

    import requests  # 运行期依赖
    from engine import run_scenario

    results, summary, ctx = run_scenario(scenario, db_cfg)

    os.makedirs(args.outdir, exist_ok=True)
    name = os.path.splitext(os.path.basename(args.scenario))[0]
    with open(os.path.join(args.outdir, "results.json"), "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "results": results, "context": ctx}, f, ensure_ascii=False, indent=2)
    report = render_report(results, summary, name)
    with open(os.path.join(args.outdir, "report.md"), "w", encoding="utf-8") as f:
        f.write(report)

    print(f"[ok] 执行完成 通过 {summary['passed']}/{summary['total']}  失败 {summary['failed']}")
    print(f"     结果: {os.path.join(args.outdir,'results.json')}")
    print(f"     报告: {os.path.join(args.outdir,'report.md')}")
    if summary["failed"]:
        print("[warn] 存在失败用例，详见 report.md")


if __name__ == "__main__":
    main()
