import json
from datetime import date
from urllib.request import Request, urlopen
from src.simulators.pos_seed.connection import get_engine
from sqlalchemy import text


API_URL = "https://nagerholidays.com/api/v4/Holidays"

COUNTRY_CODES = {
    "CO": "CO",
    "PE": "PE",
    "EC": "EC",
    "BO": "BO",
    "CL": "CL",
}


def create_holidays_table(connection):
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS public.holidays (
            holiday_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            country_code VARCHAR(2) NOT NULL,
            holiday_date DATE NOT NULL,
            holiday_name VARCHAR(150) NOT NULL,
            source VARCHAR(100) NOT NULL,
            CONSTRAINT uq_holiday_country_date_name
                UNIQUE (country_code, holiday_date, holiday_name)
        )
    """))


def fetch_holidays(country_code, year):
    url = f"{API_URL}/{country_code}/{year}"
    request = Request(
        url,
        headers={"User-Agent": "MercaAndes-POS-Seed/1.0"},
    )

    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def load_holidays(connection, years):
    create_holidays_table(connection)

    total = 0

    for country_code in COUNTRY_CODES:
        for year in years:
            print(f"Checking holidays: {country_code}, {year}...")

            holidays = fetch_holidays(country_code, year)

            for holiday in holidays:
                connection.execute(
                    text("""
                        INSERT INTO public.holidays (
                            country_code,
                            holiday_date,
                            holiday_name,
                            source
                        )
                        VALUES (
                            :country_code,
                            :holiday_date,
                            :holiday_name,
                            :source
                        )
                        ON CONFLICT (
                            country_code,
                            holiday_date,
                            holiday_name
                        )
                        DO UPDATE SET source = EXCLUDED.source
                    """),
                    {
                        "country_code": country_code,
                        "holiday_date": date.fromisoformat(
                            holiday["date"]
                        ),
                        "holiday_name": holiday["name"],
                        "source": "Nager.Date API v4",
                    },
                )

            total += len(holidays)
            print(f"Public holidays observed: {len(holidays)}")

    print(f"Total records received: {total}")

def main():
    engine = get_engine()

    try:
        with engine.begin() as connection:
            load_holidays(connection, [2026])
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()