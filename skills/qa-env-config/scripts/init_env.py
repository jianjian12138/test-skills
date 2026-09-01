#!/usr/bin/env python3
"""qa-env-config: 为多环境测试脚手架生成配置模板。

解决痛点：接口/UI 自动化里环境地址、账号、token、DB 散落在代码或聊天里，切换环境
改一处漏一处，敏感信息易泄露。本脚本生成 config/ 目录与分环境 .env 模板，约定
「配置与代码分离、环境只改一个文件」。

用法:
    python init_env.py --outdir <变更>/06-execution/config --envs dev,test,staging
生成：
    config/.env.example       通用模板（提交到仓库，不含真实值）
    config/.env.dev           dev 环境（含占位，填写后勿提交）
    config/.env.test
    config/.env.staging
"""
import argparse
import os

TEMPLATE = """# 环境配置模板（qa-env-config）
# 说明：本文件可提交仓库；真实密钥请填到对应 .env.<env>，并加入 .gitignore

# 接口/UI 基地址
BASE_URL=

# 测试账号
TEST_USER=
TEST_PASSWORD=

# 鉴权（登录后注入；或直填 token）
AUTH_TOKEN=

# 数据库断言（接口+数据双校验，可选）
DB_ASSERT_ENABLED=false
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=
DB_PASSWORD=
DB_NAME=

# 超时（秒）
TIMEOUT=30
"""


def main():
    ap = argparse.ArgumentParser(description="生成多环境配置模板")
    ap.add_argument("--outdir", default="config", help="配置输出目录")
    ap.add_argument("--envs", default="dev,test,staging", help="环境列表，逗号分隔")
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    with open(os.path.join(args.outdir, ".env.example"), "w", encoding="utf-8") as f:
        f.write(TEMPLATE)
    print(f"[ok] 通用模板: {os.path.join(args.outdir,'.env.example')}")
    for env in [e.strip() for e in args.envs.split(",") if e.strip()]:
        path = os.path.join(args.outdir, f".env.{env}")
        header = f"# 环境：{env}（含真实值，勿提交；建议加入 .gitignore）\n\n"
        with open(path, "w", encoding="utf-8") as f:
            f.write(header + TEMPLATE)
        print(f"[ok] {env} 环境: {path}")
    print("\n[info] 在对应 .env.<env> 填真实值；运行时通过 --env-file 指向它。")


if __name__ == "__main__":
    main()
