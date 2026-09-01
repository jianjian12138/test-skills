#!/usr/bin/env python3
"""无障碍(WCAG 2.1)静态检查：扫描 HTML，按 A 级规则产出违规与分数，A 级问题发阻断信号。

零外部依赖（仅标准库 html.parser）。契合 skills 系统的 signals 契约：
存在 critical/high（A 级底线）违规时写 signals/qa-a11y.json 的 a11y_violation（blocking=true）。

修复 V6 评审发现的误杀：
- 解析 `<label for="X">` ↔ `<input id="X">` 显式关联（不再把有关联的控件误判为无标签）。
- 跳过 `type=hidden/submit/button/image/reset` 的表单控件（它们无需可访问名称）。
- 新增 duplicate-id(4.1.1) / iframe 无 title(4.1.2) / table 无 th(1.3.1) / tabindex>0(2.4.3)。
"""
import argparse
import glob
import os
import re
import sys
from html.parser import HTMLParser

try:
    from _common import emit_signal, read_text
except ImportError as _imp_err:
    import sys as _sys
    _sys.stderr.write(
        "FATAL: _common.py 缺失/损坏，技能不可用（fail-closed）\n")
    _sys.exit(2)


BLOCKING_SEVERITIES = {"critical", "high"}
# 这些 input 类型无需可访问名称（WCAG 不要求）
SKIP_LABEL_INPUT_TYPES = {"hidden", "submit", "button", "image", "reset"}

# R-21（V8 方法学深度）：真实 WCAG 2.1 对比度引擎（非仅"标注边界"）。
# 仅对带 inline style 且同时给出 color 与 background 的元素计算；缺一则无法计算，
# 跳过并据实说明（完整覆盖需 axe-core，CI 强接，见能力边界）。
import colorsys  # noqa: F401  (保留以便将来扩展 HSL)


def parse_color(val):
    """解析 CSS 颜色为 (r,g,b) 0~255；不支持返回 None。支持 #rgb/#rrggbb/rgb()/rgba()。"""
    if not val:
        return None
    v = val.strip().lower()
    m = re.match(r"^#([0-9a-f]{3}|[0-9a-f]{6})$", v)
    if m:
        h = m.group(1)
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    m = re.match(r"^rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)", v)
    if m:
        return tuple(int(round(float(x))) for x in m.groups())
    return None


