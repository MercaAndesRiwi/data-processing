"""Shared configuration for catalog seeds and simulators.

This module is additive: it does not replace
``src.simulators.pos_seed.config``. Existing POS code keeps working
while new simulators (F3/F4) share a single master seed and ID space.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")

COUNTRIES: dict[str, str] = {
    "CO": "colombia",
    "PE": "peru",
    "EC": "ecuador",
    "BO": "bolivia",
    "CL": "chile",
}

CURRENCIES: dict[str, str] = {
    "CO": "COP",
    "PE": "PEN",
    "EC": "USD",
    "BO": "BOB",
    "CL": "CLP",
}

# Single master seed. Falls back to POS_SEED so existing .env files
# keep producing the same POS data.
MASTER_SEED: int = int(
    os.getenv("MASTER_SEED", os.getenv("POS_SEED", "42"))
)

# Default catalog size. Matches the reference workbook scale
# (71 categories x 15 products = 1065) without hardcoding the total.
CATALOG_PER_CATEGORY: int = int(os.getenv("CATALOG_PER_CATEGORY", "15"))
CATALOG_ACTIVE_RATE: float = float(os.getenv("CATALOG_ACTIVE_RATE", "0.95"))
