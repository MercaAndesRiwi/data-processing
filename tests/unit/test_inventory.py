"""Inventory shares the catalog ID space and is deterministic (F3)."""

import random

from src.common.master_catalog import build_master_catalog
from src.simulators.inventory_api.stock import stock_level


def test_inventory_uses_catalog_ids_and_is_stable():
    catalog = build_master_catalog(seed=42, per_category=2)
    rng = random.Random(9)
    product = rng.choice(catalog.active_products)
    store = catalog.random_store_for_country(rng, product.country)

    first = stock_level(42, product.sku, store.store_id)
    second = stock_level(42, product.sku, store.store_id)
    assert first == second
    assert 0 <= first <= 450
    assert product.sku in {p.sku for p in catalog.products}
    assert store.store_id in {s.store_id for s in catalog.stores}
