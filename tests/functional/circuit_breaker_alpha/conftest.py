from __future__ import annotations

import pytest

import aws_lambda_powertools.utilities.circuit_breaker_alpha.base as base_module
from aws_lambda_powertools.utilities.circuit_breaker_alpha.base import CircuitBreakerHandler
from aws_lambda_powertools.utilities.circuit_breaker_alpha.persistence.base import (
    CircuitBreakerExistingLockError,
    CircuitBreakerPersistenceLayer,
)
from aws_lambda_powertools.utilities.circuit_breaker_alpha.persistence.record import CircuitStateRecord
from aws_lambda_powertools.utilities.circuit_breaker_alpha.states import CircuitState


class FakePersistence(CircuitBreakerPersistenceLayer):
    """In-memory store for exercising the handler state machine without DynamoDB."""

    def __init__(self):
        self.db: dict[str, CircuitStateRecord] = {}
        super().__init__()

    def _get_record(self, name: str) -> CircuitStateRecord | None:
        if name not in self.db:
            return None
        stored = self.db[name]
        # Return a copy so the handler can't mutate stored state by reference.
        return CircuitStateRecord(
            name=stored.name,
            state=stored.state,
            failure_count=stored.failure_count,
            opened_at=stored.opened_at,
            half_open_owner=stored.half_open_owner,
            probe_lease_expiry=stored.probe_lease_expiry,
        )

    def _put_record(
        self,
        record: CircuitStateRecord,
        condition: str | None = None,
        expected_opened_at: int | None = None,
    ) -> None:
        if condition == "half_open":
            existing = self.db.get(record.name)
            now = CircuitBreakerHandler._now()

            # Mirror the DynamoDB condition: two valid paths
            # Path 1: state=OPEN AND no owner (AND opened_at matches if provided)
            # Path 2: state=HALF_OPEN AND probe_lease_expiry <= now (lease takeover)
            fresh_election_ok = existing is None or (
                existing.state == CircuitState.OPEN
                and existing.half_open_owner is None
                and (expected_opened_at is None or existing.opened_at == expected_opened_at)
            )
            lease_takeover_ok = (
                existing is not None
                and existing.state == CircuitState.HALF_OPEN
                and existing.probe_lease_expiry is not None
                and now >= existing.probe_lease_expiry
            )

            if not fresh_election_ok and not lease_takeover_ok:
                raise CircuitBreakerExistingLockError
        self.db[record.name] = record

    def _update_record(self, record: CircuitStateRecord) -> None:
        # Mirror DynamoDB UpdateItem semantics: a partial merge driven by which
        # attributes the backend actually writes, NOT a wholesale replace. This is
        # what exposes attributes the update path forgets to clear (e.g. a stale
        # half_open_owner left behind on reopen).
        existing = self.db.get(record.name)
        if existing is None:
            self.db[record.name] = record
            return
        existing.state = record.state
        existing.failure_count = record.failure_count
        existing.expiry_timestamp = record.expiry_timestamp
        # Leaving HALF_OPEN (close or reopen) always releases the probe-owner lock and
        # probe lease; only opened_at differs between the two transitions.
        existing.half_open_owner = None
        existing.probe_lease_expiry = None
        existing.opened_at = record.opened_at


@pytest.fixture
def store() -> FakePersistence:
    return FakePersistence()


@pytest.fixture(autouse=True)
def reset_local_counters():
    """Clear the per-environment module-level counters between tests."""
    base_module._LOCAL_FAILURES.clear()
    base_module._LOCAL_SUCCESSES.clear()
    base_module._LAST_OBSERVED_STATE.clear()
    yield
    base_module._LOCAL_FAILURES.clear()
    base_module._LOCAL_SUCCESSES.clear()
    base_module._LAST_OBSERVED_STATE.clear()


@pytest.fixture
def now() -> int:
    return base_module.CircuitBreakerHandler._now()
