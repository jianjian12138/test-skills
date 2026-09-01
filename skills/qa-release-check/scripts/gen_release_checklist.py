#!/usr/bin/env python3
"""Generate a release readiness checklist with a *data-driven* release gate.

门禁契约（与 ADR-002 / signals schema 一致）：**任一 blocking=true 信号即禁止发布**，
不再叠加 severity 约束（severity 仅为信息性分级）。这消除了 V6 评审发现的
「blocking=true 但 severity=medium 被静默放行」的假绿漏杀缺陷。

证据缺失即不发布：未提供任何 signals/ 信号文档（空目录或未传产物参数）→ 判阻断。
信号新鲜度：generated_at 超过 STALE_WINDOW_H 小时、或缺失/非法 → 视为陈旧 → 阻断（R-06 fail-closed）。
必需信号：默认集 ``DEFAULT_REQUIRED``（qa-security-scan/qa-a11y/qa-unit-tdd）缺失即阻断（S-01 默认 fail-closed）；
          显式 ``--required`` 覆盖默认集；``--skip-required`` 关闭该强制（仅建议非发布场景使用）。

Usage:
    python scripts/gen_release_checklist.py \
        --release release.json \
        --signals-dir ./signals \
        --out release_check.md [--fail-on] [--json summary.json] [--required qa-a11y,qa-perf-analysis]

兼容：仍可传 --test-report/--bugs/--security/--perf，门禁内部将其转译为等价信号，
保证旧流程不中断。
"""
import argparse
import json
import os
import sys
from datetime import datetime

# 人工确认类门禁（仍需人拍板，但单独成段，不与数据门禁混淆）
MANUAL_GATE_ITEMS = [
    ("构建产物版本与发布单一致", "build_ok"),
    ("DB 迁移脚本已评审且可回滚", "db_migrations"),
    ("配置（含密钥）已就位、无硬编码", "config_ok"),
    ("三方依赖/限流/配额已确认", "deps_ok"),
    ("回滚方案明确且演练过", "rollback_plan"),
]

SEVERITY_OPEN_BLOCK = {"S1", "S2"}
SEC_HIGH_BLOCK = {"critical", "high", "严重", "高"}
STALE_WINDOW_H = 24

# S-01（V8 设计权衡定稿）：发布门禁默认 fail-closed——未显式 --skip-required 时，
# 下列必需信号来源缺失即阻断（对标 Pact can-i-deploy 不可绕过）。opt-out 需显式声明。
DEFAULT_REQUIRED = ["qa-security-scan", "qa-a11y", "qa-unit-tdd"]

# A-03（V10）：横切 opt-in 候选集（高相关横切质量门）。默认不纳入发布门禁；
# 显式 --include-cross 才把它们拉进聚合，且缺失即阻断（opt-in 收紧而非放宽）。
DEFAULT_CROSS = ["qa-code-review", "qa-mutation", "qa-flaky-detect",
                 "qa-visual-regression", "qa-unit-tdd", "qa-a11y"]


def load_json(path):
    if not path:
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARN] 读取 {path} 失败: {e}", file=sys.stderr)
        return None


# ------------------------- 信号加载 -------------------------
def _is_valid_signal(s):
    """R-01：信号对象 schema 校验——字段类型必须正确，否则视为损坏（fail-closed）。"""
    if not isinstance(s, dict):
        return False
    if not isinstance(s.get("signal"), str):
        return False
    if not isinstance(s.get("blocking"), bool):
        return False
    if not isinstance(s.get("severity"), str):
        return False
    if not isinstance(s.get("count"), int):
        return False
    return True


