from sqlalchemy import text

from src.simulators.pos_seed.config import COUNTRIES
from src.simulators.pos_seed.connection import get_engine


def test_generated_sales_quality():
    engine = get_engine()

    try:
        with engine.connect() as connection:
            for country_code, schema_name in COUNTRIES.items():
                result = connection.execute(
                    text(f"""
                        SELECT
                            COUNT(*) AS total_details,
                            COUNT(*) FILTER (
                                WHERE si.unit_price <= 0
                            ) AS invalid_prices,
                            COUNT(*) FILTER (
                                WHERE si.sku <> p.sku
                            ) AS inconsistent_skus
                        FROM {schema_name}.sale_item si
                        JOIN {schema_name}.product p
                            ON p.product_id = si.product_id
                    """)
                ).one()

                print(
                    f"{country_code}: "
                    f"{result.total_details} datails, "
                    f"{result.invalid_prices} invalid prices, "
                    f"{result.inconsistent_skus} inconsistent SKU "
                )

                assert result.total_details == 100
    finally:
        engine.dispose()