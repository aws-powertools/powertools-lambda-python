from __future__ import annotations

import pytest

import aws_lambda_powertools.utilities.circuit_breaker_alpha.base as base_module
from aws_lambda_powertools.utilities.circuit_breaker_alpha.persistence.base import (
    CircuitBreakerExistingLockError,
    CircuitBreakerPersistenceLayer,
    CircuitBreakerRecordNotFoundError,
)
from aws_lambda_powertools.utilities.circuit_breaker_alpha.persistence.record import CircuitStateRecord


class FakePersistence(CircuitBreakerPersistenceLayer):
    """In-memory store for exercising the handler state machine without DynamoDB."""

    def __init__(self):
        self.db: dict[str, CircuitStateRecord] = {}
        super().__init__()

    def _get_record(self, name: str) -> CircuitStateRecord:
        if name not in self.db:
            raise CircuitBreakerRecordNotFoundError
        stored = self.db[name]
        # Return a copy so the handler can't mutate stored state by reference.
        return CircuitStateRecord(
            name=stored.name,
            state=stored.state,
            failure_count=stored.failure_count,
            opened_at=stored.opened_at,
            half_open_owner=stored.half_open_owner,
        )

    def _put_record(self, record: CircuitStateRecord, condition: str | None = None) -> None:
        if condition == "half_open":
            existing = self.db.get(record.name)
            if existing is not None and existing.half_open_owner is not None:
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
        # Leaving HALF_OPEN (close or reopen) always releases the probe-owner lock; only
        # opened_at differs between the two transitions. This mirrors the DynamoDB backend.
        existing.half_open_owner = None
        existing.opened_at = record.opened_at


@pytest.fixture
def store() -> FakePersistence:
    return FakePersistence()


@pytest.fixture(autouse=True)
def reset_local_counters():
    """Clear the per-environment module-level counters between tests."""
    base_module._LOCAL_FAILURES.clear()
    base_module._LOCAL_SUCCESSES.clear()
    yield
    base_module._LOCAL_FAILURES.clear()
    base_module._LOCAL_SUCCESSES.clear()


@pytest.fixture
def now() -> int:
    return base_module.CircuitBreakerHandler._now()
