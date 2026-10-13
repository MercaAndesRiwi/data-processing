"""Consumer for the F3 inventory API.

Fetches inventory without modifying the original API or writing to the database.
Validates identifiers against the shared master catalog.
"""

import os
import time
from typing import Any
import httpx
from dotenv import load_dotenv
from src.common.config import MASTER_SEED, PROJECT_ROOT
from src.common.master_catalog import build_master_catalog

load_dotenv(PROJECT_ROOT / ".env")

API_URL = os.getenv(
    "INVENTORY_API_URL",
    "http://127.0.0.1:8000",
).rstrip("/")

API_TOKEN = os.getenv(
    "INVENTORY_API_TOKEN",
    "token-seller-123",
)


class InventoryAPIError(RuntimeError):
    """Raised when the inventory API request fails."""


def fetch_inventory(
    seller_id: str,
    page_size: int = 100,
    max_retries: int = 5,
) -> list[dict[str, Any]]:
    """Fetch all inventory pages for a seller."""

    if not 1 <= page_size <= 100:
        raise ValueError("page_size must be between 1 and 100.")

    items: list[dict[str, Any]] = []
    page = 1

    with httpx.Client(timeout=10.0) as client:
        while True:
            url = f"{API_URL}/api/v1/sellers/{seller_id}/inventory"

            for attempt in range(max_retries + 1):
                response = client.get(
                    url,
                    params={"page": page, "limit": page_size},
                    headers={
                        "Authorization": f"Bearer {API_TOKEN}",
                    },
                )

                if response.status_code in (429, 503):
                    if attempt < max_retries:
                        time.sleep(min(0.25 * (2**attempt), 3.0))
                        continue

                if response.status_code != 200:
                    raise InventoryAPIError(
                        f"F3 returned HTTP {response.status_code}; "
                        f"seller={seller_id}, page={page}."
                    )

                payload = response.json()
                break
            else:
                raise InventoryAPIError(
                    "Maximum API retries exceeded."
                )

            items.extend(payload.get("data", []))

            total_pages = int(payload.get("total_pages", 1))
            if page >= total_pages:
                break

            page += 1

    return items


def validate_inventory(
    seller_id: str,
    items: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compare inventory records with the shared master catalog."""

    catalog = build_master_catalog(seed=MASTER_SEED)

    unknown_skus = sorted({
        item.get("sku", "")
        for item in items
        if item.get("sku") not in catalog.products_by_sku
    })

    negative_stock = [
        {
            "sku": item.get("sku"),
            "quantity": item.get("quantity"),
        }
        for item in items
        if isinstance(item.get("quantity"), int)
        and item["quantity"] < 0
    ]

    missing_store_id = sum(
        "store_id" not in item for item in items
    )

    seller_exists = seller_id in catalog.sellers_by_id

    return {
        "seller_id": seller_id,
        "seller_exists_in_catalog": seller_exists,
        "items_received": len(items),
        "unknown_skus_count": len(unknown_skus),
        "unknown_skus_sample": unknown_skus[:10],
        "negative_stock_count": len(negative_stock),
        "negative_stock_sample": negative_stock[:10],
        "items_without_store_id": missing_store_id,
        "integration_ready": (
            seller_exists
            and not unknown_skus
            and missing_store_id == 0
        ),
    }


def main() -> None:
    """Run the inventory integration check."""

    seller_id = os.getenv(
        "INVENTORY_SELLER_ID",
        "SELLER_001",
    )

    print("Fetching inventory from F3...")
    items = fetch_inventory(seller_id)
    report = validate_inventory(seller_id, items)

    print("\nF3 INTEGRATION REPORT")
    for key, value in report.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
