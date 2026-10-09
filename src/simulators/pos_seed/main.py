import random
from datetime import datetime, timedelta
from sqlalchemy import text
from src.simulators.pos_seed.config import (
    COUNTRIES,
    SEED,
    get_sales_per_country,
)
from src.simulators.pos_seed.connection import get_engine


PAYMENT_METHODS = [
    "cash",
    "credit_card",
    "debit_card",
    "digital_wallet",
]


def generate_sale_date(rng, start_date, days=365):
    """Generate a date with more sales on weekends."""
    while True:
        offset = rng.randrange(days)
        sale_date = start_date + timedelta(
            days=offset,
            hours=rng.randrange(10, 23),
            minutes=rng.randrange(60),
        )

        # Increase the probability of weekend sales.
        if sale_date.weekday() >= 5 or rng.random() < 0.55:
            return sale_date


def get_catalog(connection, schema_name):
    """Load existing branches and products."""
    branches = connection.execute(
        text(f"SELECT branch_id FROM {schema_name}.branch ORDER BY branch_id")
    ).scalars().all()

    products = connection.execute(
        text(f"""
            SELECT product_id, sku
            FROM {schema_name}.product
            ORDER BY product_id
        """)
    ).all()

    if not branches:
        raise ValueError(f"No branches found in schema {schema_name}")

    if not products:
        raise ValueError(f"No products found in schema {schema_name}")

    return branches, products


def generate_country_sales(connection, country_code, schema_name, quantity):
    """Generate reproducible sales for one country."""
    rng = random.Random(f"{SEED}-{country_code}")
    branches, products = get_catalog(connection, schema_name)

    # The initial implementation replaces only the generated sales
    # for this country. sale_item rows are removed first because they
    # reference sale rows.
    connection.execute(text(f"DELETE FROM {schema_name}.sale_item"))
    connection.execute(text(f"DELETE FROM {schema_name}.sale"))

    start_date = datetime(2025, 1, 1)
    sale_rows = []
    item_rows = []

    for number in range(1, quantity + 1):
        sale_id = number
        sale_date = generate_sale_date(rng, start_date)
        branch_id = rng.choice(branches)
        payment_method = rng.choice(PAYMENT_METHODS)

        sale_rows.append({
            "sale_id": sale_id,
            "sale_at": sale_date,
            "branch_id": branch_id,
            "payment_method": payment_method,
        })

        product_id, sku = rng.choice(products)

        # Defect rates are added in the next implementation step.
        item_rows.append({
            "sale_item_id": number,
            "sale_id": sale_id,
            "product_id": product_id,
            "sku": sku,
            "quantity": rng.randint(1, 5),
            "unit_price": round(rng.uniform(5000, 150000), 2),
        })

    connection.execute(
        text(f"""
            INSERT INTO {schema_name}.sale
                (sale_id, sale_at, branch_id, payment_method)
            VALUES
                (:sale_id, :sale_at, :branch_id, :payment_method)
        """),
        sale_rows,
    )

    connection.execute(
        text(f"""
            INSERT INTO {schema_name}.sale_item
                (sale_item_id, sale_id, product_id, sku, quantity, unit_price)
            VALUES
                (:sale_item_id, :sale_id, :product_id, :sku, :quantity, :unit_price)
        """),
        item_rows,
    )

    print(f"{country_code}: {quantity} sales generated.")


def main():
    quantity = get_sales_per_country()
    engine = get_engine()

    try:
        with engine.begin() as connection:
            for country_code, schema_name in COUNTRIES.items():
                print(f"Generating sales for {country_code}...")
                generate_country_sales(
                    connection,
                    country_code,
                    schema_name,
                    quantity,
                )
    finally:
        engine.dispose()

    print("POS sales generation completed.")


if __name__ == "__main__":
    main()