def load_signal_docs(signals_dir):
    """扫描 signals/ 下所有 *.json，返回 [doc, ...]。

    R-01 修复（损坏即阻断）：解析失败或含非法信号对象的文件，不再被静默跳过，
    而是注入 critical/blocking 的 corrupt_signal 信号，使门禁必然 fail-closed。
    """
    docs = []
    if not signals_dir or not os.path.isdir(signals_dir):
        return docs
    now_iso = datetime.now().isoformat()
    for fn in sorted(os.listdir(signals_dir)):
        if not fn.endswith(".json"):
            continue
        path = os.path.join(signals_dir, fn)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            # 解析失败 → 损坏即阻断（对标 Pact can-i-deploy：missing==failed 均 exit1）
            print(f"[WARN] 解析信号文件 {path} 失败: {e} → 视为损坏信号(blocking)", file=sys.stderr)
            docs.append({
                "source": f"CORRUPT:{fn}", "generated_at": now_iso,
                "signals": [{
                    "signal": "corrupt_signal_file", "severity": "critical", "count": 1,
                    "blocking": True,
                    "detail": f"信号文件 {fn} 解析失败/损坏，按「损坏即阻断」处理",
                }],
            })
            continue
        if not isinstance(data, dict) or not data.get("signals"):
            # 非信号文档（普通 JSON 产物）→ 跳过，不报错
            continue
        bad = [s for s in data.get("signals", []) if not _is_valid_signal(s)]
        if bad:
            # 信号对象不符合 schema → 损坏即阻断
            print(f"[WARN] 信号文件 {path} 含 {len(bad)} 个非法信号对象 → 视为损坏(blocking)", file=sys.stderr)
            docs.append({
                "source": f"CORRUPT:{fn}", "generated_at": now_iso,
                "signals": [{
                    "signal": "corrupt_signal_schema", "severity": "critical", "count": len(bad),
                    "blocking": True,
                    "detail": f"信号文件 {fn} 含 {len(bad)} 个不符合 schema 的信号对象",
                }],
            })
            continue
        docs.append(data)
    return docs


def _is_stale(generated_at, stale_window_h=STALE_WINDOW_H):
    """R-05/R-06 修复：缺失或非法戳 → 判陈旧（fail-closed）；时区戳不得打崩门禁。

    统一用带时区的 now 比对：naive 戳按本机时区补齐，aware 戳直接比对，
    杜绝 naive-naive(tz) 相减 TypeError 导致清单都不生成。

    stale_window_h 可显式注入（A-02 解耦：窗口是参数而非不可覆写常量），
    便于测试/特殊发布窗口覆写，生产默认 24h，fail-closed 不变。
    """
    if not generated_at:
        return True
    try:
        dt = datetime.fromisoformat(generated_at)
    except Exception:
        return True
    now = datetime.now().astimezone()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=now.tzinfo)
    age_h = (now - dt).total_seconds() / 3600.0
    return age_h > stale_window_h


def legacy_to_signals(test_report, bugs, security, perf):
    """将 4 类旧参数转译为等价信号文档，保证向后兼容。"""
    docs = []
    sigs = []

    if bugs is not None:
        items = bugs if isinstance(bugs, list) else bugs.get("bugs", bugs.get("items", []))
        open_critical = [b for b in items
                         if str(b.get("status", "")).lower() in ("open", "未关闭", "")
                         and str(b.get("severity", "")).upper() in SEVERITY_OPEN_BLOCK]
        if open_critical:
            sigs.append({"signal": "open_critical_bug", "severity": "critical",
                         "count": len(open_critical), "blocking": True,
                         "detail_ref": "bugs"})

    if security is not None:
        sec_items = security if isinstance(security, list) else security.get("findings", security.get("items", []))
        high = [s for s in sec_items if str(s.get("severity", "")).lower() in {x.lower() for x in SEC_HIGH_BLOCK}]
        if high:
            sigs.append({"signal": "security_finding", "severity": "high",
                         "count": len(high), "blocking": True, "detail_ref": "security"})

    if test_report is not None:
        p0_total = test_report.get("p0_total", 0)
        p0_pass = test_report.get("p0_pass", 0)
        if p0_total and p0_pass < p0_total:
            sigs.append({"signal": "p0_case_fail", "severity": "high",
                         "count": p0_total - p0_pass, "blocking": True, "detail_ref": "test_report"})

    if perf is not None:
        p95 = perf.get("p95_ms", 0)
        sla = perf.get("sla_ms", 0)
        if sla and p95 > sla:
            sigs.append({"signal": "perf_sla_violation", "severity": "high",
                         "count": 1, "blocking": True, "detail_ref": "perf"})

    if sigs:
        docs.append({"source": "legacy-args", "generated_at": datetime.now().isoformat(), "signals": sigs})
    return docs


def inject_governance(docs, required, stale_window_h=STALE_WINDOW_H):
    """追加治理类门禁：陈旧信号 + 缺失必需信号。返回新 docs 列表。"""
    extra = []
    stale = [d for d in docs if _is_stale(d.get("generated_at", ""), stale_window_h)]
    if stale:
        extra.append({
            "source": "release-gate", "generated_at": datetime.now().isoformat(),
            "signals": [{
                "signal": "stale_signals", "severity": "high", "count": len(stale),
                "blocking": True,
                "detail": f"{len(stale)} 个信号超过 {stale_window_h}h 新鲜度窗口，须重新生成",
            }],
        })
    if required:
        present = {d.get("source") for d in docs}
        missing = [r for r in required if r not in present]
        if missing:
            extra.append({
                "source": "release-gate", "generated_at": datetime.now().isoformat(),
                "signals": [{
                    "signal": "missing_required_signals", "severity": "critical",
                    "count": len(missing), "blocking": True,
                    "detail": "缺少必需信号来源: " + ", ".join(missing),
                }],
            })
    return docs + extra


