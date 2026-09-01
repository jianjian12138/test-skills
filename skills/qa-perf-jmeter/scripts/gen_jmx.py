#!/usr/bin/env python3
"""Generate a JMeter .jmx test plan from a qa-perf-design scenario JSON.

Usage:
    python scripts/gen_jmx.py --scenarios scenario.json --out plan.jmx
    python scripts/gen_jmx.py --scenarios scenario.json --out plan.jmx \
        --data-csv data.csv --threads-cap 1000

Mirrors the qa-perf-design / qa-perf-locust scenario schema so Locust and JMeter
are interchangeable downstream.

Produces:
  - one ThreadGroup per scenario (users -> num_threads, spawn_rate -> ramp_time,
    duration -> scheduler duration)
  - each endpoint wrapped in a Throughput Controller weighted by `weight`
  - HTTP Header Manager (Content-Type/json), Constant Timer (think_time)
  - Aggregate Report + Summary Report listeners at TestPlan level
"""
import argparse
import json
import sys
import xml.etree.ElementTree as ET
from urllib.parse import urlparse


# ---------- JMX tree builder ----------
def add(parent, tag, attrib=None, text=None, props=None, bools=None, elements=None,
        children=None):
    """Append an element + a sibling <hashTree> holding its children (JMeter convention)."""
    e = ET.SubElement(parent, tag, attrib or {})
    if text is not None:
        e.text = str(text)
    for name, val in (props or []):
        sp = ET.SubElement(e, "stringProp", {"name": name})
        sp.text = val
    for name, val in (bools or []):
        bp = ET.SubElement(e, "boolProp", {"name": name})
        bp.text = "true" if val else "false"
    for name, child_tag, child_attrib in (elements or []):
        ET.SubElement(e, child_tag, {"name": name, **(child_attrib or {})})
    ht = ET.SubElement(parent, "hashTree")
    for c in (children or []):
        add(ht, **c)
    return e


def http_sampler(name, method, path, body=None, headers=None):
    children = []
    arg_children = []
    if body is not None:
        arg_children.append({
            "tag": "elementProp",
            "attrib": {"name": "", "elementType": "HTTPArgument"},
            "bools": [("HTTPArgument.always_encode", False), ("HTTPArgument.use_equals", True)],
            "props": [("Argument.value", body), ("Argument.metadata", "="), ("Argument.name", "")],
        })
    sampler = {
        "tag": "HTTPSamplerProxy",
        "attrib": {"guiclass": "HttpTestSampleGui", "testclass": "HTTPSamplerProxy",
                   "testname": name, "enabled": "true"},
        "props": [
            ("HTTPSampler.path", path),
            ("HTTPSampler.method", method.upper()),
            ("HTTPSampler.protocol", ""),
            ("HTTPSampler.domain", ""),
            ("HTTPSampler.port", ""),
            ("HTTPSampler.contentEncoding", ""),
            ("HTTPSampler.implementation", "HttpClient4"),
        ],
        "bools": [("HTTPSampler.postBodyRaw", body is not None)],
        "elements": [("HTTPsampler.Arguments", "Arguments",
                      {"guiclass": "HTTPArgumentsPanel", "testclass": "Arguments",
                       "testname": "用户定义的变量", "enabled": "true"})],
        "children": [{
            "tag": "collectionProp",
            "attrib": {"name": "Arguments.arguments"},
            "children": arg_children,
        }],
    }
    return sampler


def throughput_controller(name, percent):
    return {
        "tag": "ThroughputController",
        "attrib": {"guiclass": "ThroughputControllerGui", "testclass": "ThroughputController",
                   "testname": name, "enabled": "true"},
        "props": [],
        "bools": [("ThroughputController.perThread", False)],
        "elements": [
            ("ThroughputController.style", "intProp", {"name": "ThroughputController.style"}),
        ],
        # style=1 (percent), percentThroughput
        "children": [
            {"tag": "floatProp", "attrib": {"name": "ThroughputController.percentThroughput"},
             "text": f"{percent:.2f}"},
            {"tag": "intProp", "attrib": {"name": "ThroughputController.maxThroughput"}, "text": "0"},
        ],
    }


