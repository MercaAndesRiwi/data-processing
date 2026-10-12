"""Seeded marketplace event producer (F4): lifecycle + faults + peak mode.

All producers share IDs from ``master_catalog``. Event IDs are
deterministic ``uuid5`` so duplicate injection re-emits the same ID.
Timestamps are logical (no sleep); peak throughput is pure compute.
"""

from __future__ import annotations

import argparse
import json
import random
import time
import uuid
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.common.config import MASTER_SEED
from src.common.master_catalog import MasterCatalog, build_master_catalog
from src.simulators.marketplace_events import lifecycle
from src.simulators.marketplace_events.faults import (
    apply_duplicates,
    apply_out_of_order,
)

EVENT_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


@dataclass(frozen=True)
class Event:
    event_id: str
    order_id: str
    event_type: str
    sku: str
    store_id: str
    seller_id: str
    country: str
    quantity: int
    unit_price: float
    event_ts: datetime
    arrival_ts: datetime

    def with_arrival(self, arrival_ts: datetime) -> Event:
        return replace(self, arrival_ts=arrival_ts)

    def to_json(self) -> str:
        payload = asdict(self)
        payload["event_ts"] = self.event_ts.isoformat()
        payload["arrival_ts"] = self.arrival_ts.isoformat()
        return json.dumps(payload)


@dataclass
class ProducerConfig:
    seed: int = MASTER_SEED
    n_orders: int = 100
    duplicate_rate: float = 0.0
    ooo_enabled: bool = False
    ooo_max_lag_sec: int = 21600
    start: datetime = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def __post_init__(self) -> None:
        if self.n_orders <= 0:
            raise ValueError("n_orders must be positive.")
        if not 0 <= self.duplicate_rate <= 1:
            raise ValueError("duplicate_rate must be between 0 and 1.")
        if self.ooo_max_lag_sec < 0 or self.ooo_max_lag_sec > 21600:
            raise ValueError("ooo_max_lag_sec must be in [0, 21600].")


def _step_timestamps(
    rng: random.Random, base: datetime
) -> dict[str, datetime]:
    paid_at = base + timedelta(minutes=5, seconds=rng.randint(0, 600))
    shipped_at = paid_at + timedelta(hours=2, minutes=rng.randint(0, 60))
    final_at = shipped_at + timedelta(hours=24, minutes=rng.randint(0, 120))
    return {"paid": paid_at, "shipped": shipped_at, "final": final_at}


def generate_events(
    config: ProducerConfig,
    catalog: MasterCatalog | None = None,
) -> list[Event]:
    """Generate arrival-ordered events for ``n_orders`` seeded orders."""
    catalog = catalog or build_master_catalog(seed=config.seed)
    rng = random.Random(f"{config.seed}-orders")
    price_by_sku = {p.sku: p.base_price_usd for p in catalog.products}

    ordered: list[Event] = []
    for i in range(config.n_orders):
        product = rng.choice(catalog.active_products)
        candidates = [
            s for s in catalog.stores if s.country == product.country
        ]
        store = rng.choice(candidates)
        order_id = f"ORD-{config.seed}-{i:06d}"
        base = config.start + timedelta(seconds=i * 30)
        stamps = _step_timestamps(rng, base)
        quantity = rng.randint(1, 3)
        unit_price = price_by_sku[product.sku]

        order = lifecycle.Order(
            order_id=order_id,
            sku=product.sku,
            store_id=store.store_id,
            seller_id=product.seller_id,
            country=product.country,
        )
        # Paid stage: ~6% cancel straight from created.
        if rng.random() < 0.06:
            states = [(lifecycle.CANCELLED, base + timedelta(minutes=1))]
            order.apply(lifecycle.CANCELLED)
        else:
            order.apply(lifecycle.PAID)
            states = [(lifecycle.PAID, stamps["paid"])]
            # Shipped stage: ~8% cancel from paid.
            if rng.random() < 0.08:
                order.apply(lifecycle.CANCELLED)
                states.append((lifecycle.CANCELLED, stamps["shipped"]))
            else:
                order.apply(lifecycle.SHIPPED)
                states.append((lifecycle.SHIPPED, stamps["shipped"]))
                roll = rng.random()
                if roll < 0.80:
                    order.apply(lifecycle.DELIVERED)
                    states.append((lifecycle.DELIVERED, stamps["final"]))
                elif roll < 0.90:
                    order.apply(lifecycle.RETURNED)
                    states.append((lifecycle.RETURNED, stamps["final"]))
                else:
                    # Post-dispatch cancellation -> returned (rule).
                    order.apply(lifecycle.CANCELLED)
                    states.append((lifecycle.RETURNED, stamps["final"]))

        for seq, (state, ts) in enumerate(
            [(lifecycle.CREATED, base)] + states
        ):
            event_id = str(
                uuid.uuid5(EVENT_NAMESPACE, f"{config.seed}-{order_id}-{seq}")
            )
            ordered.append(
                Event(
                    event_id=event_id,
                    order_id=order_id,
                    event_type=state,
                    sku=product.sku,
                    store_id=store.store_id,
                    seller_id=product.seller_id,
                    country=product.country,
                    quantity=quantity,
                    unit_price=unit_price,
                    event_ts=ts,
                    arrival_ts=ts,
                )
            )

    rng_faults = random.Random(f"{config.seed}-faults")
    faulted = apply_duplicates(
        ordered, rng_faults, config.duplicate_rate
    )
    if config.ooo_enabled:
        faulted = apply_out_of_order(
            faulted, rng_faults, config.ooo_max_lag_sec
        )
    return faulted


def write_jsonl(events: list[Event], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        for event in events:
            fh.write(event.to_json() + "\n")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seeded F4 event producer.")
    parser.add_argument("--seed", type=int, default=MASTER_SEED)
    parser.add_argument("--orders", type=int, default=100)
    parser.add_argument("--duplicate-rate", type=float, default=0.0)
    parser.add_argument("--ooo", action="store_true")
    parser.add_argument("--max-lag", type=int, default=21600)
    parser.add_argument(
        "--start", default="2026-01-01T00:00:00+00:00"
    )
    parser.add_argument("--out", default="data/raw/events.jsonl")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    config = ProducerConfig(
        seed=args.seed,
        n_orders=args.orders,
        duplicate_rate=args.duplicate_rate,
        ooo_enabled=bool(args.ooo),
        ooo_max_lag_sec=args.max_lag,
        start=datetime.fromisoformat(args.start),
    )
    started = time.perf_counter()
    events = generate_events(config)
    elapsed = time.perf_counter() - started
    write_jsonl(events, Path(args.out))
    eps = len(events) / elapsed if elapsed > 0 else float("inf")
    print(f"orders={config.n_orders} events={len(events)} eps={eps:.1f}")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
