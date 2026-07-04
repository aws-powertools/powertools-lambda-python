from __future__ import annotations

import threading
import warnings

import pytest

import aws_lambda_powertools.utilities.circuit_breaker_alpha.base as base_module
from aws_lambda_powertools.utilities.circuit_breaker_alpha import (
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    CircuitState,
    CircuitTransition,
    circuit_breaker,
)
from aws_lambda_powertools.utilities.circuit_breaker_alpha.exceptions import CircuitBreakerError
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


# --------------------------------------------------------------------------- bug regressions


def test_stale_local_failures_reset_on_external_close(store, now):
    """Bug 1: a partial failure streak in env A must not survive an external recovery cycle."""
    config = CircuitBreakerConfig(failure_threshold=3, local_cache_max_age=0)
    mode = {"value": "fail"}

    @circuit_breaker(name="c", persistence_store=store, config=config)
    def call():
        if mode["value"] == "fail":
            raise ConnectionError("down")
        return "ok"

    # Env A accumulates 2 failures (below threshold of 3).
    for _ in range(2):
        with pytest.raises(ConnectionError):
            call()
    assert base_module._LOCAL_FAILURES["c"] == 2

    # Simulate: another env trips the circuit, then a third closes it.
    store.db["c"] = CircuitStateRecord(name="c", state=CircuitState.OPEN, failure_count=3, opened_at=now)
    # Force env A to observe OPEN so _LAST_OBSERVED_STATE tracks the transition.
    with pytest.raises(CircuitBreakerOpenError):
        call()
    # Now the circuit is externally closed.
    store.db["c"] = CircuitStateRecord(name="c", state=CircuitState.CLOSED, failure_count=0)

    # A single failure in env A must NOT re-trip (stale streak was invalidated).
    mode["value"] = "fail"
    with pytest.raises(ConnectionError):
        call()
    assert "c" not in store.db or store.db["c"].state == CircuitState.CLOSED
    assert base_module._LOCAL_FAILURES["c"] == 1  # fresh count, not 3


def test_store_write_failure_does_not_mask_downstream_result(store, now):
    """Bug 2: if save_closed() fails, the successful probe result must still be returned."""
    config = CircuitBreakerConfig(failure_threshold=3, recovery_timeout=30, success_threshold=1, local_cache_max_age=0)

    store.db["c"] = CircuitStateRecord(name="c", state=CircuitState.OPEN, failure_count=3, opened_at=now - 100)

    @circuit_breaker(name="c", persistence_store=store, config=config)
    def call():
        return "payment_charged"

    # Make the persistence write fail.
    original_update = store._update_record

    def failing_update(record):
        raise RuntimeError("DynamoDB timeout")

    store._update_record = failing_update

    # The probe should still return the downstream result despite the write failure.
    result = call()
    assert result == "payment_charged"

    store._update_record = original_update


def test_store_write_failure_on_trip_does_not_replace_downstream_exception(store):
    """Bug 2 (trip path): if save_open() fails, the downstream's own exception must propagate."""
    config = CircuitBreakerConfig(failure_threshold=2, local_cache_max_age=0)

    @circuit_breaker(name="c", persistence_store=store, config=config)
    def call():
        raise ConnectionError("the real error")

    # Make the persistence write fail.
    def failing_put(record, condition=None, expected_opened_at=None):
        raise RuntimeError("DynamoDB throttle")

    store._put_record = failing_put

    # Two failures should raise the ORIGINAL ConnectionError, not a RuntimeError from the store.
    for _ in range(2):
        with pytest.raises(ConnectionError, match="the real error"):
            call()


def test_probe_lease_takeover_when_owner_recycled(store, now):
    """Design issue 1: a stranded HALF_OPEN probe with expired lease can be taken over."""
    config = CircuitBreakerConfig(recovery_timeout=30, success_threshold=1, local_cache_max_age=0)

    # Simulate: the probe owner ("dead-env") was recycled, lease has expired.
    store.db["c"] = CircuitStateRecord(
        name="c",
        state=CircuitState.HALF_OPEN,
        opened_at=now - 200,
        half_open_owner="dead-env",
        probe_lease_expiry=now - 10,  # expired
    )

    @circuit_breaker(name="c", persistence_store=store, config=config)
    def call():
        return "recovered"

    # Current environment should take over the expired lease and succeed.
    result = call()
    assert result == "recovered"
    assert store.db["c"].state == CircuitState.CLOSED


def test_half_open_non_owner_with_active_lease_is_rejected(store, now):
    """Design issue 1 negative: active lease must NOT allow takeover."""
    config = CircuitBreakerConfig(recovery_timeout=30, success_threshold=1, local_cache_max_age=0)

    # Probe owner is alive (lease not expired yet).
    store.db["c"] = CircuitStateRecord(
        name="c",
        state=CircuitState.HALF_OPEN,
        opened_at=now - 50,
        half_open_owner="other-env",
        probe_lease_expiry=now + 999,  # far in the future
    )

    @circuit_breaker(name="c", persistence_store=store, config=config)
    def call():
        return "should not run"

    with pytest.raises(CircuitBreakerOpenError):
        call()


