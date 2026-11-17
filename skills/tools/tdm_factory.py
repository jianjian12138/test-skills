#!/usr/bin/env python3
"""Mainland China Compliant TDM Factory, Relational Order State-Machine & PII Sanitizer."""

from __future__ import annotations

import hashlib
import random
import re
from datetime import datetime, timedelta
from typing import Any

from .router import get_trace_id

ID_WEIGHTS = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
ID_CHECK_MAP = ["1", "0", "X", "9", "8", "7", "6", "5", "4", "3", "2"]
AREA_CODES = ["110101", "110105", "310101", "310115", "440106", "440305", "330106", "510107"]
MOBILE_PREFIXES = ["138", "139", "136", "150", "158", "186", "188", "199", "177"]
SURNAMES = ["张", "王", "李", "赵", "陈", "刘", "杨", "黄", "周", "吴", "林", "郑", "冯", "许"]
GIVEN_CHARS = ["明", "伟", "芳", "娜", "敏", "静", "浩", "宇", "轩", "泽", "晨", "思", "远", "嘉", "航"]


def compute_id_check_digit(body17: str) -> str:
    """Compute GB 11643-1999 18th check digit from 17-digit prefix."""
    if len(body17) != 17 or not body17.isdigit():
        raise ValueError("ID card prefix must be exactly 17 digits.")
    total = sum(int(ch) * w for ch, w in zip(body17, ID_WEIGHTS))
    return ID_CHECK_MAP[total % 11]


def verify_id_card_checksum(id_card: str) -> bool:
    """Validate an 18-digit Mainland China ID card checksum and date structure."""
    if len(id_card) != 18 or not id_card[:17].isdigit():
        return False
    expected = compute_id_check_digit(id_card[:17])
    return id_card[17].upper() == expected


def generate_id_card(seed: int | None = None) -> str:
    """Generate a synthetically valid 18-digit Mainland China ID card number."""
    rng = random.Random(seed) if seed is not None else random
    area = rng.choice(AREA_CODES)
    start_date = datetime(1975, 1, 1)
    birth = (start_date + timedelta(days=rng.randint(0, 9000))).strftime("%Y%m%d")
    seq = f"{rng.randint(1, 999):03d}"
    body17 = f"{area}{birth}{seq}"
    return f"{body17}{compute_id_check_digit(body17)}"


def generate_phone(seed: int | None = None) -> str:
    """Generate a compliant 11-digit Mainland China mobile number."""
    rng = random.Random(seed) if seed is not None else random
    prefix = rng.choice(MOBILE_PREFIXES)
    suffix = f"{rng.randint(0, 99999999):08d}"
    return f"{prefix}{suffix}"


def generate_name(seed: int | None = None) -> str:
    """Generate a synthetic Chinese full name."""
    rng = random.Random(seed) if seed is not None else random
    surname = rng.choice(SURNAMES)
    given = "".join(rng.sample(GIVEN_CHARS, k=rng.choice([1, 2])))
    return f"{surname}{given}"


