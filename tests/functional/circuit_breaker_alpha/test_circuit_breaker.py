from __future__ import annotations

import warnings

import pytest

from aws_lambda_powertools.utilities.circuit_breaker_alpha import (
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    CircuitState,
    CircuitTransition,
    circuit_breaker,
)
from aws_lambda_powertools.utilities.circuit_breaker_alpha.persistence.record import CircuitStateRecord

# All tests disable the local read cache (max_age=0) so each call re-reads the fake store.


def test_closed_circuit_returns_result_and_writes_nothing(store):
    @circuit_breaker(name="c", persistence_store=store, config=CircuitBreakerConfig(local_cache_max_age=0))
    def call(value):
        return value * 2

    assert call(21) == 42
    assert store.db == {}, "healthy path must not write to the store"


def test_trips_open_after_failure_threshold(store):
    config = CircuitBreakerConfig(failure_threshold=3, local_cache_max_age=0)

    @circuit_breaker(name="c", persistence_store=store, config=config)
    def call():
        raise ConnectionError("downstream down")

    for _ in range(3):
        with pytest.raises(ConnectionError):
            call()

    assert store.db["c"].state == CircuitState.OPEN
    assert store.db["c"].opened_at is not None


def test_open_with_callback_returns_callback_value_without_calling_protected(store, now):
    store.db["c"] = CircuitStateRecord(name="c", state=CircuitState.OPEN, failure_count=5, opened_at=now)
    protected_ran = {"value": False}

    def on_open(order, circuit):
        return {"buffered": order, "state": str(circuit.state)}

    config = CircuitBreakerConfig(recovery_timeout=9999, local_cache_max_age=0)

    @circuit_breaker(name="c", persistence_store=store, on_circuit_open=on_open, config=config)
    def charge(order):
        protected_ran["value"] = True
        return f"charged {order}"

    result = charge({"id": 1})
    assert result == {"buffered": {"id": 1}, "state": "OPEN"}
    assert protected_ran["value"] is False


def test_open_without_callback_raises_with_circuit_info(store, now):
    store.db["c"] = CircuitStateRecord(name="c", state=CircuitState.OPEN, failure_count=7, opened_at=now)
    config = CircuitBreakerConfig(recovery_timeout=9999, local_cache_max_age=0)

    @circuit_breaker(name="c", persistence_store=store, config=config)
    def charge(order):
        return f"charged {order}"

    with pytest.raises(CircuitBreakerOpenError) as exc_info:
        charge({"id": 1})

    assert exc_info.value.circuit.name == "c"
    assert exc_info.value.circuit.failure_count == 7


def test_half_open_probe_success_closes_after_success_threshold(store, now):
    store.db["c"] = CircuitStateRecord(name="c", state=CircuitState.OPEN, failure_count=5, opened_at=now - 100)
    config = CircuitBreakerConfig(recovery_timeout=30, success_threshold=2, local_cache_max_age=0)

    @circuit_breaker(name="c", persistence_store=store, config=config)
    def call():
        return "ok"

    call()  # wins the probe lock, state becomes HALF_OPEN
    assert store.db["c"].state == CircuitState.HALF_OPEN

    call()  # second consecutive probe success closes the circuit
    assert store.db["c"].state == CircuitState.CLOSED


def test_half_open_probe_failure_reopens(store, now):
    store.db["c"] = CircuitStateRecord(name="c", state=CircuitState.OPEN, failure_count=5, opened_at=now - 100)
    config = CircuitBreakerConfig(recovery_timeout=30, success_threshold=2, local_cache_max_age=0)

    @circuit_breaker(name="c", persistence_store=store, config=config)
    def call():
        raise ConnectionError("still down")

    with pytest.raises(ConnectionError):
        call()

    assert store.db["c"].state == CircuitState.OPEN


# --------------------------------------------------------------------------- bug regressions


def test_half_open_can_be_reacquired_after_failed_probe_reopens(store, now):
    # Bug #1: a failed probe (HALF_OPEN -> OPEN) must clear the half_open_owner so a
    # later recovery window can elect a prober again. Otherwise the circuit is stuck
    # OPEN forever because attribute_not_exists(half_open_owner) never holds again.
    store.db["c"] = CircuitStateRecord(name="c", state=CircuitState.OPEN, failure_count=5, opened_at=now - 100)
    config = CircuitBreakerConfig(recovery_timeout=30, success_threshold=2, local_cache_max_age=0)

    outcomes = iter([ConnectionError("still down"), "recovered"])

    @circuit_breaker(name="c", persistence_store=store, config=config)
    def call():
        result = next(outcomes)
        if isinstance(result, Exception):
            raise result
        return result

    # First recovery window: env wins the probe, probe fails, circuit reopens.
    with pytest.raises(ConnectionError):
        call()
    assert store.db["c"].state == CircuitState.OPEN
    assert store.db["c"].half_open_owner is None, "reopen must release the probe lock"

    # Second recovery window (opened_at is fresh, push it into the past again).
    store.db["c"].opened_at = now - 100
    # Downstream recovered: the env must be able to acquire the probe again and run it.
    assert call() == "recovered"
    assert store.db["c"].state == CircuitState.HALF_OPEN


