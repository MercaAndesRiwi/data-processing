"""Lifecycle criterion: valid path + post-dispatch cancel = return."""

import pytest

from src.simulators.marketplace_events.lifecycle import (
    InvalidTransitionError,
    Order,
    transition,
)


def test_happy_path_created_paid_shipped_delivered():
    order = Order("O1", "SKU", "STO", "SEL", "CO")
    assert order.apply("paid") == "paid"
    assert order.apply("shipped") == "shipped"
    assert order.apply("delivered") == "delivered"
    assert order.is_terminal


def test_cancel_before_dispatch_stays_cancelled():
    assert transition("created", "cancelled") == "cancelled"
    assert transition("paid", "cancelled") == "cancelled"


def test_cancel_after_dispatch_becomes_return():
    # The core post-dispatch rule.
    assert transition("shipped", "cancelled") == "returned"
    assert transition("shipped", "returned") == "returned"
    assert transition("delivered", "returned") == "returned"


def test_invalid_transitions_raise():
    with pytest.raises(InvalidTransitionError):
        transition("created", "shipped")
    with pytest.raises(InvalidTransitionError):
        transition("created", "delivered")
    with pytest.raises(InvalidTransitionError):
        transition("delivered", "paid")
    with pytest.raises(InvalidTransitionError):
        transition("cancelled", "paid")