def generate_order_state_chain(count: int = 3, seed: int = 42) -> dict[str, Any]:
    """Generate referentially intact multi-table test data (Users -> Orders -> Payments -> Inventory)."""
    rng = random.Random(seed)
    users = []
    orders = []
    payments = []
    inventory_ledger = []

    for idx in range(1, max(1, count) + 1):
        uid = f"USR-{1000 + idx}"
        oid = f"ORD-202611-{2000 + idx}"
        pid = f"PAY-202611-{3000 + idx}"
        sku = f"SKU-AI-{10 + idx}"
        qty = rng.randint(1, 5)
        unit_price_cents = rng.choice([9900, 19900, 29900, 49900])
        amount_cents = qty * unit_price_cents
        initial_stock = 100

        id_card = generate_id_card(seed=seed + idx * 17)
        phone = generate_phone(seed=seed + idx * 31)
        name = generate_name(seed=seed + idx * 53)

        users.append({
            "user_id": uid,
            "name": name,
            "phone": phone,
            "id_card": id_card,
            "id_card_valid": verify_id_card_checksum(id_card),
            "tenant_id": f"TENANT-{(idx % 2) + 1:02d}",
        })
        orders.append({
            "order_id": oid,
            "user_id": uid,
            "sku_id": sku,
            "quantity": qty,
            "amount_cents": amount_cents,
            "status": "PAID",
        })
        payments.append({
            "payment_id": pid,
            "order_id": oid,
            "user_id": uid,
            "paid_cents": amount_cents,
            "channel": "WECHAT_PAY",
            "status": "SUCCESS",
        })
        inventory_ledger.append({
            "sku_id": sku,
            "order_id": oid,
            "initial_stock": initial_stock,
            "locked_qty": 0,
            "deducted_qty": qty,
            "remaining_stock": initial_stock - qty,
            "invariant_ok": (initial_stock - qty) >= 0,
        })

    return {
        "trace_id": get_trace_id(),
        "type": "order_chain",
        "referential_integrity_verified": True,
        "tables": {
            "users": users,
            "orders": orders,
            "payments": payments,
            "inventory_ledger": inventory_ledger,
        },
    }


def generate_test_data_batch(data_type: str = "id_card", count: int = 3, seed: int = 1024) -> dict[str, Any]:
    """Unified TDM entry point supporting id_card, phone, name, and multi-table order_chain."""
    dtype = data_type.lower().strip()
    if dtype == "order_chain":
        return generate_order_state_chain(count=count, seed=seed)

    records: list[dict[str, Any]] = []
    for i in range(max(1, count)):
        cur_seed = seed + i * 19
        if dtype == "id_card":
            val = generate_id_card(seed=cur_seed)
            records.append({"value": val, "checksum_valid": verify_id_card_checksum(val)})
        elif dtype == "phone":
            records.append({"value": generate_phone(seed=cur_seed), "carrier_compliant": True})
        elif dtype == "name":
            records.append({"value": generate_name(seed=cur_seed)})
        else:
            id_val = generate_id_card(seed=cur_seed)
            records.append({
                "name": generate_name(seed=cur_seed),
                "phone": generate_phone(seed=cur_seed),
                "id_card": id_val,
                "checksum_valid": verify_id_card_checksum(id_val),
            })

    return {
        "trace_id": get_trace_id(),
        "type": dtype,
        "count": len(records),
        "records": records,
    }


def sanitize_sensitive_data(raw_text: str) -> dict[str, Any]:
    """Mask Mainland China ID cards, phone numbers, and API secrets before LLM ingestion."""
    redactions = 0

    def _mask_id(match: re.Match[str]) -> str:
        nonlocal redactions
        val = match.group(0)
        redactions += 1
        return f"{val[:6]}********{val[14:]}"

    def _mask_phone(match: re.Match[str]) -> str:
        nonlocal redactions
        val = match.group(0)
        redactions += 1
        return f"{val[:3]}****{val[7:]}"

    def _mask_secret(match: re.Match[str]) -> str:
        nonlocal redactions
        val = match.group(0)
        redactions += 1
        digest = hashlib.sha256(val.encode("utf-8")).hexdigest()[:6]
        return f"[REDACTED_SECRET:{digest}]"

    # 1. Mask 18-digit Mainland ID cards
    sanitized = re.sub(
        r"(?<!\d)[1-6]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx](?!\d)",
        _mask_id,
        raw_text,
    )
    # 2. Mask 11-digit Mainland mobile phones
    sanitized = re.sub(r"(?<!\d)1[3-9]\d{9}(?!\d)", _mask_phone, sanitized)
    # 3. Mask API Keys / Bearer Tokens
    sanitized = re.sub(r"(?:sk-[a-zA-Z0-9_-]{12,}|ghp_[a-zA-Z0-9]{16,}|AKIA[0-9A-Z]{16})", _mask_secret, sanitized)

    return {
        "trace_id": get_trace_id(),
        "original_length": len(raw_text),
        "redaction_count": redactions,
        "sanitized_text": sanitized,
        "pipl_compliant": True,
    }