def test_open_callback_receives_keyword_arguments_intact(store, now):
    # Bug #3: the callback must receive the same kwargs the protected function got,
    # as kwargs, not flattened into positional values.
    store.db["c"] = CircuitStateRecord(name="c", state=CircuitState.OPEN, failure_count=5, opened_at=now)
    config = CircuitBreakerConfig(recovery_timeout=9999, local_cache_max_age=0)

    captured = {}

    def on_open(order, customer, circuit):
        captured["order"] = order
        captured["customer"] = customer
        return "buffered"

    @circuit_breaker(name="c", persistence_store=store, on_circuit_open=on_open, config=config)
    def charge(order, customer):
        return "charged"

    # Called entirely with keyword arguments, deliberately out of signature order.
    assert charge(customer="alice", order={"id": 1}) == "buffered"
    assert captured["order"] == {"id": 1}
    assert captured["customer"] == "alice"


def test_consecutive_failures_trip_but_a_success_resets_the_streak(store):
    # The failure counter is per-environment and counts *consecutive* failures as this
    # env sees them: any success in between must reset the streak.
    config = CircuitBreakerConfig(failure_threshold=3, local_cache_max_age=0)

    should_fail = {"value": True}

    @circuit_breaker(name="c", persistence_store=store, config=config)
    def call():
        if should_fail["value"]:
            raise ConnectionError("down")
        return "ok"

    # Two failures, then a success: the streak resets, so the circuit must NOT be tripping.
    for _ in range(2):
        with pytest.raises(ConnectionError):
            call()
    should_fail["value"] = False
    assert call() == "ok"
    assert "c" not in store.db

    # A fresh run of 3 consecutive failures from here must trip it.
    should_fail["value"] = True
    for _ in range(3):
        with pytest.raises(ConnectionError):
            call()
    assert store.db["c"].state == CircuitState.OPEN


def test_circuit_can_retrip_after_a_previous_close(store):
    # Regression guard: a healthy circuit's steady state is a *persisted CLOSED* record.
    # Reading that record must not reset the running failure counter, or the circuit
    # could never trip again after it has closed once.
    config = CircuitBreakerConfig(failure_threshold=3, local_cache_max_age=0)

    # Pretend a prior recovery left a persisted CLOSED record behind.
    store.db["c"] = CircuitStateRecord(name="c", state=CircuitState.CLOSED, failure_count=0)

    @circuit_breaker(name="c", persistence_store=store, config=config)
    def call():
        raise ConnectionError("down again")

    for _ in range(3):
        with pytest.raises(ConnectionError):
            call()

    assert store.db["c"].state == CircuitState.OPEN, "circuit must re-trip even with a prior CLOSED record present"


def test_full_lifecycle_survives_multiple_recovery_cycles(store):
    # End-to-end guard tying #1 together: the circuit must cycle OPEN -> HALF_OPEN ->
    # CLOSED, re-trip, survive a failed probe (which reopens and must release the lock),
    # and then recover again. Before the owner-release fix the second recovery dead-locked.
    config = CircuitBreakerConfig(
        failure_threshold=2,
        recovery_timeout=30,
        success_threshold=2,
        local_cache_max_age=0,
    )
    mode = {"value": "fail"}

    @circuit_breaker(name="c", persistence_store=store, config=config)
    def call():
        if mode["value"] == "fail":
            raise ConnectionError("down")
        return "ok"

    def elapse_recovery_window():
        store.db["c"].opened_at -= 100

    # Trip open.
    for _ in range(2):
        with pytest.raises(ConnectionError):
            call()
    assert store.db["c"].state == CircuitState.OPEN

    # Recover through two successful probes.
    mode["value"] = "ok"
    elapse_recovery_window()
    assert call() == "ok"
    assert store.db["c"].state == CircuitState.HALF_OPEN
    assert call() == "ok"
    assert store.db["c"].state == CircuitState.CLOSED

    # Re-trip from the now-CLOSED state.
    mode["value"] = "fail"
    for _ in range(2):
        with pytest.raises(ConnectionError):
            call()
    assert store.db["c"].state == CircuitState.OPEN

    # A failed probe reopens it and must release the probe lock.
    elapse_recovery_window()
    with pytest.raises(ConnectionError):
        call()
    assert store.db["c"].state == CircuitState.OPEN
    assert store.db["c"].half_open_owner is None

    # The lock being free, recovery must be possible again.
    mode["value"] = "ok"
    elapse_recovery_window()
    assert call() == "ok"
    assert store.db["c"].state == CircuitState.HALF_OPEN
    assert call() == "ok"
    assert store.db["c"].state == CircuitState.CLOSED


