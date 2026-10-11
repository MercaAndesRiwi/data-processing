from datetime import date
from decimal import Decimal

from sqlalchemy import text


def load_rate_cache(connection, currencies):
    """
    Load persisted exchange rates into memory.
    Each currency uses the latest available rate on or before each date.
    """
    cache = {"USD": {}}

    for currency in set(currencies.values()):
        if currency == "USD":
            continue

        rows = connection.execute(
            text(
                """
                SELECT rate_date, rate
                FROM public.exchange_rate
                WHERE base_currency_code = 'USD'
                  AND quote_currency_code = :currency
                ORDER BY rate_date
                """
            ),
            {"currency": currency},
        ).all()

        if not rows:
            raise ValueError(
                f"No exchange rates stored for USD/{currency}. "
                "Load valid rates before generating POS sales."
            )

        cache[currency] = {
            rate_date: Decimal(str(rate))
            for rate_date, rate in rows
        }

    return cache


def get_usd_rate(rate_cache, currency, sale_date):
    """Find the most recent stored rate on or before the sale date."""
    if currency == "USD":
        return Decimal("1")

    available_dates = [
        rate_date
        for rate_date in rate_cache[currency]
        if rate_date <= sale_date
    ]

    if not available_dates:
        raise ValueError(
            f"No USD/{currency} rate available on or before "
            f"{sale_date}. No replacement rate will be invented."
        )

    latest_date = max(available_dates)
    return rate_cache[currency][latest_date]


def convert_usd_to_local(
    base_price_usd,
    currency,
    sale_date,
    rate_cache,
):
    rate = get_usd_rate(rate_cache, currency, sale_date)

    return (
        Decimal(str(base_price_usd)) * rate
    ).quantize(Decimal("0.01"))


def convert_local_to_usd(
    local_amount,
    currency,
    sale_date,
    rate_cache,
):
    rate = get_usd_rate(rate_cache, currency, sale_date)

    return (
        Decimal(str(local_amount)) / rate
    ).quantize(Decimal("0.01"))
