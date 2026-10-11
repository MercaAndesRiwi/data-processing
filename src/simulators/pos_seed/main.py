import random
from datetime import datetime, timedelta
from sqlalchemy import text
from src.simulators.pos_seed.config import (
    COUNTRIES,
    SEED,
    PRICE_DEFECT_RATE,
    SKU_DEFECT_RATE,
    get_sales_per_country,
    CURRENCIES,
    POS_START_DATE,
    POS_END_DATE,
)
from src.simulators.pos_seed.connection import get_engine
from src.simulators.pos_seed.exchange_rates import (
    convert_usd_to_local,
    load_rate_cache,
)

PAYMENT_METHODS = [
    "cash",
    "credit_card",
    "debit_card",
    "digital_wallet",
]

DIGITAL_CHANNELS = (
    "E-commerce Propio",
    "Marketplace Propietario",
)

def load_seasonality_data(connection, start_date, end_date):
    """Load the holidays and promotions for the period."""

    holidays = connection.execute(
        text("""
            SELECT country_code, holiday_date
            FROM public.holidays
            WHERE holiday_date BETWEEN :start_date AND :end_date
        """),
        {
            "start_date": start_date.date(),
            "end_date": end_date.date(),
        },
    ).mappings().all()

    promotions = connection.execute(
        text("""
            SELECT sku, store_or_channel, discount_pct,
                   start_date, end_date
            FROM public.promotions
            WHERE start_date <= :end_date
              AND end_date >= :start_date
        """),
        {
            "start_date": start_date.date(),
            "end_date": end_date.date(),
        },
    ).mappings().all()

    holiday_dates = {
        (row["country_code"], row["holiday_date"])
        for row in holidays
    }

    promotion_dates = {
        country_code: set()
        for country_code in COUNTRIES
    }

    for promotion in promotions:
        store_or_channel = promotion["store_or_channel"] or ""
        country_code = store_or_channel.split("_", 1)[0]

        if country_code not in promotion_dates:
            continue

        current_date = max(
            promotion["start_date"],
            start_date.date(),
        )
        last_date = min(
            promotion["end_date"],
            end_date.date(),
        )

        while current_date <= last_date:
            promotion_dates[country_code].add(current_date)
            current_date += timedelta(days=1)

    print(f"Packed holidays: {len(holiday_dates)}")
    print(f"Promotions viewed: {len(promotions)}")

    for country_code in COUNTRIES:
        print(
            f"{country_code}: "
            f"{len(promotion_dates[country_code])} promotional days"
        )

    return holiday_dates, promotions, promotion_dates

def generate_sale_date( rng, start_date, end_date, country_code, holiday_dates, promotion_dates):
    """Generates dates with weekly, holiday, and promotional seasonality."""

    days = (end_date.date() - start_date.date()).days + 1

    if days <= 0:
        raise ValueError(
            "The date range must contain at least one day."
        )

    while True:
        offset = rng.randrange(days)

        sale_date = start_date + timedelta(
            days=offset,
            hours=rng.randrange(10, 23),
            minutes=rng.randrange(60),
        )

        current_date = sale_date.date()

        is_weekend = sale_date.weekday() >= 5
        is_holiday = (country_code, current_date) in holiday_dates
        is_promotion = (
            current_date in promotion_dates.get(country_code, set())
        )

        # Normal days have a 55% acceptance probability. 
        # Weekends, holidays, and promotional days are accepted.
        probability = 0.55

        if is_weekend or is_holiday or is_promotion:
            probability = 1.0

        if rng.random() < probability:
            return sale_date

def get_catalog(connection, schema_name):
    """Retrieves the country's branches and products."""

    branches = connection.execute(
        text(f"""
            SELECT branch_id
            FROM {schema_name}.branch
            ORDER BY branch_id
        """)
    ).scalars().all()

    products = connection.execute(
        text(f"""
            SELECT product_id, sku, base_price_usd
            FROM {schema_name}.product
            WHERE base_price_usd IS NOT NULL
              AND base_price_usd > 0
            ORDER BY product_id
        """)
    ).all()

    if not branches:
        raise ValueError(
            f"There are no branches in the schema. '{schema_name}'."
        )

    if not products:
        raise ValueError(
            f"There are no products with valid prices in '{schema_name}'."
        )

    return branches, products

def has_completed_run( connection, country_code, start_date, end_date):
    """Check if the batch already exists for the country and period."""

    result = connection.execute(
        text("""
            SELECT EXISTS (
                SELECT 1
                FROM public.pos_seed_runs
                WHERE country_code = :country_code
                  AND start_date = :start_date
                  AND end_date = :end_date
                  AND seed = :seed
            )
        """),
        {
            "country_code": country_code,
            "start_date": start_date.date(),
            "end_date": end_date.date(),
            "seed": SEED,
        },
    )

    return result.scalar_one()

def get_active_digital_promotion( promotions, country_code, sku, sale_date, sale_channel):
    """Look for the digital promotion with the highest applicable discount."""

    if sale_channel not in DIGITAL_CHANNELS:
        return None

    expected_channel = f"{country_code}_{sale_channel}"

    active_promotions = [
        promotion
        for promotion in promotions
        if promotion["sku"] == sku
        and promotion["start_date"] <= sale_date
        and promotion["end_date"] >= sale_date
        and promotion["store_or_channel"] == expected_channel
    ]

    if not active_promotions:
        return None

    return max(
        active_promotions,
        key=lambda promotion: float(promotion["discount_pct"]),
    )

