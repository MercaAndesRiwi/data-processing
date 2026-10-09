import os
from pathlib import Path

COUNTRIES = {
    "CO": "colombia",
    "PE": "peru",
    "EC": "ecuador",
    "BO": "bolivia",
    "CL": "chile",
}

SEED = int(os.getenv("POS_SEED", "42"))

# POS data generation configuration
POS_MODE = os.getenv("POS_MODE", "dev").lower()

DEV_SALES_PER_COUNTRY = int(
    os.getenv("POS_DEV_SALES_PER_COUNTRY", "100")
)

FULL_SALES_PER_COUNTRY = int(
    os.getenv("POS_FULL_SALES_PER_COUNTRY", "400000")
)

PRICE_DEFECT_RATE = float(
    os.getenv("POS_PRICE_DEFECT_RATE", "0.005")
)

SKU_DEFECT_RATE = float(
    os.getenv("POS_SKU_DEFECT_RATE", "0.01")
)

if POS_MODE not in {"dev", "full"}:
    raise ValueError("POS_MODE must be 'dev' or 'full'.")

if not 0 <= PRICE_DEFECT_RATE <= 1:
    raise ValueError(
        "POS_PRICE_DEFECT_RATE must be between 0 and 1."
    )

if not 0 <= SKU_DEFECT_RATE <= 1:
    raise ValueError(
        "POS_SKU_DEFECT_RATE must be between 0 and 1."
    )


def get_sales_per_country() -> int:
    """Return the sales volume based on the selected mode."""
    if POS_MODE == "full":
        return FULL_SALES_PER_COUNTRY

    return DEV_SALES_PER_COUNTRY



PROJECT_ROOT = Path(__file__).resolve().parents[3]

PROMOTIONS_DIR = PROJECT_ROOT / "data" / "promotions"
PROMOTIONS_TABLE = "promotions"
