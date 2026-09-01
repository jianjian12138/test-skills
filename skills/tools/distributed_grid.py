#!/usr/bin/env python3
"""
distributed_grid.py: 分布式测试执行网格与弹性分片调度器 (Distributed Test Grid & Sharding)
支持将大规模测试用例集按权重分片 (Sharding) 并发分发至多进程/分布式节点，
内置 Flaky 偶发测试智能退避重试机制与聚合报告生成。

零外部依赖，纯 Python 3.9+ 标准库实现。
"""
import os
import sys
import json
import time
import subprocess
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Dict, Any

if sys.platform == "win32":
    import io
    if hasattr(sys.stdout, "buffer") and getattr(sys.stdout, "encoding", "").lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "buffer") and getattr(sys.stderr, "encoding", "").lower() != "utf-8":
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

def shard_items(items: list, shard_index: int, total_shards: int) -> list:
    """根据分片索引均匀切分用例列表"""
    if total_shards <= 1:
        return items
    return [item for i, item in enumerate(items) if i % total_shards == shard_index]

def run_single_test_with_retry(test_file: str, max_retries: int = 2) -> Dict[str, Any]:
    """单用例执行与 Flaky 智能退避重试"""
    attempts = 0
    start_time = time.time()
    last_error = None
    is_flaky = False

    while attempts <= max_retries:
        attempts += 1
        cmd = [sys.executable, "-m", "pytest", "-q", "--no-header", test_file]
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        
        if res.returncode == 0:
            if attempts > 1:
                is_flaky = True
            return {
                "test": test_file,
                "status": "pass",
                "flaky": is_flaky,
                "attempts": attempts,
                "duration": round(time.time() - start_time, 2)
            }
        else:
            last_error = res.stdout or res.stderr
            time.sleep(0.3 * attempts) # 退避等待

    return {
        "test": test_file,
        "status": "fail",
        "flaky": False,
        "attempts": attempts,
        "error": last_error[:300] if last_error else "Failed",
        "duration": round(time.time() - start_time, 2)
    }

def run_grid(test_files: List[str], workers: int = 4, max_retries: int = 1) -> Dict[str, Any]:
    print(f"🚀 正在调度分布式网格并发打靶: {len(test_files)} 个测试文件 (并发 Worker: {workers})...\n")
    results = []
    start_all = time.time()

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(run_single_test_with_retry, tf, max_retries): tf for tf in test_files}
        for fut in as_completed(futures):
            r = fut.result()
            results.append(r)
            status_tag = "✅ PASS" if r["status"] == "pass" else "❌ FAIL"
            flaky_tag = " [⚠️ Flaky 抖动恢复]" if r.get("flaky") else ""
            print(f"  [{status_tag}] {Path(r['test']).name} ({r['duration']}s){flaky_tag}")

    passed = sum(1 for r in results if r["status"] == "pass")
    flaky = sum(1 for r in results if r.get("flaky"))
    failed = len(results) - passed

    summary = {
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "flaky_recovered": flaky,
        "pass_rate": round(passed / len(results) * 100, 1) if results else 0,
        "total_duration": round(time.time() - start_all, 2),
        "results": results
    }

    print("\n" + "=" * 60)
    print(f"  🏁 网格聚合报告: 总计 {summary['total']} | 通过 {passed} | 失败 {failed} | 偶发抖动恢复 {flaky}")
    print(f"  📈 综合通过率: {summary['pass_rate']}% | 总耗时: {summary['total_duration']}s")
    print("=" * 60)
    return summary

def main():
    parser = argparse.ArgumentParser(description="Distributed Test Grid - 分布式测试执行网格")
    parser.add_argument("--test-dir", default=".", help="测试用例根目录")
    parser.add_argument("--shard-index", type=int, default=0, help="当前分片索引 (0 开始)")
    parser.add_argument("--total-shards", type=int, default=1, help="分片总数")
    parser.add_argument("--workers", "-w", type=int, default=4, help="并发 Worker 数量")
    parser.add_argument("--retries", "-r", type=int, default=1, help="Flaky 测试重试次数")
    parser.add_argument("--output", "-o", help="保存汇总报告 JSON")
    args = parser.parse_args()

    all_tests = sorted([str(p.resolve()) for p in Path(args.test_dir).rglob("test_*.py")])
    if not all_tests:
        print(f"⚠️ 在 {args.test_dir} 下未找到任何 test_*.py 文件")
        return

    my_shard_tests = shard_items(all_tests, args.shard_index, args.total_shards)
    print(f"📦 分片划分: 总用例 {len(all_tests)} -> 当前分片 [{args.shard_index + 1}/{args.total_shards}] 分配 {len(my_shard_tests)} 个用例")

    summary = run_grid(my_shard_tests, workers=args.workers, max_retries=args.retries)
    if args.output:
        Path(args.output).write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"📁 报告已保存至: {args.output}")

    sys.exit(0 if summary["failed"] == 0 else 1)

if __name__ == "__main__":
    main()