def build_thread_group(scn, base_parsed):
    users = int(scn.get("users", 1))
    spawn_rate = scn.get("spawn_rate") or users
    duration = int(scn.get("duration", 60))
    ramp = max(1, round(users / spawn_rate)) if spawn_rate else users
    think = float(scn.get("think_time", 0) or 0)
    endpoints_keys = scn.get("endpoints", [])
    raw_endpoints = base_parsed.get("endpoints", {})

    # weights
    weights = [float(raw_endpoints.get(k, {}).get("weight", 1) or 1) for k in endpoints_keys]
    total_w = sum(weights) or 1.0

    children = []
    # header manager (ThreadGroup level)
    children.append({
        "tag": "HeaderManager",
        "attrib": {"guiclass": "HeaderPanel", "testclass": "HeaderManager",
                   "testname": "HTTP Header Manager", "enabled": "true"},
        "children": [{
            "tag": "collectionProp",
            "attrib": {"name": "HeaderManager.headers"},
            "children": [{
                "tag": "elementProp",
                "attrib": {"name": "", "elementType": "Header"},
                "props": [("Header.name", "Content-Type"), ("Header.value", "application/json")],
            }],
        }],
    })
    # throughput controllers per endpoint
    for k, w in zip(endpoints_keys, weights):
        ep = raw_endpoints.get(k, {})
        method = ep.get("method", "GET")
        path = ep.get("path", "/")
        body = ep.get("json")
        if body is not None:
            body = json.dumps(body, ensure_ascii=False)
        # substitute {var} -> ${var} for JMeter
        path = _tmpl(path)
        if body:
            body = _tmpl(body)
        sampler = http_sampler(k, method, path, body)
        percent = w / total_w * 100.0
        tc = throughput_controller(f"TC_{k}", percent)
        # wrap sampler inside tc
        tc_wrap = dict(tc)
        # rebuild children: tc holds the sampler
        tc_wrap["children"] = tc.get("children", []) + [sampler]
        children.append(tc_wrap)
    # constant timer for think_time
    if think > 0:
        children.append({
            "tag": "ConstantTimer",
            "attrib": {"guiclass": "ConstantTimerGui", "testclass": "ConstantTimer",
                       "testname": "Think Time", "enabled": "true"},
            "props": [("ConstantTimer.delay", str(int(think * 1000)))],
        })

    tg = {
        "tag": "ThreadGroup",
        "attrib": {"guiclass": "ThreadGroupGui", "testclass": "ThreadGroup",
                   "testname": scn.get("name", "scenario"), "enabled": "true"},
        "props": [
            ("ThreadGroup.num_threads", str(users)),
            ("ThreadGroup.ramp_time", str(ramp)),
            ("ThreadGroup.duration", str(duration)),
            ("ThreadGroup.delay", "0"),
            ("ThreadGroup.on_sample_error", "continue"),
        ],
        "bools": [("ThreadGroup.scheduler", True), ("ThreadGroup.delayedStart", False)],
        "children": children,
    }
    return tg