def test_half_open_expired_lease_lost_takeover_returns_open_response(store, now):
    """Losing the takeover election must NOT probe: another thread/environment won
    the conditional write between our expiry check and our acquire, so the call
    has to get the open-circuit response — electing every candidate is exactly
    the multi-prober bug the per-thread owner id exists to prevent."""
    config = CircuitBreakerConfig(recovery_timeout=30, success_threshold=1, local_cache_max_age=0)

    # A stranded probe with an expired lease, owned by someone else.
    store.db["c"] = CircuitStateRecord(
        name="c",
        state=CircuitState.HALF_OPEN,
        opened_at=now - 200,
        half_open_owner="dead-env",
        probe_lease_expiry=now - 10,  # expired — takeover will be attempted
    )

    # The race's loser: the conditional election fails.
    def lost_election(name, owner_id, opened_at):
        return False

    store.try_acquire_half_open = lost_election

    protected_ran = {"value": False}

    @circuit_breaker(name="c", persistence_store=store, config=config)
    def call():
        protected_ran["value"] = True
        return "must not probe"

    with pytest.raises(CircuitBreakerOpenError):
        call()
    assert protected_ran["value"] is False


def test_open_lost_election_returns_open_response(store, now):
    """Branch: try_acquire_half_open returns False (another env won the race)."""
    config = CircuitBreakerConfig(recovery_timeout=30, success_threshold=1, local_cache_max_age=0)

    # Circuit is OPEN and recovery window has elapsed, but election will fail
    # because another env already holds the lock.
    store.db["c"] = CircuitStateRecord(
        name="c",
        state=CircuitState.OPEN,
        failure_count=5,
        opened_at=now - 100,
        half_open_owner="winner-env",
    )

    @circuit_breaker(name="c", persistence_store=store, config=config)
    def call():
        return "should not run"

    with pytest.raises(CircuitBreakerOpenError):
        call()


def test_probe_ignored_exception_propagates_without_affecting_circuit(store, now):
    """Branch: probe raises an exception that doesn't count as failure."""
    config = CircuitBreakerConfig(
        recovery_timeout=30,
        success_threshold=1,
        handled_exceptions=(ConnectionError,),
        local_cache_max_age=0,
    )

    store.db["c"] = CircuitStateRecord(name="c", state=CircuitState.OPEN, failure_count=5, opened_at=now - 100)

    @circuit_breaker(name="c", persistence_store=store, config=config)
    def call():
        raise ValueError("not a counted failure")

    with pytest.raises(ValueError, match="not a counted failure"):
        call()
    # Circuit should still be HALF_OPEN (not reopened), the ValueError didn't count.
    assert store.db["c"].state == CircuitState.HALF_OPEN


def test_local_cache_serves_state_without_store_read(store):
    """Covers the cache hit path (persistence/base.py line 140)."""
    config = CircuitBreakerConfig(failure_threshold=3, local_cache_max_age=60)
    call_count = {"value": 0}

    @circuit_breaker(name="c", persistence_store=store, config=config)
    def call():
        call_count["value"] += 1
        return "ok"

    # First call reads the store (cache miss).
    assert call() == "ok"
    # Second call should serve from cache — override _get_record to detect reads.
    original_get = store._get_record
    get_called = {"value": False}

    def tracked_get(name):
        get_called["value"] = True
        return original_get(name)

    store._get_record = tracked_get
    assert call() == "ok"
    assert not get_called["value"], "second call should have used the cache, not the store"
    store._get_record = original_get


def test_error_with_details_formatting():
    """Covers exceptions.py line 28 — __str__ with details."""
    err = CircuitBreakerError("main message", "extra detail")
    assert str(err) == "main message - (extra detail)"


# --------------------------------------------------------------------------- thread safety (#8320)


