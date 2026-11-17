#!/usr/bin/env python3
"""Distributed Test Grid Sharding & Parallel Partitioning Engine."""

from __future__ import annotations


def shard_test_cases(test_ids: list[str], total_shards: int = 4) -> dict[int, list[str]]:
    shards: dict[int, list[str]] = {i: [] for i in range(max(1, total_shards))}
    for idx, tid in enumerate(sorted(test_ids)):
        shards[idx % max(1, total_shards)].append(tid)
    return shards