def inject_cross(docs, cross_list, signals_dir):
    """A-03：横切 opt-in 收紧。cross_list 非空时，若所列横切信号来源在 signals/ 中缺失，
    注入 blocking 的 ``missing_cross_signal``（opt-in 意味着主动提高发布门槛）；
    已存在的横切 blocking 信号由 collect_blocking 正常聚合。
    """
    if not cross_list:
        return docs
    present = {d.get("source") for d in load_signal_docs(signals_dir)}
    missing = [c for c in cross_list if c not in present]
    if missing:
        docs.append({
            "source": "release-gate", "generated_at": datetime.now().isoformat(),
            "signals": [{
                "signal": "missing_cross_signal", "severity": "critical", "count": len(missing),
                "blocking": True,
                "detail": "opt-in 横切信号缺失（--include-cross 已开启）: " + ", ".join(missing),
            }],
        })
    return docs


def collect_blocking(docs):
    """门禁唯一权威：blocking=true 即收集（severity 仅为信息性分级，不参与判定）。"""
    blocked = []
    for doc in docs:
        src = doc.get("source", "?")
        for s in doc.get("signals", []):
            if s.get("blocking"):
                blocked.append((src, s))
    return blocked


def evaluate_data_gates(signals_dir, test_report, bugs, security, perf, required=None,
                        stale_window_h=STALE_WINDOW_H, include_cross=None):
    """返回 (signal_docs, blocked_list, any_blocking)。include_cross 非空（A-03 opt-in）时收紧。"""
    docs = load_signal_docs(signals_dir)
    docs += legacy_to_signals(test_report, bugs, security, perf)
    docs = inject_governance(docs, required, stale_window_h)
    docs = inject_cross(docs, include_cross, signals_dir)
    blocked = collect_blocking(docs)
    return docs, blocked, bool(blocked)