def test_opened_at_zero_is_treated_as_a_real_timestamp(store):
    # Bug #7: opened_at == 0 is a valid (if pathological) epoch timestamp, not "missing".
    # `record.opened_at or self._now()` wrongly re-anchors it to now, pinning OPEN forever.
    store.db["c"] = CircuitStateRecord(name="c", state=CircuitState.OPEN, failure_count=5, opened_at=0)
    config = CircuitBreakerConfig(recovery_timeout=30, success_threshold=1, local_cache_max_age=0)

    @circuit_breaker(name="c", persistence_store=store, config=config)
    def call():
        return "recovered"

    # opened_at=0 is far in the past, so the recovery window has long elapsed:
    # the call must be allowed to probe, not short-circuited.
    assert call() == "recovered"
    assert store.db["c"].state in (CircuitState.HALF_OPEN, CircuitState.CLOSED)


def test_ignored_exception_does_not_trip_circuit(store):
    config = CircuitBreakerConfig(
        failure_threshold=2,
        handled_exceptions=(ConnectionError,),
        local_cache_max_age=0,
    )

    @circuit_breaker(name="c", persistence_store=store, config=config)
    def call():
        raise ValueError("caller error, not a downstream failure")

    for _ in range(5):
        with pytest.raises(ValueError):
            call()

    assert "c" not in store.db


def test_disabled_env_bypasses_circuit(store, now, monkeypatch):
    monkeypatch.setenv("POWERTOOLS_CIRCUIT_BREAKER_DISABLED", "true")
    store.db["c"] = CircuitStateRecord(name="c", state=CircuitState.OPEN, failure_count=9, opened_at=now)
    config = CircuitBreakerConfig(recovery_timeout=9999, local_cache_max_age=0)

    @circuit_breaker(name="c", persistence_store=store, config=config)
    def call():
        return "ran anyway"

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        assert call() == "ran anyway"


def test_config_is_optional(store):
    @circuit_breaker(name="c", persistence_store=store)
    def call():
        return "ok"

    assert call() == "ok"


# --------------------------------------------------------------------------- on_transition hook


def test_on_transition_fires_for_each_state_change(store):
    transitions: list[CircuitTransition] = []
    config = CircuitBreakerConfig(
        failure_threshold=2,
        recovery_timeout=30,
        success_threshold=1,
        local_cache_max_age=0,
    )
    mode = {"value": "fail"}

    @circuit_breaker(
        name="c",
        persistence_store=store,
        on_transition=transitions.append,
        config=config,
    )
    def call():
        if mode["value"] == "fail":
            raise ConnectionError("down")
        return "ok"

    # CLOSED -> OPEN after 2 failures.
    for _ in range(2):
        with pytest.raises(ConnectionError):
            call()
    # OPEN -> HALF_OPEN (election) -> CLOSED (success_threshold=1) on the recovery probe.
    mode["value"] = "ok"
    store.db["c"].opened_at -= 100
    assert call() == "ok"

    pairs = [(t.from_state, t.to_state) for t in transitions]
    assert pairs == [
        (CircuitState.CLOSED, CircuitState.OPEN),
        (CircuitState.OPEN, CircuitState.HALF_OPEN),
        (CircuitState.HALF_OPEN, CircuitState.CLOSED),
    ]
    assert all(t.circuit_name == "c" for t in transitions)
    # opened_at carried on the open/probe transitions, absent on close.
    assert transitions[0].opened_at is not None
    assert transitions[-1].opened_at is None


def test_on_transition_fires_on_failed_probe_reopen(store, now):
    transitions: list[CircuitTransition] = []
    store.db["c"] = CircuitStateRecord(name="c", state=CircuitState.OPEN, failure_count=5, opened_at=now - 100)
    config = CircuitBreakerConfig(recovery_timeout=30, success_threshold=2, local_cache_max_age=0)

    @circuit_breaker(name="c", persistence_store=store, on_transition=transitions.append, config=config)
    def call():
        raise ConnectionError("still down")

    with pytest.raises(ConnectionError):
        call()

    pairs = [(t.from_state, t.to_state) for t in transitions]
    assert pairs == [
        (CircuitState.OPEN, CircuitState.HALF_OPEN),
        (CircuitState.HALF_OPEN, CircuitState.OPEN),
    ]


def test_raising_on_transition_hook_is_swallowed(store):
    config = CircuitBreakerConfig(failure_threshold=1, local_cache_max_age=0)

    def boom(_transition):
        raise RuntimeError("hook blew up")

    @circuit_breaker(name="c", persistence_store=store, on_transition=boom, config=config)
    def call():
        raise ConnectionError("down")

    # The hook raises during the CLOSED->OPEN notify, but the protected call's own
    # ConnectionError must surface unchanged, not the hook's RuntimeError.
    with pytest.raises(ConnectionError):
        call()
    assert store.db["c"].state == CircuitState.OPEN