def rel_luminance(rgb):
    def lin(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast_ratio(fg, bg):
    l1, l2 = rel_luminance(fg), rel_luminance(bg)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def check_contrast(style, tag, attrs):
    """解析 inline style 的 color / background(-color)，低于 WCAG AA 阈值则返回 finding 字段。"""
    props = {}
    for part in style.split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            props[k.strip().lower()] = v.strip()
    fg = parse_color(props.get("color"))
    bg = parse_color(props.get("background-color")) or parse_color(props.get("background"))
    if fg is None or bg is None:
        return None  # 缺背景或前景无法计算，跳过（不误报）
    ratio = contrast_ratio(fg, bg)
    if ratio >= 4.5:
        return None  # 满足 AA 正常文本
    sev = "critical" if ratio < 3.0 else "high"  # <3.0 连大文本 AA 都不满足
    return {"rule": "A-CONTRAST", "severity": sev, "tag": tag,
            "detail": "文本对比度 %.2f:1 低于 WCAG AA（正常文本需≥4.5，大文本≥3.0）" % ratio,
            "attrs": attrs, "ratio": round(ratio, 2)}


class A11yScanner(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.findings = []
        self.stack = []
        self.in_label = 0
        self.last_heading = None
        self.checked = 0
        self.html_lang = None
        self.collecting = None      # 当前在收集名称的 a/button
        self.buf = []
        self.pending_attrs = {}
        self.in_video = 0
        self.video_has_caption = False
        # 显式 <label for="X"> 关联：记录所有出现过的 for 值
        self.label_fors = set()
        # id 去重检测
        self.ids = {}
        self.dup_flagged = set()
        # table/th
        self.in_table = 0
        self.table_has_th = False

    def add(self, rule, severity, tag, detail, attrs):
        loc = attrs.get("src") or attrs.get("id") or attrs.get("name") or ""
        self.findings.append({
            "rule": rule,
            "severity": severity,
            "tag": tag,
            "detail": detail,
            "loc": loc,
        })

    def _track_id(self, a):
        i = a.get("id")
        if not i:
            return
        self.ids[i] = self.ids.get(i, 0) + 1
        if self.ids[i] >= 2 and i not in self.dup_flagged:
            self.dup_flagged.add(i)
            self.add("A-DUPLICATE-ID", "high", "id", f"重复 id 属性: {i}（4.1.1）", a)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.stack.append(tag)
        self._track_id(a)
        # R-21：inline style 对比度检查（真实引擎，缺前景/背景则跳过）
        style = a.get("style")
        if style:
            c = check_contrast(style, tag, a)
            if c:
                self.add(c["rule"], c["severity"], c["tag"], c["detail"], c["attrs"])
        if tag == "label":
            self.in_label += 1
            if a.get("for"):
                self.label_fors.add(a["for"])
        if tag == "html":
            self.html_lang = a.get("lang")
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.checked += 1
            lvl = int(tag[1])
            if self.last_heading is not None and lvl > self.last_heading + 1:
                self.add("A-HEADING-ORDER", "high", tag,
                         f"标题层级跳级（上一为 h{self.last_heading}）", a)
            self.last_heading = lvl
        elif tag == "img":
            self.checked += 1
            if a.get("alt") is None:
                self.add("A-IMG-ALT", "critical", "img", "图片缺少 alt 属性", a)
        elif tag in ("input", "select", "textarea"):
            self.checked += 1
            itype = (a.get("type") or "").lower()
            if itype in SKIP_LABEL_INPUT_TYPES:
                pass  # 这些类型无需可访问名称
            else:
                ok = (self.in_label > 0
                      or a.get("aria-label") or a.get("aria-labelledby") or a.get("title")
                      or (a.get("id") and a["id"] in self.label_fors))
                if not ok:
                    self.add("A-INPUT-LABEL", "critical", tag, "表单控件缺少关联 label/aria-label", a)
        elif tag in ("a", "button"):
            self.checked += 1
            self.collecting = tag
            self.buf = []
            self.pending_attrs = a
        elif tag == "video":
            self.checked += 1
            self.in_video += 1
            self.video_has_caption = False
            self.pending_attrs = a
        elif tag == "track":
            if self.in_video > 0 and a.get("kind") in ("captions", "subtitles"):
                self.video_has_caption = True
        elif tag == "iframe":
            if not a.get("title"):
                self.add("A-IFRAME-TITLE", "high", "iframe", "iframe 缺少 title（4.1.2）", a)
        elif tag == "table":
            self.in_table += 1
            self.table_has_th = False
        elif tag == "th":
            if self.in_table > 0:
                self.table_has_th = True
        elif tag == "div" or tag == "span":
            if a.get("onclick") or a.get("onkeydown"):
                self.checked += 1
                if not a.get("role"):
                    self.add("A-ROLE", "medium", tag, "可交互元素缺少 role", a)
        tz = a.get("tabindex")
        if tz is not None:
            try:
                if int(tz) > 0:
                    self.add("A-TABINDEX", "high", tag, f"tabindex={tz} > 0（2.4.3 应避免）", a)
            except ValueError:
                pass

    def handle_data(self, data):
        if self.collecting:
            self.buf.append(data)

    def handle_endtag(self, tag):
        if tag == "label" and self.in_label > 0:
            self.in_label -= 1
        if tag in ("a", "button") and self.collecting == tag:
            a = self.pending_attrs
            name = "".join(self.buf).strip()
            has_name = name or a.get("aria-label") or a.get("aria-labelledby") or a.get("title")
            if not has_name:
                self.add("A-NAME", "high", tag, "链接/按钮无可访问名称", a)
            self.collecting = None
            self.buf = []
        if tag == "video" and self.in_video > 0:
            self.in_video -= 1
            if not self.video_has_caption:
                self.add("A-VIDEO-CAPTION", "medium", "video", "视频缺少字幕轨(captions)", self.pending_attrs)
        if tag == "table" and self.in_table > 0:
            self.in_table -= 1
            if not self.table_has_th:
                self.add("A-TABLE-TH", "high", "table", "表格缺少 <th> 表头（1.3.1）", {})
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()


def scan_file(path, source_label=None):
    src = source_label or path
    try:
        html = read_text(path)
    except OSError as e:
        return [{"rule": "A-IO", "severity": "medium", "tag": "file",
                 "detail": f"读取失败: {e}", "loc": src}]
    sc = A11yScanner()
    sc.feed(html)
    if sc.html_lang is None:
        sc.add("A-HTML-LANG", "high", "html", "<html> 缺少 lang 属性", {})
    for f in sc.findings:
        f["file"] = src
    return sc.findings


def main():
    ap = argparse.ArgumentParser(description="无障碍(WCAG 2.1)静态检查")
    ap.add_argument("--in", dest="in_path", required=True, help="HTML 文件或目录")
    ap.add_argument("--out", default="a11y_report.md", help="报告输出路径")
    ap.add_argument("--signals-dir", default="signals", help="信号输出目录（接门禁）；缺省即写 signals/ 确保任何调用都落信号")
    ap.add_argument("--fail-on", action="store_true", help="存在 A 级违规时 sys.exit(1)")
    args = ap.parse_args()

    files = []
    if os.path.isdir(args.in_path):
        files = sorted(glob.glob(os.path.join(args.in_path, "**", "*.html"), recursive=True))
    else:
        files = [args.in_path]

    all_findings = []
    for fp in files:
        all_findings += scan_file(fp)

    # 分数按「A 级违规 / 被扫描元素」估算
    blocking = [f for f in all_findings if f["severity"] in BLOCKING_SEVERITIES]
    n_block = len(blocking)
    score = max(0.0, 1.0 - n_block / max(1, len(all_findings) + n_block))

    by_rule = {}
    for f in all_findings:
        by_rule.setdefault(f["rule"], []).append(f)

    lines = [
        "# 无障碍（WCAG 2.1）检查报告",
        "",
        f"**结论：{'⛔ 存在 A 级违规，阻断' if n_block else '✅ 未发现 A 级违规'}**",
        "",
        f"- 扫描文件数：{len(files)}",
        f"- 违规总数：{len(all_findings)}（其中 A 级底线 {n_block}）",
        f"- A 级违规趋势分：{score:.3f}（仅供观察）",
        "",
        "## 按规则汇总",
        "",
        "| 规则 | 级别 | 数量 |",
        "| --- | --- | --- |",
    ]
    sev_map = {"A-IMG-ALT": "critical", "A-INPUT-LABEL": "critical", "A-HTML-LANG": "high",
               "A-HEADING-ORDER": "high", "A-NAME": "high", "A-VIDEO-CAPTION": "medium",
               "A-ROLE": "medium", "A-IO": "medium", "A-DUPLICATE-ID": "high",
               "A-IFRAME-TITLE": "high", "A-TABLE-TH": "high", "A-TABINDEX": "high",
               "A-CONTRAST": "high"}
    order = ["A-IMG-ALT", "A-INPUT-LABEL", "A-HTML-LANG", "A-HEADING-ORDER",
             "A-NAME", "A-VIDEO-CAPTION", "A-ROLE", "A-DUPLICATE-ID",
             "A-IFRAME-TITLE", "A-TABLE-TH", "A-TABINDEX", "A-CONTRAST", "A-IO"]
    for r in order:
        if r in by_rule:
            lines.append(f"| {r} | {sev_map.get(r,'')} | {len(by_rule[r])} |")
    lines.append("")

    if all_findings:
        lines += ["## 违规明细", "",
                  "| 文件 | 规则 | 级别 | 元素 | 说明 |",
                  "| --- | --- | --- | --- | --- |"]
        for f in all_findings:
            loc = f.get("loc", "")
            lines.append(f"| {f.get('file','')} | {f['rule']} | {f['severity']} | "
                         f"{f.get('tag','')} {('`' + loc + '`') if loc else ''} | {f['detail']} |")
        lines.append("")

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    if n_block:
        top = "critical" if any(f["severity"] == "critical" for f in blocking) else "high"
        emit_signal("qa-a11y", [{
            "signal": "a11y_violation",
            "severity": top,
            "count": n_block,
            "blocking": True,
            "detail_ref": os.path.basename(args.out),
            "rules": sorted({f["rule"] for f in blocking}),
        }], args.signals_dir)
    else:
        # RK-02 修复：干净运行也须产出 verified 信号（blocking:false），使发布门禁
        # 能区分“跑了且过” vs “没跑”，消除 DEFAULT_REQUIRED 误杀。
        if args.signals_dir:
            emit_signal("qa-a11y", [{
                "signal": "a11y_verified",
                "severity": "info",
                "count": 0,
                "blocking": False,
                "detail_ref": os.path.basename(args.out),
                "verdict": "no_findings",
            }], args.signals_dir)

    print(f"[RESULT] files={len(files)} findings={len(all_findings)} a_level={n_block} "
          f"score={score:.3f} blocked={bool(n_block)}")
    if args.fail_on and n_block:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
