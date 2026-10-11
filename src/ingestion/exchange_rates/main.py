import json
from datetime import date
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from sqlalchemy import text
from src.simulators.pos_seed.connection import get_engine
from src.simulators.pos_seed.config import CURRENCIES



API_URL = "https://api.frankfurter.dev/v2/rates"
START_DATE = date(2025, 1, 1)
END_DATE = date(2026, 12, 31)


def create_exchange_rate_table(connection):
    connection.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS public.exchange_rate (
                rate_date DATE NOT NULL,
                base_currency_code VARCHAR(3) NOT NULL,
                quote_currency_code VARCHAR(3) NOT NULL,
                rate NUMERIC(18, 8) NOT NULL CHECK (rate > 0),
                source VARCHAR(50) NOT NULL DEFAULT 'Frankfurter',
                PRIMARY KEY (
                    rate_date,
                    base_currency_code,
                    quote_currency_code
                )
            )
            """
        )
    )


def fetch_rates(currency):
    params = urlencode(
        {
            "base": "USD",
            "quotes": currency,
            "from": START_DATE.isoformat(),
            "to": END_DATE.isoformat(),
        }
    )

    url = f"{API_URL}?{params}"

    
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
            f"Frankfurter returned HTTP {error.code} "
            f"for USD/{currency}: {details}"
        ) from error

    except (URLError, TimeoutError) as error:
        raise RuntimeError(
            f"Could not retrieve USD/{currency} rates: {error}"
        ) from error


    if not isinstance(data, list):
        raise ValueError(
            f"Unexpected response for USD/{currency}."
        )

    rates = []

    for item in data:
        if item.get("base") != "USD":
            continue

        if item.get("quote") != currency:
            continue

        rate = float(item["rate"])

        if rate <= 0:
            continue

        rates.append(
            {
                "rate_date": date.fromisoformat(item["date"]),
                "base_currency_code": "USD",
                "quote_currency_code": currency,
                "rate": rate,
                "source": "Frankfurter",
            }
        )

    if not rates:
        raise ValueError(
            f"No historical rates returned for USD/{currency}. "
            "Do not invent a replacement rate."
        )

    return rates


def load_exchange_rates():
    engine = get_engine()

    # USD is the reference currency for the consolidated report.
    target_currencies = sorted(
        set(CURRENCIES.values()) - {"USD"}
    )

    try:
        with engine.begin() as connection:
            create_exchange_rate_table(connection)

            total_loaded = 0

            for currency in target_currencies:
                rates = fetch_rates(currency)

                connection.execute(
                    text(
                        """
                        INSERT INTO public.exchange_rate (
                            rate_date,
                            base_currency_code,
                            quote_currency_code,
                            rate,
                            source
                        )
                        VALUES (
                            :rate_date,
                            :base_currency_code,
                            :quote_currency_code,
                            :rate,
                            :source
                        )
                        ON CONFLICT (
                            rate_date,
                            base_currency_code,
                            quote_currency_code
                        )
                        DO UPDATE SET
                            rate = EXCLUDED.rate,
                            source = EXCLUDED.source
                        """
                    ),
                    rates,
                )

                total_loaded += len(rates)

                print(
                    f"{currency}: {len(rates)} rates loaded."
                )

            print(
                f"Exchange-rate loading completed: "
                f"{total_loaded} records processed."
            )

    finally:
        engine.dispose()


if __name__ == "__main__":
    load_exchange_rates()