def _run_in_threads(worker, count):
    threads = [threading.Thread(target=worker) for _ in range(count)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()


def test_threads_elect_a_single_prober_on_recovery(store, now):
    """Regression for #8320: after one thread wins the election, siblings must not also probe."""
    store.db["c"] = CircuitStateRecord(name="c", state=CircuitState.OPEN, failure_count=5, opened_at=now - 60)
    # success_threshold=2 keeps the circuit HALF_OPEN after the winning probe, so a
    # late-reading loser can never legitimately run the function through a closed circuit.
    config = CircuitBreakerConfig(recovery_timeout=30, success_threshold=2, local_cache_max_age=0)
    probes = []
    open_responses = []
    barrier = threading.Barrier(8)

    @circuit_breaker(name="c", persistence_store=store, config=config)
    def call():
        probes.append(threading.current_thread().name)
        return "ok"

    def worker():
        barrier.wait(timeout=10)
        try:
            call()
        except CircuitBreakerOpenError:
            open_responses.append(threading.current_thread().name)

    _run_in_threads(worker, 8)

    assert len(probes) == 1, "exactly one thread must probe per recovery window"
    assert len(open_responses) == 7, "every other thread must get the open response"
    assert store.db["c"].state == CircuitState.HALF_OPEN
    assert store.db["c"].half_open_owner is not None


def test_threads_trip_at_exactly_the_failure_threshold(store):
    """Racing increments must neither lose updates (tripping late) nor persist the trip twice."""
    threads_count, threshold = 8, 5
    config = CircuitBreakerConfig(failure_threshold=threshold, local_cache_max_age=0)
    barrier = threading.Barrier(threads_count)
    siblings_done = threading.Event()
    done_lock = threading.Lock()
    finished = []
    save_open_counts = []
    original_save_open = store.save_open

    def blocking_save_open(name, failure_count, opened_at):
        save_open_counts.append(failure_count)
        if len(save_open_counts) > 1:
            # A second persist is the bug itself; unblock immediately so it fails fast.
            siblings_done.set()
        # Park the tripping thread mid-persist until every sibling has recorded its
        # failure. Code that resets the counter only after persisting lets the
        # remaining threads cross the threshold too and persist the trip again.
        siblings_done.wait(timeout=10)
        original_save_open(name, failure_count=failure_count, opened_at=opened_at)

    store.save_open = blocking_save_open

    @circuit_breaker(name="c", persistence_store=store, config=config)
    def call():
        # Hold every thread inside the protected call so all pass the CLOSED check
        # before any failure is recorded, forcing the increments to race.
        barrier.wait(timeout=10)
        raise ConnectionError("downstream down")

    raised = []

    def worker():
        try:
            call()
        except ConnectionError:
            raised.append(threading.current_thread().name)
        finally:
            with done_lock:
                finished.append(threading.current_thread().name)
                if len(finished) == threads_count - 1:
                    # Only the tripping thread is still parked in the persist spy.
                    siblings_done.set()

    _run_in_threads(worker, threads_count)

    assert save_open_counts == [threshold], "the trip must be persisted exactly once, at the threshold"
    assert store.db["c"].state == CircuitState.OPEN
    assert len(raised) == threads_count
    assert base_module._LOCAL_FAILURES["c"] == threads_count - threshold, "post-trip failures restart the streak"


def test_probe_ownership_is_per_thread_and_stable_across_invocations(store, now):
    store.db["c"] = CircuitStateRecord(name="c", state=CircuitState.OPEN, failure_count=5, opened_at=now - 60)
    config = CircuitBreakerConfig(recovery_timeout=30, success_threshold=2, local_cache_max_age=0)
    calls = []

    @circuit_breaker(name="c", persistence_store=store, config=config)
    def call():
        calls.append(threading.current_thread().name)
        return "ok"

    # This thread wins the election; one more probe success is needed to close.
    assert call() == "ok"
    assert store.db["c"].state == CircuitState.HALF_OPEN

    # A sibling thread must not inherit ownership (it did when the id was per-process).
    sibling_outcome = []

    def sibling():
        try:
            sibling_outcome.append(call())
        except CircuitBreakerOpenError:
            sibling_outcome.append("rejected")

    _run_in_threads(sibling, 1)
    assert sibling_outcome == ["rejected"]

    # The owner's identity must survive across invocations so it can finish the recovery;
    # a per-handler or per-invocation id would strand the circuit until the lease expired.
    assert call() == "ok"
    assert store.db["c"].state == CircuitState.CLOSED
    assert len(calls) == 2


def test_single_probe_spans_environments_and_threads(store, now):
    """The same election covers threads in one process and separate environments."""
    other_env = type(store)()
    other_env.db = store.db
    store.db["c"] = CircuitStateRecord(name="c", state=CircuitState.OPEN, failure_count=5, opened_at=now - 60)
    config = CircuitBreakerConfig(recovery_timeout=30, success_threshold=2, local_cache_max_age=0)
    probes = []
    open_responses = []
    barrier = threading.Barrier(8)

    def protect(persistence):
        @circuit_breaker(name="c", persistence_store=persistence, config=config)
        def call():
            probes.append(threading.current_thread().name)
            return "ok"

        return call

    calls = [protect(store), protect(other_env)]

    def worker(index):
        env_call = calls[index % 2]
        barrier.wait(timeout=10)
        try:
            env_call()
        except CircuitBreakerOpenError:
            open_responses.append(threading.current_thread().name)

    threads = [threading.Thread(target=worker, args=(index,)) for index in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(probes) == 1, "one probe across all threads of all environments"
    assert len(open_responses) == 7


def test_settings_are_kept_per_circuit_on_a_shared_layer(store, now):
    """Configuring another circuit on the same layer must not stamp this one's probe lease."""
    store.configure(CircuitBreakerConfig(recovery_timeout=30, local_cache_max_age=0), circuit_name="a")
    store.configure(CircuitBreakerConfig(recovery_timeout=9999, local_cache_max_age=0), circuit_name="b")
    store.db["a"] = CircuitStateRecord(name="a", state=CircuitState.OPEN, failure_count=5, opened_at=now - 60)

    assert store.try_acquire_half_open("a", "owner-1", now - 60)

    lease = store.db["a"].probe_lease_expiry
    assert lease is not None
    assert lease <= now + 30 + 2, "the lease must derive from circuit 'a' recovery_timeout, not 'b'"
