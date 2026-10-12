"""Fault criteria: configurable duplicates + disorder capped at 6h."""

import random
from datetime import datetime, timezone

from src.simulators.marketplace_events.faults import (
    apply_duplicates,
    apply_out_of_order,
)
from src.simulators.marketplace_events.producer import (
    Event,
    ProducerConfig,
    generate_events,
)


def _event(event_id: str, ts: datetime) -> Event:
    return Event(
        event_id=event_id,
        order_id="ORD-1",
        event_type="created",
        sku="SKU-X",
        store_id="STO",
        seller_id="SEL",
        country="CO",
        quantity=1,
        unit_price=10.0,
        event_ts=ts,
        arrival_ts=ts,
    )


def test_duplicates_disabled_by_default():
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    events = [_event(f"E{i}", base) for i in range(5)]
    out = apply_duplicates(events, random.Random(1), 0.0)
    assert [e.event_id for e in out] == [f"E{i}" for i in range(5)]


def test_duplicates_repeat_same_id_when_enabled():
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    events = [_event(f"E{i}", base) for i in range(20)]
    out = apply_duplicates(events, random.Random(2), 1.0)
    assert len(out) > len(events)
    # Same IDs repeated, no invented IDs.
    assert {e.event_id for e in out} == {f"E{i}" for i in range(20)}


def test_out_of_order_capped_at_six_hours():
    events = generate_events(
        ProducerConfig(seed=11, n_orders=30, ooo_enabled=False)
    )
    shifted = apply_out_of_order(events, random.Random(3), 21600)
    lags = [(e.arrival_ts - e.event_ts).total_seconds() for e in shifted]
    assert all(0 <= lag <= 21600 for lag in lags)
    assert [e.arrival_ts for e in shifted] == sorted(
        e.arrival_ts for e in shifted
    )


def test_generated_histories_are_valid_lifecycle():
    from src.simulators.marketplace_events.lifecycle import TERMINAL_STATES

    events = generate_events(
        ProducerConfig(
            seed=21, n_orders=50, duplicate_rate=0.05, ooo_enabled=True
        )
    )
    by_order: dict[str, list[str]] = {}
    for event in events:
        by_order.setdefault(event.order_id, [])
        if event.event_type not in by_order[event.order_id]:
            # First arrival of each type preserves lifecycle order check
            # loosely; strict per-order validation below uses event_ts.
            by_order[event.order_id].append(event.event_type)

    ordered = sorted(events, key=lambda e: (e.order_id, e.event_ts))
    seen: dict[str, str] = {}
    for event in ordered:
        if event.order_id not in seen:
            assert event.event_type == "created"
            seen[event.order_id] = "created"
            continue
        # Duplicates carry the same type: allowed without transition.
        if event.event_type == seen[event.order_id]:
            continue
        from src.simulators.marketplace_events.lifecycle import transition

        seen[event.order_id] = transition(
            seen[event.order_id], event.event_type
        )
    assert all(s in TERMINAL_STATES for s in seen.values())
