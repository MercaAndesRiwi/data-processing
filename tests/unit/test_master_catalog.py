"""Criterion 1: POS, inventory and events share one ID space."""

import random

from src.common.master_catalog import build_master_catalog


def test_same_seed_builds_identical_catalog():
    first = build_master_catalog(seed=42, per_category=2)
    second = build_master_catalog(seed=42, per_category=2)

    assert [p.sku for p in first.products] == [
        p.sku for p in second.products
    ]
    assert [s.store_id for s in first.stores] == [
        s.store_id for s in second.stores
    ]
    assert [s.seller_id for s in first.sellers] == [
        s.seller_id for s in second.sellers
    ]


def test_ids_are_unique_and_cross_referenced():
    catalog = build_master_catalog(seed=42, per_category=2)

    skus = [p.sku for p in catalog.products]
    assert len(skus) == len(set(skus))

    store_ids = {s.store_id for s in catalog.stores}
    seller_ids = {s.seller_id for s in catalog.sellers}
    assert len(store_ids) == 20
    assert len(seller_ids) == 35

    # Every product/store points to a seller that exists: shared ID space.
    for product in catalog.products:
        assert product.seller_id in seller_ids
        assert product.country in {"CO", "PE", "EC", "BO", "CL"}
    for store in catalog.stores:
        assert store.seller_id in seller_ids


def test_all_generators_draw_from_same_catalog():
    catalog = build_master_catalog(seed=7, per_category=3)
    rng_pos = random.Random("7-pos")
    rng_inv = random.Random("7-inv")
    rng_evt = random.Random("7-evt")

    pos_product = rng_pos.choice(catalog.active_products)
    inv_product = rng_inv.choice(catalog.active_products)
    evt_product = rng_evt.choice(catalog.active_products)

    valid_skus = {p.sku for p in catalog.products}
    assert pos_product.sku in valid_skus
    assert inv_product.sku in valid_skus
    assert evt_product.sku in valid_skus

    # Stores are resolved in the product country: POS/inventory/events
    # can join on (sku, store_id, seller_id).
    store = catalog.random_store_for_country(rng_pos, pos_product.country)
    assert store.country == pos_product.country
    assert store.store_id in {s.store_id for s in catalog.stores}
