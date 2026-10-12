"""Peak criterion: generator reaches at least 20 events/second."""

import time

from src.simulators.marketplace_events.producer import ProducerConfig
from src.simulators.marketplace_events.producer import generate_events


def test_peak_throughput_reaches_20_eps():
    config = ProducerConfig(seed=42, n_orders=300)
    started = time.perf_counter()
    events = generate_events(config)
    elapsed = time.perf_counter() - started
    eps = len(events) / elapsed if elapsed > 0 else float("inf")
    print(f"\npeak: {len(events)} events in {elapsed:.3f}s = {eps:.1f} eps")
    assert eps >= 20
