"""Catalog-backed inventory API for F3 integration."""

import os
import random
from math import ceil
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from src.common.config import MASTER_SEED
from src.common.master_catalog import build_master_catalog
from src.simulators.inventory_api.stock import stock_level


app = FastAPI(
    title="MercaAndes Catalog Inventory API",
    version="1.0.0",
    description="Inventory API backed by the shared master catalog.",
)

security_scheme = HTTPBearer()

ERROR_RATE = float(os.getenv("ERROR_RATE", "0.03"))
ENABLE_NEGATIVE_INVENTORY = (
    os.getenv("ENABLE_NEGATIVE_INVENTORY", "true").lower() == "true"
)
VALID_TOKENS = {
    "token-seller-123",
    "bearer-token-mercaandes-2026",
    "test-token",
}


class InventoryItem(BaseModel):
    sku: str
    store_id: str
    seller_id: str
    product_seller_id: str
    quantity: int


class PaginatedInventoryResponse(BaseModel):
    seller_id: str
    page: int
    limit: int
    total_items: int
    total_pages: int
    data: list[InventoryItem]


@app.get(
    "/api/v1/sellers/{seller_id}/inventory",
    response_model=PaginatedInventoryResponse,
)
def get_seller_inventory(
    seller_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
):
    """Return catalog-backed inventory for the selected seller."""

    if credentials.credentials not in VALID_TOKENS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Invalid seller token",
        )

    if random.random() < ERROR_RATE:
        error_status = random.choice([429, 503])
        message = (
            "Rate limit exceeded. Try again later."
            if error_status == 429
            else "Service temporarily unavailable (simulated fault)."
        )
        raise HTTPException(status_code=error_status, detail=message)

    catalog = build_master_catalog(seed=MASTER_SEED)

    seller_stores = [
        store
        for store in catalog.stores
        if store.seller_id == seller_id
    ]

    if not seller_stores:
        raise HTTPException(
            status_code=404,
            detail="Seller has no stores in the shared catalog.",
        )

    stores_by_country = {
        country: [
            store for store in seller_stores
            if store.country == country
        ]
        for country in {store.country for store in seller_stores}
    }

    inventory = []

    for product in catalog.active_products:
        for store in stores_by_country.get(product.country, []):
            quantity = stock_level(
                MASTER_SEED,
                product.sku,
                store.store_id,
            )

            # Preserve the existing negative-inventory simulation setting.
            if ENABLE_NEGATIVE_INVENTORY and random.random() < 0.10:
                quantity = -random.randint(1, 10)

            inventory.append(
                InventoryItem(
                    sku=product.sku,
                    store_id=store.store_id,
                    seller_id=store.seller_id,
                    product_seller_id=product.seller_id,
                    quantity=quantity,
                )
            )

    total_items = len(inventory)
    total_pages = ceil(total_items / limit) if total_items else 0
    start = (page - 1) * limit

    return PaginatedInventoryResponse(
        seller_id=seller_id,
        page=page,
        limit=limit,
        total_items=total_items,
        total_pages=total_pages,
        data=inventory[start:start + limit],
    )
