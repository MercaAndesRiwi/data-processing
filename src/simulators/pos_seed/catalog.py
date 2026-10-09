from sqlalchemy import text

from src.simulators.pos_seed.connection import get_engine
from src.simulators.pos_seed.config import COUNTRIES, SEED


def create_catalogs():
    engine = get_engine()

    with engine.begin() as connection:
        for country_code, schema_name in COUNTRIES.items():
            print(f"Preparing catalog for {country_code}...")

            connection.execute(
                text(f"""
                    INSERT INTO {schema_name}.branch
                        (branch_id, name, city, state)
                    VALUES
                        (1, 'Main Branch', 'Capital City', 'Main State'),
                        (2, 'North Branch', 'North City', 'North State')
                    ON CONFLICT (branch_id) DO NOTHING
                """)
            )

            connection.execute(
                text(f"""
                    INSERT INTO {schema_name}.product_category
                        (product_category_id, name)
                    VALUES
                        (1, 'Food'),
                        (2, 'Home'),
                        (3, 'Personal Care')
                    ON CONFLICT (product_category_id) DO NOTHING
                """)
            )

            connection.execute(
                text(f"""
                    INSERT INTO {schema_name}.product
                        (product_id, product_category_id, sku, name)
                    VALUES
                        ('P001', 1, 'SKU-P001', 'Product One'),
                        ('P002', 2, 'SKU-P002', 'Product Two'),
                        ('P003', 3, 'SKU-P003', 'Product Three')
                    ON CONFLICT (product_id) DO NOTHING
                """)
            )

    engine.dispose()
    print(f"Catalogs created. Seed configured: {SEED}")


if __name__ == "__main__":
    create_catalogs()
