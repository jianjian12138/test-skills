#!/usr/bin/env python3
"""qa-orchestrator 单一事实源（SSOT）加载器。

所有编排脚本（init_change / route_next / close_loop）统一从 `stages.json` 读取阶段定义，
杜绝三处硬编码 STAGES 漂移（修复 P0-B）。

阶段目录判定 `is_stage_done` 要求：目录存在、且至少有一个**非隐藏、非空（>MIN_BYTES）**
的匹配产物（修复 P1-K 「0 字节文件即通过阶段」）。
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
STAGES_FILE = os.path.join(os.path.dirname(HERE), "stages.json")
MIN_BYTES = 1

# 缓存，避免重复读盘
_STAGES_CACHE = None


def load_stages(force=False):
    """返回 stages.json 中的 stage 列表（dict 列表）。"""
    global _STAGES_CACHE
    if _STAGES_CACHE is not None and not force:
        return _STAGES_CACHE
    with open(STAGES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    _STAGES_CACHE = data["stages"]
    return _STAGES_CACHE


def stage_dir_has_output(stage_dir, min_bytes=MIN_BYTES):
    """目录是否含非空产物（忽略隐藏文件）。返回 (bool, [文件名])。"""
    if not os.path.isdir(stage_dir):
        return False, []
    files = [f for f in os.listdir(stage_dir) if not f.startswith(".")]
    non_empty = []
    for f in files:
        p = os.path.join(stage_dir, f)
        if os.path.isfile(p) and os.path.getsize(p) > min_bytes:
            non_empty.append(f)
    return bool(non_empty), non_empty


def is_stage_done(stage_dir, stage_def, min_bytes=MIN_BYTES):
    """按 stages.json 的阶段定义判定该阶段是否已完成。

    - 目录无内容 → 未完成
    - optional 阶段：有任意非空产物即完成
    - 非 optional：需命中 artifacts 中至少一个（.zip 按后缀匹配）
    """
    has, files = stage_dir_has_output(stage_dir, min_bytes)
    if not has:
        return False
    if stage_def.get("optional"):
        return True
    arts = stage_def.get("artifacts") or []
    if not arts:
        return True
    low = {f.lower() for f in files}
    for a in arts:
        if a == ".zip":
            if any(f.lower().endswith(".zip") for f in files):
                return True
        elif a.lower() in low:
            return True
    return False


# ----------------------------------------------------------------------------
# R-14：--apply 前产物内容校验（防止「空壳阶段」被标完成）
# 仅对 JSON 产物做关键字段校验；非 JSON / 未在期望表的产物退回 lenient 非空判定。
# 设计原则：fail-closed——阶段若「有产物」但全部产物均为空壳，则不得被 --apply 标完成。
# ----------------------------------------------------------------------------
ARTIFACT_KEY_EXPECTATIONS = {
    "reqs.json": {"any_of": ["requirements", "reqs", "items"], "non_empty": True},
    "cases.json": {"any_of": ["cases"], "non_empty": True, "non_empty_keys": ["cases"]},
    "testdata.json": {"non_empty": True},
    "api-doc.json": {"any_of": ["items", "endpoints", "paths", "apis"], "non_empty": True},
    "openapi.json": {"any_of": ["paths", "openapi", "swagger"], "non_empty": True},
    "results.json": {"any_of": ["results", "summary", "total", "cases"], "non_empty": True,
                     "non_empty_keys": ["results"]},
    "test-report.json": {"any_of": ["total", "passed", "failed_cases", "p0_total", "summary"],
                         "non_empty": True},
    "bug_report.json": {"any_of": ["bugs", "items"], "non_empty": True, "non_empty_keys": ["bugs"]},
    "security_findings.json": {"any_of": ["findings", "items"], "non_empty": True,
                               "non_empty_keys": ["findings"]},
}

# ----------------------------------------------------------------------------
# T-01：Markdown 阶段产物空壳判定（requirement.md / analysis.md / testpoints.md /
# report.md / test-report.md / test-strategy.md）。这些产物此前不在 ARTIFACT_KEY_EXPECTATIONS，
# 被 _artifact_content_ok 以 lenient 非空直接放行——一个仅含标题的空壳 Markdown 即可让阶段被
# --apply 标完成。此处补齐启发式：至少 1 个标题 + 足够正文行，或含阶段强标识（REQ-/TP-/结果关键词）。
# 标记只用「强标识」（REQ-/TP-/通过·失败/summary 等），避免标题里的通用词（需求/策略）触发误判。
# ----------------------------------------------------------------------------
_MARKDOWN_HEADING_MIN = 1
_MARKDOWN_BODY_MIN = 5
_MARKDOWN_MARKERS = {
    "requirement.md": ["REQ-"],
    "analysis.md": ["TP-"],
    "testpoints.md": ["TP-"],
    "report.md": ["通过", "失败", "pass", "fail", "summary"],
    "test-report.md": ["通过", "失败", "pass", "fail", "summary", "p0"],
    "test-strategy.md": ["准入", "退出准则", "测试范围", "风险等级", "覆盖率目标"],
}


def _markdown_not_shell(path, exp=None):
    """判定 Markdown 产物是否非空壳。要求：>=1 标题，且（正文行数>=阈值 或 含阶段强标识且正文>=1）。"""
    try:
        text = open(path, "r", encoding="utf-8").read()
    except Exception:
        return False
    if not text.strip():
        return False
    lines = text.splitlines()
    headings = [l for l in lines if re.match(r"^#+\s", l)]
    body = [l for l in lines if l.strip() and not l.strip().startswith("#") and len(l.strip()) >= 4]
    if len(headings) < _MARKDOWN_HEADING_MIN:
        return False
    min_body = (exp or {}).get("min_body", _MARKDOWN_BODY_MIN)
    if len(body) >= min_body:
        return True
    markers = (exp or {}).get("markers") or _MARKDOWN_MARKERS.get(os.path.basename(path).lower())
    if markers and len(body) >= 1 and any(m.lower() in text.lower() for m in markers):
        return True
    return False


def _artifact_content_ok(path):
    """判定单个产物是否非空壳。非 JSON / 不在期望表 → lenient 非空即 ok。"""
    if not os.path.isfile(path) or os.path.getsize(path) <= 0:
        return False
    exp = ARTIFACT_KEY_EXPECTATIONS.get(os.path.basename(path).lower())
    if not exp:
        if os.path.basename(path).lower().endswith(".md"):
            return _markdown_not_shell(path)
        return True
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return False  # 破坏的 JSON = 空壳
    if exp.get("non_empty") and (data is None or (isinstance(data, (dict, list)) and len(data) == 0)):
        return False
    any_of = exp.get("any_of")
    if any_of:
        keys = data.keys() if isinstance(data, dict) else ()
        if not any(k in keys for k in any_of):
            return False
        # non_empty_keys：具名集合键（cases/bugs/results/findings/items 等）须非空，
        # 防止 {"cases":[]} 这类「有键无值」的空壳通过。
        for k in (exp.get("non_empty_keys") or []):
            if k in keys and isinstance(data[k], (list, dict, str)) and len(data[k]) == 0:
                return False
    return True


def validate_artifact_content(stage_dir, stage_def):
    """R-14：阶段若已「有产物」，但所有产物均为空壳 → 判为 shell，--apply 不得标完成。

    返回 (ok: bool, reason: str)。
      ok=True  —— 至少含一份真实内容产物（有合法关键字段 / 非空集合），可标完成；
      ok=False —— 全部产物为空壳（空 dict/list / 破坏 JSON / 缺关键字段），应 blocked。
    无产物（is_stage_done 已判未完成）时返回 (True, "")——与 R-14 无关，交由 is_stage_done 处理。
    """
    if not os.path.isdir(stage_dir):
        return True, ""
    present = []
    for a in (stage_def.get("artifacts") or []):
        p = os.path.join(stage_dir, a)
        if os.path.isfile(p) and os.path.getsize(p) > 0:
            present.append(p)
    if not present:
        return True, ""
    if any(_artifact_content_ok(p) for p in present):
        return True, ""
    names = [os.path.basename(p) for p in present]
    return False, "空壳产物（无关键字段/空集合/损坏）：" + ", ".join(names)


# ----------------------------------------------------------------------------
# 编排状态机（P0-A：防死循环 / 黑洞）
# 每个变更目录维护一份轻量状态文件，记录编排步数；超过 max_steps 即判 BLOCKED，
# 防止外部驱动循环无限重复同一未完成阶段。
# ----------------------------------------------------------------------------
ORCH_STATE_FILE = ".qa_orch_state.json"


def orch_state_path(change_dir):
    return os.path.join(change_dir, ORCH_STATE_FILE)


def load_orch_state(change_dir):
    p = orch_state_path(change_dir)
    if os.path.isfile(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"step": 0}


def save_orch_state(change_dir, state):
    try:
        with open(orch_state_path(change_dir), "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def bump_step(change_dir, max_steps):
    """推进编排步数；超过上限返回 blocked=True（防死循环）。"""
    st = load_orch_state(change_dir)
    st["step"] = st.get("step", 0) + 1
    blocked = st["step"] > max_steps
    if blocked:
        st["blocked_reason"] = "max_steps_exceeded@%d" % max_steps
    save_orch_state(change_dir, st)
    return st, blocked


# ----------------------------------------------------------------------------
# 横切关注点推荐（P1-9：修复 route_next / close_loop 只循环 8 阶段、完全忽略
# stages.json.cross_cutting ×11 的问题）。
#
# 触发规则集中在此（编排 SSOT），route_next / close_loop 共用；
# 刻意保持 stages.json 的 cross_cutting 为「纯名称数组」，因为 build_registry /
# check_drift / gen_deps / render_stages 均把它当字符串集合消费——改为对象会破坏
# 这 4 个消费者。触发规则与名称解耦，既满足「按变更特征推荐横切技能」的目标，
# 又对既有契约零破坏。
# ----------------------------------------------------------------------------
CROSS_CUTTING_TRIGGERS = {
    "qa-code-review": {
        "suffixes": [".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go",
                     ".rs", ".cpp", ".c", ".cs", ".rb", ".php"],
        "names": [], "keywords": [],
        "reason": "检测到源代码文件，建议做代码评审（qa-code-review）",
    },
    "qa-unit-tdd": {
        "suffixes": [".py", ".js", ".ts", ".java", ".go"],
        "names": [], "keywords": [],
        "reason": "检测到源代码，建议补充单元测试 / TDD（qa-unit-tdd）",
    },
    "qa-mutation": {
        "suffixes": [".py"],
        "names": [], "keywords": [],
        "reason": "存在 Python 源码，建议做变异测试评估用例杀伤力（qa-mutation）",
    },
    "qa-a11y": {
        "suffixes": [".html", ".htm", ".vue", ".jsx", ".tsx"],
        "names": [], "keywords": [],
        "reason": "存在前端 / 页面文件，建议做无障碍 a11y 扫描（qa-a11y）",
    },
    "qa-visual-regression": {
        "suffixes": [".png", ".jpg", ".jpeg", ".html", ".vue", ".jsx", ".tsx"],
        "names": [], "keywords": [],
        "reason": "存在 UI 截图 / 页面文件，建议做视觉回归（qa-visual-regression）",
    },
    "qa-perf-locust": {
        "suffixes": [".py"],
        "names": ["locustfile.py", "locustfile"], "keywords": ["locust"],
        "reason": "检测到 Locust 脚本，建议做性能压测（qa-perf-locust）",
    },
    "qa-perf-jmeter": {
        "suffixes": [".jmx"],
        "names": ["plan.jmx"], "keywords": ["jmeter"],
        "reason": "检测到 JMeter 脚本，建议做性能压测（qa-perf-jmeter）",
    },
    "qa-chaos": {
        "suffixes": [".yaml", ".yml"],
        "names": ["docker-compose.yaml", "docker-compose.yml"],
        "keywords": ["kubernetes", "chaos", "deploy"],
        "reason": "检测到部署 / 编排配置，建议做混沌工程（qa-chaos）",
    },
    "qa-synthetic-monitoring": {
        "suffixes": [".json"],
        "names": ["openapi.json", "api-doc.json", "results.json"],
        "keywords": ["synthetic", "monitoring", "probe"],
        "reason": "检测到接口 / 线上产物，建议补充合成监控探针（qa-synthetic-monitoring）",
    },
    "qa-risk-based": {
        "suffixes": [], "names": [], "keywords": [],
        "min_stage_done": 2,
        "reason": "变更已推进到用例 / 执行阶段，建议做基于风险的测试优先排序（qa-risk-based）",
    },
    "qa-flaky-detect": {
        "suffixes": [".json", ".md"],
        "names": ["results.json", "report.md"], "keywords": ["flaky"],
        "reason": "存在执行结果，建议做 flaky 测试探测（qa-flaky-detect）",
    },
    "qa-ci": {
        "suffixes": [".yaml", ".yml"],
        "names": ["ci.yaml", "jenkinsfile", ".gitlab-ci.yml", ".github"],
        "keywords": ["ci", "pipeline"],
        "reason": "检测到 CI 配置，建议生成 / 校验 CI 流水线（qa-ci）",
    },
    "qa-test-strategy": {
        "suffixes": [], "names": [], "keywords": [],
        "min_stage_done": 0,
        "reason": "建议在变更早期补充整体测试策略（qa-test-strategy）",
    },
}


# stages.json 文档级缓存（供 cross_cutting 名称读取，独立于 stages 列表缓存）
_DOC_CACHE = None


def _load_doc(force=False):
    global _DOC_CACHE
    if _DOC_CACHE is not None and not force:
        return _DOC_CACHE
    with open(STAGES_FILE, "r", encoding="utf-8") as f:
        _DOC_CACHE = json.load(f)
    return _DOC_CACHE


def load_cross_cutting_names(force=False):
    """返回 stages.json 顶层 cross_cutting 名称数组（与 4 个字符串消费者同一来源）。"""
    return _load_doc(force=force).get("cross_cutting", [])


def resolve_stages(doc=None, force=False):
    """合并 domain_extensions 后的有效阶段列表（平台基线 + 领域 insert/replace）。

    - ``insert``：在指定阶段之后插入领域阶段（领域节点可定制，走同一上报协议）。
    - ``replace``：覆盖某阶段定义，但若该阶段在 ``locked_stages`` 中则**忽略**
      （平台强保障节点不可改）。
    - 默认（生产 stages.json 的 domain_extensions 为空）→ 返回与 load_stages() 一致的基线，
      因此不改变既有路由行为（零漂移风险，详见 W7 增强）。
    """
    if doc is None:
        doc = _load_doc(force=force)
    base = doc.get("stages", [])
    ext = doc.get("domain_extensions") or {}
    locked = set(ext.get("locked_stages", []))
    inserts = ext.get("insert") or []
    replaces = ext.get("replace") or {}
    result = []
    for st in base:
        if st["dir"] in replaces and st["dir"] not in locked:
            result.append(dict(replaces[st["dir"]]))
        else:
            result.append(st)
        for ins in inserts:
            if ins.get("after") == st["dir"]:
                result.append(dict(ins.get("stage", {})))
    return result


def recommend_cross_cutting(change_dir, stages_list=None):
    """扫描变更目录，返回被触发的横切技能推荐列表 [{skill, reason}]。

    触发依据（见 CROSS_CUTTING_TRIGGERS）：
      - suffixes：任意文件后缀命中
      - names：文件名（子串）命中
      - keywords：文件相对路径 / 文件名含关键词
      - min_stage_done：已完成的 8 阶段数 >= 阈值（需 stages_list）
    仅推荐 cross_cutting 名称数组内的技能，保证与注册表一致。
    """
    names = load_cross_cutting_names()
    if stages_list is None:
        stages_list = load_stages()
    files = []
    if os.path.isdir(change_dir):
        for root, dirs, fnames in os.walk(change_dir):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for fn in fnames:
                if fn.startswith("."):
                    continue
                files.append(os.path.relpath(os.path.join(root, fn), change_dir).lower())
    done_count = 0
    for st in stages_list:
        sd = os.path.join(change_dir, st["dir"])
        if is_stage_done(sd, st):
            done_count += 1
    recs = []
    for skill in names:
        rule = CROSS_CUTTING_TRIGGERS.get(skill)
        if not rule:
            continue
        hit = False
        for fp in files:
            base = os.path.basename(fp)
            if any(fp.endswith(s) for s in rule.get("suffixes", [])):
                hit = True
                break
            if any(n.lower() in base for n in rule.get("names", [])):
                hit = True
                break
            if any(k.lower() in fp for k in rule.get("keywords", [])):
                hit = True
                break
        if not hit:
            msd = rule.get("min_stage_done")
            if msd is not None and done_count >= msd:
                hit = True
        if hit:
            recs.append({"skill": skill, "reason": rule.get("reason", "")})
    return recs


# ----------------------------------------------------------------------------
# 横切技能执行追踪（P1-9：close_loop 侧）
# change_dir 下维护 cross_cutting_done.json，记录哪些横切技能已实际跑过。
# 默认不强制——未跑的高相关横切仅提示；仅 --strict-cross 转门禁。
# ----------------------------------------------------------------------------
CROSS_DONE_FILE = "cross_cutting_done.json"


def load_cross_cutting_done(change_dir):
    p = os.path.join(change_dir, CROSS_DONE_FILE)
    if os.path.isfile(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                d = json.load(f)
            return set(d.get("done", []))
        except Exception:
            pass
    return set()


def mark_cross_cutting(change_dir, skill):
    """记录某横切技能已在本次变更中执行；返回是否成功写入。"""
    if not os.path.isdir(change_dir):
        return False
    done = load_cross_cutting_done(change_dir)
    done.add(skill)
    p = os.path.join(change_dir, CROSS_DONE_FILE)
    try:
        with open(p, "w", encoding="utf-8") as f:
            json.dump({"done": sorted(done)}, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False
