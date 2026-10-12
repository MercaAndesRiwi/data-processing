from sqlalchemy import text

from src.common.master_catalog import build_master_catalog
from src.simulators.pos_seed.config import COUNTRIES, SEED
from src.simulators.pos_seed.connection import get_engine


def load_catalog():
    """Build active products and base USD prices from the seeded catalog.

    Replaces the Excel workbook source (gitignored, absent in CI) with
    the deterministic master catalog so POS shares SKUs with F3/F4.
    Return shape is unchanged: ``{country_code: [product dicts]}``.
    """
    catalog = build_master_catalog(seed=SEED)

    products_by_country = {code: [] for code in COUNTRIES}

    for product in catalog.products:
        if product.status.lower() not in {"activo", "active"}:
            continue
        if product.country not in products_by_country:
            continue
        products_by_country[product.country].append(
            {
                "sku": product.sku,
                "name": product.name,
                "category": product.category,
                "base_price_usd": product.base_price_usd,
            }
        )

    return products_by_country


def create_catalogs():
    products_by_country = load_catalog()
    engine = get_engine()

    try:
        with engine.begin() as connection:
            for country_code, schema_name in COUNTRIES.items():

                # Update existing databases as well as newly created ones.
                connection.execute(
                    text(
                        f"""
                        ALTER TABLE {schema_name}.product
                        ADD COLUMN IF NOT EXISTS
                        base_price_usd NUMERIC(12, 2)
                        """
                    )
                )

                products = products_by_country[country_code]
                print(
                    f"{country_code}: loading {len(products)} active products."
                )

                categories = sorted(
                    {product["category"] for product in products}
                )

                existing_categories = dict(
                    connection.execute(
                        text(
                            f"""
                            SELECT name, product_category_id
                            FROM {schema_name}.product_category
                            """
                        )
                    ).fetchall()
                )

                next_category_id = (
                    max(existing_categories.values(), default=0) + 1
                )

                for category_name in categories:
                    if category_name in existing_categories:
                        continue

                    connection.execute(
                        text(
                            f"""
                            INSERT INTO {schema_name}.product_category
                                (product_category_id, name)
                            VALUES (:category_id, :name)
                            """
                        ),
                        {
                            "category_id": next_category_id,
                            "name": category_name,
                        },
                    )

                    existing_categories[category_name] = next_category_id
                    next_category_id += 1

                for product in products:
                    connection.execute(
                        text(
                            f"""
                            INSERT INTO {schema_name}.product
                                (
                                    product_id,
                                    product_category_id,
                                    sku,
                                    name,
                                    base_price_usd
                                )
                            VALUES
                                (
                                    :product_id,
                                    :category_id,
                                    :sku,
                                    :name,
                                    :base_price_usd
                                )
                            ON CONFLICT (sku) DO UPDATE SET
                                product_category_id = EXCLUDED.product_category_id,
                                name = EXCLUDED.name,
                                base_price_usd = EXCLUDED.base_price_usd
                            """
                        ),
                        {
                            "product_id": product["sku"],
                            "category_id": existing_categories[
                                product["category"]
                            ],
                            "sku": product["sku"],
                            "name": product["name"],
                            "base_price_usd": product["base_price_usd"],
                        },
                    )

                print(
                    f"{country_code}: catalog loaded successfully."
                )

        print("Master catalog loading completed.")

    finally:
        engine.dispose()


if __name__ == "__main__":
    create_catalogs()
