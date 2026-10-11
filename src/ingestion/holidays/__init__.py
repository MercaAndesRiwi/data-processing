import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from sqlalchemy import text

from src.simulators.pos_seed.connection import get_engine


API_URL = "https://date.nager.at/api/v3/PublicHolidays"
COUNTRIES = ["CO", "PE", "EC", "BO", "CL"]
YEARS = [2026]


def create_holidays_table(connection):
    connection.execute(
        text("""
            CREATE TABLE IF NOT EXISTS public.holidays (
                holiday_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                country_code VARCHAR(2) NOT NULL,
                holiday_date DATE NOT NULL,
                holiday_name VARCHAR(150) NOT NULL,
                source VARCHAR(100) NOT NULL DEFAULT 'Nager.Date',
                PRIMARY KEY (holiday_id),
                UNIQUE (country_code, holiday_date, holiday_name)
            )
        """)
    )


def fetch_holidays(country_code, year):
    url = f"{API_URL}/{year}/{country_code}"
    request = Request(
        url,
        headers={"User-Agent": "MercaAndesDataProcessing/1.0"},
    )

    try:
        with urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))

    except HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Nager.Date returned HTTP {error.code} "
            f"for {country_code}/{year}: {details}"
        ) from error

    except (URLError, TimeoutError) as error:
        raise RuntimeError(
            f"Could not retrieve holidays for "
            f"{country_code}/{year}: {error}"
        ) from error

    if not isinstance(data, list):
        raise ValueError(
            f"Unexpected response for {country_code}/{year}."
        )

    holidays = []

    for item in data:
        holiday_date = item.get("date")
        name = item.get("localName") or item.get("name")

        if not holiday_date or not name:
            continue

        holidays.append({
            "country_code": country_code,
            "holiday_date": holiday_date,
            "holiday_name": name,
            "source": "Nager.Date API v3",
        })

    return holidays


def load_holidays():
    engine = get_engine()

    try:
        with engine.begin() as connection:
            create_holidays_table(connection)
            total_loaded = 0

            for country in COUNTRIES:
                for year in YEARS:
                    holidays = fetch_holidays(country, year)

                    if holidays:
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
                                DO UPDATE SET
                                    source = EXCLUDED.source
                            """),
                            holidays,
                        )

                    total_loaded += len(holidays)
                    print(
                        f"{country} {year}: "
                        f"{len(holidays)} holidays processed."
                    )

            print(
                f"Holiday ingestion completed: "
                f"{total_loaded} records processed."
            )

    finally:
        engine.dispose()


if __name__ == "__main__":
    load_holidays()
