#!/usr/bin/env python3
"""依赖图生成器（P2 工程化）：由 qa-orchestrator/stages.json 渲染 Mermaid 流程/依赖图，
输出 docs/DEPENDENCY_GRAPH.md。零依赖。

图形表达：
- 8 个生命周期阶段串联（需求→归档）
- 每阶段下列出其技能（主技能 + alternates）
- 横切关注点（cross_cutting）以虚线贯穿各阶段
"""
import json
import os

SKILLS_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def nid(s):
    return s.replace("-", "_")


def main():
    stages_doc = load_json(os.path.join(SKILLS_ROOT, "qa-orchestrator", "stages.json"))
    stages = stages_doc["stages"]
    cross = stages_doc.get("cross_cutting", [])

    L = ["# 技能依赖图（由 stages.json 自动生成）", "",
         "> 阶段纵向串联，主技能 + 备选技能隶属各阶段；横切关注点以虚线贯穿全程。", "",
         "```mermaid", "flowchart TD"]

    prev = None
    for st in stages:
        key = st["dir"].split("-")[0]            # 01..08
        L.append(f'    {key}["{st["title"]}"]')
        members = list(st.get("skills", [])) + list(st.get("alternates", []))
        for sk in members:
            L.append(f'    {key}_{nid(sk)}["{sk}"]')
            L.append(f'    {key} --> {key}_{nid(sk)}')
        if prev:
            L.append(f'    {prev} --> {key}')
        prev = key

    # 横切关注点：虚线连到每个阶段，表达「贯穿」
    for cc in cross:
        L.append(f'    CC_{nid(cc)}["{cc}<br/>· 横切门禁"]')
    for cc in cross:
        for st in stages:
            key = st["dir"].split("-")[0]
            L.append(f'    CC_{nid(cc)} -.-> {key}')

    # R-11：agent_testing 维度（独立，不接入 8 阶段路由）——补维度节点，使依赖图与
    # stages.json 维度对称（stages 仅含 8 生命阶段，agent_testing 为独立 category）。
    reg = load_json(os.path.join(SKILLS_ROOT, "REGISTRY.json"))
    agent_skills = [s["name"] for s in reg.get("skills", []) if s.get("category") == "agent"]
    if agent_skills:
        L.append(f'    subgraph AT["agent_testing 维度（独立，不接入 8 阶段路由）"]')
        for sk in agent_skills:
            L.append(f'        AT_{nid(sk)}["{sk}"]')
            L.append(f'        AT --> AT_{nid(sk)}')
        L.append('    end')

    # RK-P3-20：信号数据依赖边——扫描各技能脚本中调用 emit_signal 的生产者，
    # 画一条实线到 qa-release-check（信号消费者 / 发布门禁），表达"数据依赖"。
    consumers = "qa_release_check"
    L.append(f'    {consumers}["qa-release-check<br/>· 信号消费/发布门禁"]')
    for root, _, files in os.walk(SKILLS_ROOT):
        if "SKILL.md" not in files:
            continue
        skill = os.path.basename(root)
        if skill == "qa-release-check":
            continue
        # R-35 修复：脚本均在 scripts/ 子目录，须递归扫描整棵技能子树，
        # 否则直接层 files 不含 .py，emit_signal 永远探测不到 → 信号边缺失（文档漂移）。
        emits = False
        for dirpath, _, fnames in os.walk(root):
            for fn in fnames:
                if not fn.endswith(".py"):
                    continue
                try:
                    txt = open(os.path.join(dirpath, fn), encoding="utf-8").read()
                except Exception:
                    continue
                if "emit_signal" in txt:
                    emits = True
                    break
            if emits:
                break
        if emits:
            L.append(f'    {nid(skill)} -->|signals| {consumers}')

    L.append("```")
    L.append("")
    L.append("> **维度说明**：上图含 8 个生命周期阶段（stages.json）+ 横切关注点（虚线贯穿）+ 信号数据依赖边。"
             + (" `agent_testing` 为**独立维度**，含 `" + "`、`".join(agent_skills) + "` 两个 Agent 测试技能，"
                if agent_skills else "（注：`agent_testing` 维度当前为空。）")
             + "不接入 8 阶段路由、独立于阶段流之外，详见 `REGISTRY.json`（`category=agent`）与 `stages.json`（`agent_testing` 维度）。")
    L.append("")

    out_dir = os.path.join(SKILLS_ROOT, "docs")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "DEPENDENCY_GRAPH.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print(f"[OK] 已生成依赖图: {out_path}（阶段 {len(stages)} 个，横切 {len(cross)} 个）")


if __name__ == "__main__":
    main()
