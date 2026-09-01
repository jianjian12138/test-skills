#!/usr/bin/env python3
"""qa-ui-automation: 从页面描述 JSON 生成 Playwright 页面对象（Page Object）骨架。

为什么：UI 自动化的维护成本在「选择器散落」。把元素集中到 Page Object，页面结构变了
只改一处。本脚本依据 qa-ui-kb 的知识库 / 元素清单，生成可运行的 PO 类与示例用例，
让 AI 生成的脚本从「盲人摸象」变成「看着地图走路」。

输入 JSON（见 references/po-schema.md）：
{
  "base_url": "https://app.example.com",
  "pages": [
    {"name":"LoginPage","route":"/login","elements":[
       {"name":"username","type":"input","testid":"login-username"},
       {"name":"submit","type":"button","testid":"login-submit"}
    ]}
  ]
}

用法:
    python page_object_gen.py --input pages.json --outdir ui_tests
生成：
    ui_tests/pages.py        所有 PO 类
    ui_tests/test_smoke.py   示例冒烟用例（演示串联）
"""
import argparse
import json
import os


PY_HEADER = '''# 自动生成的 Playwright 页面对象（qa-ui-automation）
# 维护：元素集中于此，页面结构变化只改本文件。需 pip install playwright && playwright install
from playwright.sync_api import Page
'''


def method_for(el):
    name = el["name"]
    t = el.get("type", "button")
    testid = el["testid"]
    if t in ("input", "textarea", "select"):
        return (
            f"    def fill_{name}(self, value: str):\n"
            f"        self.page.get_by_test_id(\"{testid}\").fill(value)\n"
        )
    if t == "select":
        return (
            f"    def select_{name}(self, value: str):\n"
            f"        self.page.get_by_test_id(\"{testid}\").select_option(value)\n"
        )
    # button / a / 默认：点击
    return (
        f"    def click_{name}(self):\n"
        f"        self.page.get_by_test_id(\"{testid}\").click()\n"
    )


def gen_pages(data):
    blocks = [PY_HEADER]
    for p in data.get("pages", []):
        cls = p["name"]
        route = p.get("route", "/")
        blocks.append(f"\nclass {cls}:")
        blocks.append(f"    route = \"{route}\"")
        blocks.append(f"    def __init__(self, page: Page):")
        blocks.append(f"        self.page = page")
        blocks.append(f"    def goto(self):")
        blocks.append(f"        self.page.goto(self.route)")
        for el in p.get("elements", []):
            blocks.append("")
            blocks.append(method_for(el))
    return "\n".join(blocks)


def gen_test(data):
    pages = data.get("pages", [])
    first = pages[0]["name"] if pages else "Page"
    return f'''# 示例冒烟用例（qa-ui-automation）
from playwright.sync_api import sync_playwright
from pages import {first}

def test_smoke():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        # 在此串联各页面对象完成业务流；下面仅为占位示例
        target = {first}(page)
        target.goto()
        # target.fill_username("test"); target.click_submit()
        browser.close()
'''


def main():
    ap = argparse.ArgumentParser(description="生成 Playwright 页面对象")
    ap.add_argument("--input", required=True, help="页面描述 JSON")
    ap.add_argument("--outdir", default="ui_tests", help="输出目录")
    args = ap.parse_args()
    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)
    os.makedirs(args.outdir, exist_ok=True)
    with open(os.path.join(args.outdir, "pages.py"), "w", encoding="utf-8") as f:
        f.write(gen_pages(data))
    with open(os.path.join(args.outdir, "test_smoke.py"), "w", encoding="utf-8") as f:
        f.write(gen_test(data))
    print(f"[ok] 页面对象: {os.path.join(args.outdir,'pages.py')}")
    print(f"[ok] 示例用例: {os.path.join(args.outdir,'test_smoke.py')}  (页面数: {len(data.get('pages',[]))})")


if __name__ == "__main__":
    main()