def render(data, docs, blocked, has_signals, include_cross=None):
    lines = []
    lines.append(f"# 上线验证清单：{data.get('version', '-')} → {data.get('env', '-')}\n")

    if include_cross:
        lines.append(f"> 🔧 **横切 opt-in（A-03）已开启**：本发布主动将高相关横切质量门 "
                     f"({', '.join(include_cross)}) 纳入聚合；缺失即阻断（opt-in 收紧而非放宽）。\n")

    lines.append("## 一、数据驱动上线门禁（聚合 signals/ 质量信号；任一 blocking → 禁止发布）\n")
    if not docs:
        # 无任何证据 → 按「无证据即不发布」判阻断
        lines.append("> ⚠️ 未提供任何门禁信号（`signals/` 为空或未传产物参数）。按「无证据即不发布」，**本项判为阻断**。\n")
        verdict_blocked = True
    else:
        verdict_blocked = bool(blocked)
        if blocked:
            lines.append(f"**🚫 门禁结论：禁止发布**（{len(blocked)} 个 blocking 信号）\n")
        else:
            lines.append("**✅ 门禁结论：可上线**（无 blocking 信号）\n")
        lines.append("| 来源 | 信号 | 严重度 | 数量 | 阻断 | 详情 |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for doc in docs:
            src = doc.get("source", "?")
            for s in doc.get("signals", []):
                mark = "🚫" if s.get("blocking") else "·"
                lines.append(f"| {src} | {s.get('signal','')} | {s.get('severity','')} | {s.get('count',0)} | {mark} | {s.get('detail_ref','')} |")
        lines.append("")

    lines.append("## 二、人工确认项（仍需人拍板）\n")
    lines.append("| 检查项 | 状态 | 备注 |")
    lines.append("| --- | --- | --- |")
    for label, key in MANUAL_GATE_ITEMS:
        ok = data.get(key)
        mark = "✅ 通过" if ok else ("☐ 待确认" if ok is None else "❌ 未过")
        lines.append(f"| {label} | {mark} | |")
    lines.append("")

    lines.append("## 三、上线冒烟（部署后立刻跑）\n")
    smokes = data.get("smoke", [])
    if smokes:
        for s in smokes:
            lines.append(f"- ☐ {s}")
    else:
        lines.append("- ☐ 核心链路冒烟（默认）")
    lines.append("")

    lines.append("## 四、发布后监控（灰度 + 全量各一轮）\n")
    mon = data.get("monitoring", [])
    default_mon = ["错误率告警", "核心接口 P95 SLA", "CPU/内存", "核心业务指标"]
    for m in (mon or default_mon):
        lines.append(f"- ☐ {m}（灰度30min → 全量2h → 次日早高峰）")
    lines.append("")

    lines.append("## 五、最终结论\n")
    lines.append(f"- 数据门禁：{'❌ 禁止发布' if verdict_blocked else '✅ 可上线'}")
    lines.append("- 人工确认：☐ 全部通过 / ☐ 有未过项")
    lines.append("- 冒烟：☐ 通过 / ☐ 失败")
    lines.append("- 监控：☐ 无异常 / ☐ 异常（触发回滚）")
    lines.append("- 最终：☐ 关闭变更（qa-archive） / ☐ 回滚重开缺陷")
    lines.append("")
    return "\n".join(lines), verdict_blocked


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--release", required=True, help="发布元数据 JSON（version/env/services/冒烟/监控 + 人工确认布尔）")
    ap.add_argument("--signals-dir", default="signals", help="质量信号目录（默认 ./signals），门禁扫描其下 *.json")
    ap.add_argument("--test-report", help="[兼容] 测试报告 JSON（p0_total/p0_pass）")
    ap.add_argument("--bugs", help="[兼容] 缺陷报告 JSON（含 severity/status）")
    ap.add_argument("--security", help="[兼容] 安全发现 JSON（含 severity）")
    ap.add_argument("--perf", help="[兼容] 性能报告 JSON（p95_ms/sla_ms）")
    ap.add_argument("--required", help="[可选] 必须齐备的信号来源名（逗号分隔），缺失即阻断；省略则用 DEFAULT_REQUIRED")
    ap.add_argument("--skip-required", action="store_true", help="S-01 关闭默认必需信号强制（仅非发布场景）")
    ap.add_argument("--include-cross", nargs="*", default=None,
                    help="A-03：横切 opt-in，将高相关横切质量门纳入发布聚合（默认关）。"
                         "可跟具体技能名（如 qa-code-review qa-mutation）；省略则启用 DEFAULT_CROSS。")
    ap.add_argument("--stale-window-h", type=float, default=STALE_WINDOW_H,
                    help="A-02：信号新鲜度窗口(小时)，默认 24；陈旧即阻断(fail-closed)。"
                         "可显式增大用于长发布周期/测试覆写，不得设为负数（仍判陈旧）。")
    ap.add_argument("--out", required=True, help="Markdown 输出")
    ap.add_argument("--fail-on", action="store_true", help="数据门禁不过时 sys.exit(1)")
    ap.add_argument("--json", help="额外输出门禁结论 JSON 摘要")
    args = ap.parse_args()

    release = load_json(args.release)
    if release is None:
        print(f"[ERROR] 读取 release 失败", file=sys.stderr)
        return 2

    test_report = load_json(args.test_report)
    bugs = load_json(args.bugs)
    security = load_json(args.security)
    perf = load_json(args.perf)
    required = [r.strip() for r in (args.required or "").split(",") if r.strip()]
    if not required and not args.skip_required:
        required = list(DEFAULT_REQUIRED)  # S-01 默认 fail-closed

    # A-03：横切 opt-in（默认关）。显式开启时收紧发布门槛。
    include_cross = None
    if args.include_cross is not None:
        include_cross = args.include_cross if args.include_cross else list(DEFAULT_CROSS)

    has_signals = bool(args.signals_dir) and os.path.isdir(args.signals_dir)
    docs, blocked, _ = evaluate_data_gates(args.signals_dir, test_report, bugs, security, perf,
                                           required, args.stale_window_h, include_cross)
    md, verdict_blocked = render(release, docs, blocked, has_signals, include_cross=include_cross)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"[OK] 已生成上线清单: {args.out}")
    print(f"[GATE] 数据门禁结论: {'❌ 禁止发布' if verdict_blocked else '✅ 可上线'}（信号来源 {len(docs)} 个，blocking {len(blocked)} 个）")

    if args.json:
        summary = {
            "version": release.get("version"),
            "env": release.get("env"),
            "blocked": verdict_blocked,
            "signal_sources": len(docs),
            "blocking_signals": [
                {"source": src, "signal": s.get("signal"), "severity": s.get("severity")}
                for src, s in blocked
            ],
        }
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"[OK] 已生成门禁摘要: {args.json}")

    if args.fail_on and verdict_blocked:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
