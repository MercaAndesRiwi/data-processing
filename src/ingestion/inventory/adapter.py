"""Build inventory records using the shared master catalog."""
from typing import Any
from src.common.config import (
    CATALOG_PER_CATEGORY,
    MASTER_SEED,
)
from src.common.master_catalog import build_master_catalog
from src.simulators.inventory_api.stock import stock_level


def build_inventory_snapshot(
    seed: int = MASTER_SEED,
    per_category: int = CATALOG_PER_CATEGORY,
    max_stock: int = 450,
) -> list[dict[str, Any]]:
    """Build deterministic inventory records for active products.

    Each product is paired with every store in the same country.
    The store seller and product seller are kept as separate fields.
    """

    if max_stock < 0:
        raise ValueError("max_stock must be non-negative.")

    catalog = build_master_catalog(
        seed=seed,
        per_category=per_category,
    )

    stores_by_country: dict[str, list] = {}

    for store in catalog.stores:
        stores_by_country.setdefault(store.country, []).append(store)

    inventory: list[dict[str, Any]] = []

    for product in catalog.active_products:
        country_stores = stores_by_country.get(product.country, [])

        for store in country_stores:
            quantity = stock_level(
                seed,
                product.sku,
                store.store_id,
                max_stock=max_stock,
            )

            inventory.append(
                {
                    "sku": product.sku,
                    "store_id": store.store_id,
                    "seller_id": store.seller_id,
                    "product_seller_id": product.seller_id,
                    "quantity": quantity,
                }
            )

    return inventory
