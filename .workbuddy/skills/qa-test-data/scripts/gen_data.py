#!/usr/bin/env python3
"""qa-test-data: 生成测试数据（边界/等价/模糊/PII 脱敏/批量造数）。

解决痛点：手工造数慢、边界易漏、含真实个人信息（PII）泄露风险。
本脚本按字段规格生成边界值与随机数据，并对指定字段脱敏，输出 CSV/JSON。

输入规格（见 references/data-spec.md）：
{
  "rows": 3,
  "seed": 7,
  "fields": [
    {"name":"age","type":"int","min":0,"max":120},
    {"name":"nickname","type":"string","min_len":1,"max_len":20},
    {"name":"phone","type":"phone"},
    {"name":"email","type":"email"}
  ],
  "pii_mask": ["nickname","phone","email"]
}

用法:
    python gen_data.py --input spec.json --outdir <变更>/04-testdata --format csv
"""
import argparse
import csv
import json
import os
import random
import string


def mask_value(value):
    s = str(value)
    if len(s) <= 2:
        return "*" * len(s)
    return s[0] + "*" * (len(s) - 2) + s[-1]


def gen_int(field, rnd):
    lo, hi = field.get("min", 0), field.get("max", 100)
    boundaries = sorted(set([lo, hi, lo - 1, hi + 1, 0]))
    return [b for b in boundaries if isinstance(b, int)]


def gen_string(field, rnd):
    lo, hi = field.get("min_len", 0), field.get("max_len", 10)
    samples = []
    samples.append("")                         # 空
    samples.append("a" * max(lo, 1))           # 最小长度
    samples.append("a" * hi)                   # 最大长度
    samples.append("a" * (hi + 1))             # 超长
    return samples


def gen_phone(rnd):
    return "1" + str(rnd.randint(30, 99)) + "".join(rnd.choice("0123456789") for _ in range(9))


def gen_email(rnd):
    u = "".join(rnd.choice(string.ascii_lowercase) for _ in range(rnd.randint(4, 8)))
    return f"{u}@example.com"


def gen_random_value(field, rnd):
    t = field.get("type", "string")
    if t == "int":
        lo, hi = field.get("min", 0), field.get("max", 100)
        return rnd.randint(lo, hi)
    if t == "phone":
        return gen_phone(rnd)
    if t == "email":
        return gen_email(rnd)
    if t == "enum":
        return rnd.choice(field.get("values", [""]))
    # string
    lo, hi = field.get("min_len", 3), field.get("max_len", 10)
    n = rnd.randint(lo, hi)
    return "".join(rnd.choice(string.ascii_letters + string.digits) for _ in range(n))


def build_spec_rows(spec):
    """为每个字段生成一组候选值（边界优先），再组合成多行。"""
    rnd = random.Random(spec.get("seed"))
    fields = spec.get("fields", [])
    values = {}
    for f in fields:
        t = f.get("type", "string")
        if t == "int":
            values[f["name"]] = [str(v) for v in gen_int(f, rnd)]
        elif t == "string":
            values[f["name"]] = gen_string(f, rnd)
        else:
            # phone/email/enum：随机若干
            n = spec.get("rows", 3)
            values[f["name"]] = [str(gen_random_value(f, rnd)) for _ in range(n)]
    # 行数 = max 候选长度
    rows = max((len(v) for v in values.values()), default=0)
    records = []
    for i in range(rows):
        rec = {}
        for f in fields:
            cand = values[f["name"]]
            rec[f["name"]] = cand[i % len(cand)]
        records.append(rec)
    # PII 脱敏
    for f in fields:
        if f["name"] in spec.get("pii_mask", []):
            for rec in records:
                rec[f["name"]] = mask_value(rec[f["name"]])
    return records


def main():
    ap = argparse.ArgumentParser(description="生成测试数据")
    ap.add_argument("--input", required=True, help="数据规格 JSON")
    ap.add_argument("--outdir", default=".", help="输出目录")
    ap.add_argument("--format", choices=["csv", "json"], default="csv")
    args = ap.parse_args()
    with open(args.input, "r", encoding="utf-8") as f:
        spec = json.load(f)
    records = build_spec_rows(spec)
    os.makedirs(args.outdir, exist_ok=True)
    names = [f["name"] for f in spec.get("fields", [])]
    if args.format == "csv":
        out = os.path.join(args.outdir, "testdata.csv")
        with open(out, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=names)
            w.writeheader()
            w.writerows(records)
    else:
        out = os.path.join(args.outdir, "testdata.json")
        with open(out, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"[ok] 测试数据已生成: {out}  ({len(records)} 行, {len(names)} 字段)")


if __name__ == "__main__":
    main()