def build_test_plan(scenarios, base_parsed, data_csv):
    root = ET.Element("jmeterTestPlan", {
        "version": "1.2", "properties": "5.0", "jmeter": "5.6.3",
        "xmlns": "http://jakarta.ee/xml/ns/jakartaee",
    })
    top_ht = ET.SubElement(root, "hashTree")
    tp = {
        "tag": "TestPlan",
        "attrib": {"guiclass": "TestPlanGui", "testclass": "TestPlan",
                   "testname": "QA Perf Plan (generated)", "enabled": "true"},
        "props": [("TestPlan.comments", "Generated by qa-perf-jmeter from qa-perf-design scenario."),
                  ("TestPlan.teardown_on_shutdown", "true"),
                  ("TestPlan.serialize_threadgroups", "false")],
        "bools": [("TestPlan.functional_mode", False), ("TestPlan.stop_threads_on_error", False)],
        "elements": [("TestPlan.user_defined_variables", "Arguments",
                      {"guiclass": "ArgumentsPanel", "testclass": "Arguments",
                       "testname": "用户定义变量", "enabled": "true"})],
        "children": [],
    }
    add(top_ht, **tp)

    # optional CSV Data Set Config at plan level
    if data_csv:
        csv_node = {
            "tag": "CSVDataSet",
            "attrib": {"guiclass": "TestBeanGUI", "testclass": "CSVDataSet",
                       "testname": "CSV Data Set Config", "enabled": "true"},
            "props": [
                ("filename", data_csv),
                ("fileEncoding", "UTF-8"),
                ("variableNames", ""),
                ("delimiter", ","),
                ("ignoreFirstLine", "true"),
                ("recycle", "true"),
                ("stopThread", "false"),
                ("shareMode", "shareMode.all"),
            ],
            "bools": [("quotedData", False)],
        }
        add(top_ht, **csv_node)

    # thread groups
    for scn in scenarios:
        tg = build_thread_group(scn, base_parsed)
        add(top_ht, **tg)

    # listeners (plan level): Aggregate + Summary report
    for name, gui in [("Aggregate Report", "StatVisualizer"), ("Summary Report", "SummaryReport")]:
        add(top_ht, **{
            "tag": "ResultCollector",
            "attrib": {"guiclass": gui, "testclass": "ResultCollector",
                       "testname": name, "enabled": "true"},
            "props": [("filename", ""), ("TestPlan.comments", "")],
            "elements": [("ResultCollector.error_logging", "boolProp", {"name": "ResultCollector.error_logging"})],
        })
    return root


def _tmpl(s):
    """Replace {var} with ${var} for JMeter variable substitution."""
    import re
    return re.sub(r"\{(\w+)\}", r"${\1}", s)


def main():
    ap = argparse.ArgumentParser(description="Generate JMeter .jmx from qa-perf-design scenario JSON.")
    ap.add_argument("--scenarios", required=True, help="Path to scenario JSON (same schema as qa-perf-locust).")
    ap.add_argument("--out", required=True, help="Output .jmx path.")
    ap.add_argument("--data-csv", help="Optional CSV data file for CSV Data Set Config.")
    ap.add_argument("--threads-cap", type=int, default=0,
                    help="If a scenario's users exceed this, emit a distributed note in comments.")
    args = ap.parse_args()

    try:
        with open(args.scenarios, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[ERROR] 读取场景失败: {e}", file=sys.stderr)
        return 2

    base_url = data.get("base_url", "")
    base_parsed = {"endpoints": data.get("endpoints", {})}
    scenarios = data.get("scenarios", [])
    if not scenarios:
        print("[ERROR] scenarios 为空", file=sys.stderr)
        return 2

    # distributed note
    notes = []
    for scn in scenarios:
        u = int(scn.get("users", 1))
        if args.threads_cap and u > args.threads_cap:
            notes.append(f"scenario '{scn.get('name')}' users={u} 超过单节点上限 "
                         f"{args.threads_cap}，建议分布式(-r)或多节点。")

    root = build_test_plan(scenarios, base_parsed, args.data_csv)
    if notes:
        # append to testplan comments via a prettify comment is not valid XML; write a side note file instead
        note_path = args.out + ".distributed_note.txt"
        with open(note_path, "w", encoding="utf-8") as nf:
            nf.write("\n".join(notes))
        print(f"[NOTE] 分布式提示已写入: {note_path}")

    ET.indent(root, space="  ")
    xml_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    with open(args.out, "wb") as f:
        f.write(xml_bytes)
    print(f"[OK] 已生成 JMeter 计划: {args.out} (scenarios={len(scenarios)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
