#!/usr/bin/env python3
"""Compatibility bridge: delegates legacy v11 traffic_shadow calls to L6.0 shadow_qa engine."""

from __future__ import annotations

from .shadow_qa import diff_shadow_traffic, scrub_volatile_fields

__all__ = ["diff_shadow_traffic", "scrub_volatile_fields"]