def generate_country_sales( connection, country_code, schema_name, quantity, rate_cache, promotions, holiday_dates, promotion_dates):
    """Generates repeatable sales linked to a batch."""

    rng = random.Random(f"{SEED}-{country_code}")

    branches, products = get_catalog(connection, schema_name)
    currency = CURRENCIES[country_code]

    start_date = datetime.fromisoformat(POS_START_DATE)
    end_date = datetime.fromisoformat(POS_END_DATE)

    if start_date > end_date:
        raise ValueError(
            "POS_START_DATE must be earlier than POS_END_DATE."
        )

    if has_completed_run(
        connection,
        country_code,
        start_date,
        end_date,
    ):
        print(
            f"{country_code}: The period already exists. "
            "It is omitted to avoid duplicates."
        )
        return

    run_id = connection.execute(
        text("""
            INSERT INTO public.pos_seed_runs (
                country_code,
                start_date,
                end_date,
                seed,
                sales_count
            )
            VALUES (
                :country_code,
                :start_date,
                :end_date,
                :seed,
                :sales_count
            )
            ON CONFLICT (
                country_code,
                start_date,
                end_date,
                seed
            )
            DO NOTHING
            RETURNING run_id
        """),
        {
            "country_code": country_code,
            "start_date": start_date.date(),
            "end_date": end_date.date(),
            "seed": SEED,
            "sales_count": quantity,
        },
    ).scalar_one_or_none()

    if run_id is None:
        print(
            f"{country_code}: The batch is already registered. It is skipped."
        )
        return

    next_sale_id = connection.execute(
        text(f"""
            SELECT COALESCE(MAX(sale_id), 0) + 1
            FROM {schema_name}.sale
        """)
    ).scalar_one()

    next_item_id = connection.execute(
        text(f"""
            SELECT COALESCE(MAX(sale_item_id), 0) + 1
            FROM {schema_name}.sale_item
        """)
    ).scalar_one()

    sale_rows = []
    item_rows = []

    for number in range(quantity):
        sale_id = next_sale_id + number

        sale_date = generate_sale_date(
            rng,
            start_date,
            end_date,
            country_code,
            holiday_dates,
            promotion_dates,
        )

        branch_id = rng.choice(branches)
        payment_method = rng.choice(PAYMENT_METHODS)

        sale_rows.append({
            "sale_id": sale_id,
            "sale_at": sale_date,
            "branch_id": branch_id,
            "payment_method": payment_method,
            "currency_code": currency,
            "run_id": run_id,
        })

        product_id, sku, base_price_usd = rng.choice(products)
        quantity_sold = rng.randint(1, 5)

        sale_channel = rng.choice([
            "TIENDA",
            "E-commerce Propio",
            "Marketplace Propietario",
        ])

        promotion = get_active_digital_promotion(
            promotions,
            country_code,
            sku,
            sale_date.date(),
            sale_channel,
        )

        unit_price = float(
            convert_usd_to_local(
                base_price_usd,
                currency,
                sale_date.date(),
                rate_cache,
            )
        )

        # Apply the discount to the price converted to local currency.
        if promotion is not None:
            discount_pct = float(promotion["discount_pct"])

            unit_price = round(
                unit_price * (1 - discount_pct / 100),
                2,
            )

        # Artificial defects for data quality testing.
        if rng.random() < PRICE_DEFECT_RATE:
            unit_price = rng.choice([
                0,
                -round(rng.uniform(100, 50000), 2),
            ])

        if rng.random() < SKU_DEFECT_RATE:
            sku = sku.lower().replace("-", "_")

        item_rows.append({
            "sale_item_id": next_item_id + number,
            "sale_id": sale_id,
            "product_id": product_id,
            "sku": sku,
            "quantity": quantity_sold,
            "unit_price": unit_price,
        })

    connection.execute(
        text(f"""
            INSERT INTO {schema_name}.sale (
                sale_id,
                sale_at,
                branch_id,
                payment_method,
                currency_code,
                run_id
            )
            VALUES (
                :sale_id,
                :sale_at,
                :branch_id,
                :payment_method,
                :currency_code,
                :run_id
            )
        """),
        sale_rows,
    )

    connection.execute(
        text(f"""
            INSERT INTO {schema_name}.sale_item (
                sale_item_id,
                sale_id,
                product_id,
                sku,
                quantity,
                unit_price
            )
            VALUES (
                :sale_item_id,
                :sale_id,
                :product_id,
                :sku,
                :quantity,
                :unit_price
            )
        """),
        item_rows,
    )

    print(
        f"{country_code}: {quantity} sales generated "
        f"(run_id={run_id})."
    )

def main():
    quantity = get_sales_per_country()
    engine = get_engine()

    start_date = datetime.fromisoformat(POS_START_DATE)
    end_date = datetime.fromisoformat(POS_END_DATE)

    if start_date > end_date:
        raise ValueError(
            "POS_START_DATE must be earlier than POS_END_DATE."
        )

    try:
        with engine.begin() as connection:
            rate_cache = load_rate_cache(connection, CURRENCIES)

            holiday_dates, promotions, promotion_dates = (
                load_seasonality_data(
                    connection,
                    start_date,
                    end_date,
                )
            )

            for country_code, schema_name in COUNTRIES.items():
                connection.execute(
                    text(f"""
                        ALTER TABLE {schema_name}.sale
                        ADD COLUMN IF NOT EXISTS
                        currency_code VARCHAR(3) NOT NULL DEFAULT 'USD'
                    """)
                )

                print(f"Generating sales for {country_code}...")

                generate_country_sales(
                    connection,
                    country_code,
                    schema_name,
                    quantity,
                    rate_cache,
                    promotions,
                    holiday_dates,
                    promotion_dates,
                )
    finally:
        engine.dispose()

    print("POS sales generation completed.")

if __name__ == "__main__":
    main()

