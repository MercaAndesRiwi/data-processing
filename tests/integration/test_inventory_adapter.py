"""Integration tests for the shared inventory adapter."""

from src.common.master_catalog import build_master_catalog
from src.ingestion.inventory.adapter import build_inventory_snapshot


def test_inventory_uses_catalog_ids_and_is_deterministic():
    first = build_inventory_snapshot(seed=42, per_category=2)
    second = build_inventory_snapshot(seed=42, per_category=2)

    catalog = build_master_catalog(seed=42, per_category=2)

    assert first == second
    assert first

    for item in first:
        assert item["sku"] in catalog.products_by_sku
        assert item["store_id"] in catalog.stores_by_id
        assert item["seller_id"] in catalog.sellers_by_id
        assert item["product_seller_id"] in catalog.sellers_by_id
        assert 0 <= item["quantity"] <= 450

        product = catalog.products_by_sku[item["sku"]]
        store = catalog.stores_by_id[item["store_id"]]

        assert product.country == store.country
        assert item["seller_id"] == store.seller_id
        assert item["product_seller_id"] == product.seller_id
