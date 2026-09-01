#!/usr/bin/env python3
"""统一 CI 门禁入口（R-02 硬化）：一条命令跑齐四道闸 + REGISTRY 派生校验，fail-closed。

闸顺序（任一非零即整体失败，退出码 1）：
  1. compileall -q        —— 全脚本可编译（零第三方依赖）
  2. REGISTRY 派生一致性  —— 重建 REGISTRY.json（临时），与已提交版做「本质一致性」比对
                            （name/category/stage/tier/scripts/orchestrated，忽略日期类字段）；
                            捕获「新增 qa-* 未进 REGISTRY / REGISTRY 静默脱管」漂移。
  3. check_drift          —— 启用 --require-verified --strict-meta（R-02：硬化默认关的两道可选严格闸）
  4. gen_common(--check)  —— R-10：5 份 vendored _common.py 与单一模板字节一致（单源生成，CI 干跑不写文件）
  5. validate_portability —— 跨 agent 可移植性
  6. run_all_tests        —— golden 自测（含异常路径 fail-closed）

用法：
    python tools/run_gates.py
退出码：全绿 0；任一闸失败 1。
"""
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # skills/
PY = sys.executable


def step(name, cmd, cwd=ROOT):
    print(f"\n=== [{name}] ===")
    rc = subprocess.run(cmd, cwd=cwd).returncode
    if rc != 0:
        print(f"  ✗ {name} 失败 (rc={rc})")
    else:
        print(f"  ✓ {name} 通过")
    return rc


def registry_consistency():
    """重建 REGISTRY 到默认位置，与已提交版做本质一致性比对（忽略日期字段）。"""
    print("\n=== [REGISTRY 派生一致性] ===")
    reg_path = os.path.join(ROOT, "REGISTRY.json")
    with open(reg_path, encoding="utf-8") as f:
        committed_text = f.read()
    committed_obj = json.loads(committed_text)
    try:
        rc = subprocess.run([PY, os.path.join(ROOT, "build_registry.py")], cwd=ROOT).returncode
        if rc != 0:
            print("  ✗ build_registry.py 失败")
            return rc
        fresh = json.load(open(reg_path, encoding="utf-8"))

        def essentials(o):
            out = {}
            for s in o.get("skills", []):
                out[s.get("name")] = (
                    s.get("category"), s.get("stage"), s.get("tier"),
                    tuple(s.get("scripts", [])), bool(s.get("orchestrated")),
                )
            return out

        ec, ef = essentials(committed_obj), essentials(fresh)
        if ec != ef:
            diffs = []
            for name in sorted(set(ec) | set(ef)):
                if ec.get(name) != ef.get(name):
                    diffs.append(f"{name}: committed={ec.get(name)} fresh={ef.get(name)}")
            print("  ✗ REGISTRY 派生与已提交版本质不一致"
                  "（新增/删除技能或修改 metadata 后须重跑 build_registry.py）：")
            for d in diffs[:20]:
                print("    - " + d)
            return 1
        print("  ✓ REGISTRY 派生与已提交版一致（无脱管/漂移）")
        return 0
    finally:
        # 还原已提交版（写回内存原文，避免删除触发安全删除钩子）；CI 只报告不自动改写产物
        with open(reg_path, "w", encoding="utf-8") as f:
            f.write(committed_text)


def main():
    failures = []
    if step("compileall", [PY, "-m", "compileall", "-q", ROOT]) != 0:
        failures.append("compileall")
    if registry_consistency() != 0:
        failures.append("registry_consistency")
    if step("check_drift(--require-verified --strict-meta)",
            [PY, os.path.join(ROOT, "qa-orchestrator", "scripts", "check_drift.py"),
             "--require-verified", "--strict-meta"]) != 0:
        failures.append("check_drift")
    if step("gen_common(--check 单源一致性)",
            [PY, os.path.join(ROOT, "tools", "gen_common.py"), "--check"]) != 0:
        failures.append("gen_common_check")
    if step("validate_portability",
            [PY, os.path.join(ROOT, "tools", "validate_portability.py")]) != 0:
        failures.append("validate_portability")
    if step("run_all_tests",
            [PY, os.path.join(ROOT, "tests", "run_all_tests.py")]) != 0:
        failures.append("run_all_tests")

    print("\n" + "=" * 60)
    if failures:
        print(f"[FAIL] 以下闸未通过：{failures}（fail-closed，exit 1）")
        return 1
    print("[PASS] 全部门禁通过（compileall / REGISTRY派生 / check_drift(strict) / "
          "gen_common(--check) / validate_portability / run_all_tests）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
