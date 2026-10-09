
from src.simulators.pos_seed.config import (
    COUNTRIES,
    SEED,
    get_sales_per_country,
)


def main():
    print("POS Generator Configuration")
    print(f"Seed: {SEED}")
    print(f"Sales by country: {get_sales_per_country()}")
    print("Configured countries:")

    for country_code, schema_name in COUNTRIES.items():
        print(f"- {country_code}: {schema_name}")


if __name__ == "__main__":
    main()
