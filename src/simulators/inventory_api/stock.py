"""Minimal inventory snapshot from the shared master catalog (F3).

Stock per (sku, store) is deterministic from (seed, sku, store_id),
so the mock API, POS and events never diverge on IDs.
"""

from __future__ import annotations

import hashlib
import random


def stock_level(seed: int, sku: str, store_id: str, max_stock: int = 450) -> int:
    """Deterministic on-hand units for one SKU in one store."""
    digest = hashlib.sha256(f"{seed}-{sku}-{store_id}".encode()).digest()
    rng = random.Random(int.from_bytes(digest[:8], "big"))
    return rng.randint(0, max_stock)
