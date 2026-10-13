import os
import random
from typing import List
from fastapi import FastAPI, HTTPException, Query, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

app = FastAPI(
    title="Seller Inventory Simulator API (F3)",
    version="1.0.0",
    description="Mock REST API for seller inventory simulation featuring pagination, rate limits, and intermittent error injection."
)

# Security scheme for Swagger UI
security_scheme = HTTPBearer()

# Configuration from environment variables
ERROR_RATE = float(os.getenv("ERROR_RATE", "0.03"))  # Default 3% error rate
ENABLE_NEGATIVE_INVENTORY = os.getenv("ENABLE_NEGATIVE_INVENTORY", "true").lower() == "true"

# Data Models
class InventoryItem(BaseModel):
    sku: str
    quantity: int
    updated_at: str

class PaginatedInventoryResponse(BaseModel):
    seller_id: str
    page: int
    limit: int
    total_items: int
    total_pages: int
    data: List[InventoryItem]

# Mock data sources
MOCK_SKUS = [f"SKU-{i:05d}" for i in range(1, 101)]
VALID_TOKENS = ["token-seller-123", "bearer-token-mercaandes-2026", "test-token"]

@app.get(
    "/api/v1/sellers/{seller_id}/inventory",
    response_model=PaginatedInventoryResponse,
    summary="Get Seller Inventory",
    description="Retrieves paginated inventory for a given seller with intermittent fault injection."
)
def get_seller_inventory(
    seller_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
):
    # 1. Intermittent fault injection (>= 3% rate limit or service unavailable)
    if random.random() < ERROR_RATE:
        error_status = random.choice([
            status.HTTP_429_TOO_MANY_REQUESTS,
            status.HTTP_503_SERVICE_UNAVAILABLE
        ])
        error_msg = (
            "Rate limit exceeded. Try again later." 
            if error_status == 429 
            else "Service temporarily unavailable (Simulated fault)."
        )
        raise HTTPException(status_code=error_status, detail=error_msg)

    # 2. Authorization Token Validation
    token = credentials.credentials
    if token not in VALID_TOKENS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Invalid seller token"
        )

    # 3. Deterministic Inventory Generation per Seller
    seller_seed = sum(ord(c) for c in seller_id)
    rng = random.Random(seller_seed)
    
    num_products = rng.randint(15, 30)
    seller_skus = rng.sample(MOCK_SKUS, num_products)
    
    inventory_data = []
    for sku in seller_skus:
        # Negative inventory injection if enabled
        if ENABLE_NEGATIVE_INVENTORY and random.random() < 0.10:
            qty = random.randint(-10, -1)
        else:
            qty = random.randint(0, 100)
            
        inventory_data.append(
            InventoryItem(
                sku=sku,
                quantity=qty,
                updated_at="2026-10-05T12:00:00Z"
            )
        )

    # 4. Pagination Logic
    total_items = len(inventory_data)
    total_pages = (total_items + limit - 1) // limit
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_data = inventory_data[start_idx:end_idx]

    return PaginatedInventoryResponse(
        seller_id=seller_id,
        page=page,
        limit=limit,
        total_items=total_items,
        total_pages=total_pages,
        data=paginated_data
    )