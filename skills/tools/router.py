#!/usr/bin/env python3
"""L1/L2 Progressive Skill Router & Distributed Trace / Token Cost Ledger."""

from __future__ import annotations

import json
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

trace_id_var: ContextVar[str] = ContextVar("trace_id", default="tr-init0000")


def new_trace_id(prefix: str = "tr") -> str:
    """Generate and bind a new distributed trace ID in contextvars."""
    tid = f"{prefix}-{uuid.uuid4().hex[:8]}"
    trace_id_var.set(tid)
    return tid


def get_trace_id() -> str:
    """Return current contextvars trace ID."""
    return trace_id_var.get()


@dataclass
class TokenCostLedger:
    """Tracks token savings achieved by L1/L2 progressive disclosure vs full dump."""

    full_dump_tokens_per_turn: int = 15200
    l1_routed_tokens: int = 0
    l2_loaded_tokens: int = 0
    turns: int = 0
    events: list[dict[str, Any]] = field(default_factory=list)

    def record_route(self, candidate_count: int, l1_tokens: int) -> None:
        self.turns += 1
        self.l1_routed_tokens += l1_tokens
        self.events.append({
            "trace_id": get_trace_id(),
            "event": "l1_route",
            "candidates": candidate_count,
            "tokens_used": l1_tokens,
            "tokens_saved": max(0, self.full_dump_tokens_per_turn - l1_tokens),
        })

    def record_l2_load(self, skill_id: str, l2_tokens: int) -> None:
        self.l2_loaded_tokens += l2_tokens
        self.events.append({
            "trace_id": get_trace_id(),
            "event": "l2_load_sop",
            "skill_id": skill_id,
            "tokens_used": l2_tokens,
        })

    def summary(self) -> dict[str, Any]:
        baseline = max(1, self.turns) * self.full_dump_tokens_per_turn
        actual = self.l1_routed_tokens + self.l2_loaded_tokens
        saved_Ratio = round((1.0 - (actual / baseline)) * 100.0, 2) if baseline else 0.0
        return {
            "trace_id": get_trace_id(),
            "turns": self.turns,
            "baseline_full_dump_tokens": baseline,
            "actual_progressive_tokens": actual,
            "token_reduction_pct": saved_Ratio,
        }


class ProgressiveSkillRouter:
    """Routes user QA queries across 40 skills down to <= 5 high-signal candidates."""

    def __init__(self, repo_root: Path | None = None) -> None:
        self.repo_root = repo_root or Path(__file__).resolve().parents[2]
        self.registry_path = self.repo_root / "skills" / "registry.json"
        self.ledger = TokenCostLedger()
        self._registry_data = self._load_registry()

    def _load_registry(self) -> list[dict[str, Any]]:
        if not self.registry_path.exists():
            return []
        raw = json.loads(self.registry_path.read_text(encoding="utf-8"))
        return raw.get("skills", [])

    def list_all(self, stage: str = "") -> list[dict[str, Any]]:
        if not stage:
            return self._registry_data
        return [s for s in self._registry_data if s.get("stage") == stage]

    def route(self, query: str, stage: str = "", top_k: int = 4) -> dict[str, Any]:
        """Filter 40 skills to <= 5 candidates using keyword, tag, and stage affinity."""
        if not query.strip() and not stage:
            selected = self._registry_data[: min(top_k, 5)]
        else:
            q_lower = query.lower().strip()
            q_terms = [t for t in q_lower.replace("-", " ").split() if t]
            scored: list[tuple[float, dict[str, Any]]] = []
            for skill in self._registry_data:
                if stage and skill.get("stage") != stage:
                    continue
                score = 0.0
                sid = str(skill.get("id", "")).lower()
                title = str(skill.get("title", "")).lower()
                summary = str(skill.get("l1_summary", "")).lower()
                tags = [str(t).lower() for t in skill.get("tags", [])]

                if q_lower and q_lower in sid:
                    score += 12.0
                if q_lower and q_lower in title:
                    score += 10.0
                if q_lower and q_lower in summary:
                    score += 6.0
                for term in q_terms:
                    if term in tags:
                        score += 5.0
                    elif any(term in tg for tg in tags):
                        score += 3.0
                    if term in sid or term in title or term in summary:
                        score += 2.5
                if stage and skill.get("stage") == stage:
                    score += 4.0
                scored.append((score, skill))

            scored.sort(key=lambda item: (-item[0], item[1].get("index", 999)))
            positive = [item[1] for item in scored if item[0] > 0]
            selected = (positive or [item[1] for item in scored])[: min(max(1, top_k), 5)]

        l1_candidates = [
            {
                "id": s["id"],
                "title": s["title"],
                "stage": s["stage"],
                "tier": s["tier"],
                "l1_summary": s["l1_summary"],
                "mcp_tool_binding": s["mcp_tool_binding"],
            }
            for s in selected
        ]
        used_tokens = sum(int(s.get("l1_tokens", 42)) for s in selected)
        self.ledger.record_route(len(l1_candidates), used_tokens)
        return {
            "trace_id": get_trace_id(),
            "query": query,
            "stage_filter": stage or "ALL",
            "candidate_count": len(l1_candidates),
            "candidates": l1_candidates,
            "telemetry": self.ledger.summary(),
        }

    def load_skill_sop(self, skill_id: str) -> dict[str, Any]:
        """Stage 2 Progressive Loader: Load full SKILL.md SOP only for selected skill."""
        target = next((s for s in self._registry_data if s.get("id") == skill_id), None)
        if not target:
            return {
                "trace_id": get_trace_id(),
                "status": "error",
                "error": f"Skill '{skill_id}' not found in registry.",
            }
        sop_file = self.repo_root / str(target.get("sop_path", f"skills/{skill_id}/SKILL.md"))
        content = sop_file.read_text(encoding="utf-8") if sop_file.exists() else ""
        self.ledger.record_l2_load(skill_id, int(target.get("l2_tokens", 380)))
        return {
            "trace_id": get_trace_id(),
            "status": "ok",
            "skill_id": skill_id,
            "title": target.get("title"),
            "tier": target.get("tier"),
            "mcp_tool_binding": target.get("mcp_tool_binding"),
            "sop_markdown": content,
            "telemetry": self.ledger.summary(),
        }
