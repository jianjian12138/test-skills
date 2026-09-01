#!/usr/bin/env python3
"""qa-api-doc: 从 Swagger / OpenAPI 拉取接口信息，输出标准化 Markdown 接口文档。

解决痛点：手动从 Swagger 复制接口易错、接口一更新就得重抄。
本脚本动态拉取最新 OpenAPI JSON（支持 Bearer / Basic 鉴权），转成 AI 可直接解析的
Markdown；同时可保存原始 JSON 供后续用例生成 / 自动化使用。

用法:
    # 从 URL 拉取（Bearer 鉴权）
    python swagger_fetch.py --url https://api.example.com/v3/api-docs \
        --token "<JWT>" --output api-doc.md --save-json api-doc.json

    # 从本地 JSON 文件解析
    python swagger_fetch.py --file openapi.json --output api-doc.md

    # 只看某些路径（按关键字过滤）
    python swagger_fetch.py --url ... --filter "user,order"
"""
import argparse
import json
import sys
import urllib.request
import urllib.error


def fetch_json(url, token=None, username=None, password=None):
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    if username and password:
        import base64
        cred = base64.b64encode(f"{username}:{password}".encode()).decode()
        req.add_header("Authorization", f"Basic {cred}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def simplify_schema(schema, depth=0, max_depth=4):
    """把 OpenAPI schema 递归简化为可读文本。"""
    if depth > max_depth or not isinstance(schema, dict):
        return schema if not isinstance(schema, dict) else "{...}"
    if "properties" in schema:
        out = {}
        for name, prop in schema["properties"].items():
            ptype = prop.get("type", prop.get("$ref", "object"))
            req = "必填" if name in schema.get("required", []) else "可选"
            desc = prop.get("description", "")
            out[name] = f"{ptype}（{req}）{('：' + desc) if desc else ''}"
            if prop.get("type") == "object" or "$ref" in prop:
                out[name] += " " + str(simplify_schema(prop, depth + 1, max_depth))
        return out
    if "$ref" in schema:
        return schema["$ref"].split("/")[-1]
    return schema.get("type", "object")


def render(openapi):
    info = openapi.get("info", {})
    paths = openapi.get("paths", {})
    version = openapi.get("openapi") or openapi.get("swagger") or "未知"
    lines = [
        f"# 接口文档（自动生成）",
        f"- 标题：{info.get('title', '-')}",
        f"- 版本：{info.get('version', '-')}  | OpenAPI/Swagger：{version}",
        f"- 接口总数：{sum(len(methods) for methods in paths.values())}",
        "",
        "## 接口清单",
        "",
    ]
    for path, methods in paths.items():
        for method, spec in methods.items():
            if method.lower() not in ("get", "post", "put", "delete", "patch"):
                continue
            summary = spec.get("summary") or spec.get("description") or ""
            lines.append(f"### `{method.upper()} {path}`")
            if summary:
                lines.append(f"- 说明：{summary}")
            # 参数
            params = spec.get("parameters", [])
            if params:
                lines.append("- 参数：")
                for p in params:
                    req = "必填" if p.get("required") else "可选"
                    lines.append(f"  - `{p.get('name')}` ({p.get('in')}, {req})：{p.get('description','')}")
            # 请求体
            rb = spec.get("requestBody")
            if rb:
                content = rb.get("content", {})
                schema = None
                for ct, cv in content.items():
                    schema = cv.get("schema")
                    break
                if schema:
                    lines.append("- 请求体：")
                    simplified = simplify_schema(schema)
                    if isinstance(simplified, dict):
                        for k, v in simplified.items():
                            lines.append(f"  - {k}：{v}")
                    else:
                        lines.append(f"  - {simplified}")
            # 响应
            resp = spec.get("responses", {})
            if resp:
                lines.append("- 主要响应：")
                for code, r in resp.items():
                    lines.append(f"  - `{code}`：{r.get('description','')}")
            lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Swagger/OpenAPI → Markdown 接口文档")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--url", help="OpenAPI JSON 地址")
    src.add_argument("--file", help="本地 OpenAPI JSON 文件")
    ap.add_argument("--token", help="Bearer Token")
    ap.add_argument("--username", help="Basic 用户名")
    ap.add_argument("--password", help="Basic 密码")
    ap.add_argument("--output", default="api-doc.md", help="Markdown 输出路径")
    ap.add_argument("--save-json", help="同时保存原始 JSON 的路径")
    ap.add_argument("--filter", help="按路径关键字过滤，逗号分隔")
    args = ap.parse_args()

    try:
        if args.url:
            data = fetch_json(args.url, args.token, args.username, args.password)
        else:
            with open(args.file, "r", encoding="utf-8") as f:
                data = json.load(f)
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError) as e:
        print(f"[error] 拉取/解析失败：{e}", file=sys.stderr)
        sys.exit(1)

    if args.filter:
        keys = [k.strip() for k in args.filter.split(",") if k.strip()]
        filtered = {p: m for p, m in data.get("paths", {}).items()
                    if any(k in p for k in keys)}
        data["paths"] = filtered

    md = render(data)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(md)
    if args.save_json:
        with open(args.save_json, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[ok] 接口文档已生成: {args.output}")
    print(f"      接口数: {sum(len(m) for m in data.get('paths',{}).values())}")


if __name__ == "__main__":
    main()
