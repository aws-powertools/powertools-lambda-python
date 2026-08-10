from __future__ import annotations

import dataclasses

import pytest

from aws_lambda_powertools.utilities.circuit_breaker.config import CircuitBreakerConfig
from aws_lambda_powertools.utilities.circuit_breaker.exceptions import (
    CircuitBreakerConfigError,
    CircuitBreakerOpenError,
)
from aws_lambda_powertools.utilities.circuit_breaker.persistence.record import CircuitStateRecord
from aws_lambda_powertools.utilities.circuit_breaker.states import CircuitInfo, CircuitState


def test_circuit_state_serializes_to_plain_string():
    assert str(CircuitState.OPEN) == "OPEN"
    assert CircuitState.OPEN == "OPEN"


def test_circuit_info_is_immutable():
    info = CircuitInfo(name="payment", state=CircuitState.OPEN, failure_count=5, opened_at=123)
    with pytest.raises(dataclasses.FrozenInstanceError):
        info.name = "other"  # type: ignore[misc]


def test_config_defaults():
    config = CircuitBreakerConfig()
    assert config.failure_threshold == 5
    assert config.recovery_timeout == 30
    assert config.success_threshold == 3
    assert config.local_cache_max_age == 5
    assert config.handled_exceptions is None
    assert config.ignored_exceptions is None


def test_config_rejects_both_exception_lists():
    with pytest.raises(CircuitBreakerConfigError, match="mutually exclusive"):
        CircuitBreakerConfig(handled_exceptions=(TimeoutError,), ignored_exceptions=(ValueError,))


@pytest.mark.parametrize("field", ["failure_threshold", "recovery_timeout", "success_threshold"])
def test_config_rejects_non_positive_thresholds(field):
    with pytest.raises(CircuitBreakerConfigError, match="positive integer"):
        CircuitBreakerConfig(**{field: 0})


def test_config_allows_zero_cache_age():
    assert CircuitBreakerConfig(local_cache_max_age=0).local_cache_max_age == 0


def test_config_rejects_negative_cache_age():
    with pytest.raises(CircuitBreakerConfigError, match="non-negative"):
        CircuitBreakerConfig(local_cache_max_age=-1)


def test_counts_as_failure_default_any_exception():
    config = CircuitBreakerConfig()
    assert config.counts_as_failure(ValueError()) is True
    assert config.counts_as_failure(TimeoutError()) is True


def test_counts_as_failure_allowlist():
    config = CircuitBreakerConfig(handled_exceptions=(TimeoutError, ConnectionError))
    assert config.counts_as_failure(TimeoutError()) is True
    assert config.counts_as_failure(ValueError()) is False


def test_counts_as_failure_denylist():
    config = CircuitBreakerConfig(ignored_exceptions=(ValueError,))
    assert config.counts_as_failure(ValueError()) is False
    assert config.counts_as_failure(KeyError()) is True


def test_config_normalizes_handled_exceptions_list_to_tuple():
    config = CircuitBreakerConfig(handled_exceptions=[TimeoutError, ConnectionError])
    assert config.handled_exceptions == (TimeoutError, ConnectionError)
    # The reported bug: a list must not break counts_as_failure when the circuit evaluates a failure.
    assert config.counts_as_failure(TimeoutError()) is True
    assert config.counts_as_failure(ValueError()) is False


def test_config_normalizes_single_exception_type_to_tuple():
    config = CircuitBreakerConfig(handled_exceptions=ValueError)
    assert config.handled_exceptions == (ValueError,)
    assert config.counts_as_failure(ValueError()) is True


def test_config_normalizes_ignored_exceptions_list_to_tuple():
    config = CircuitBreakerConfig(ignored_exceptions=[ValueError])
    assert config.ignored_exceptions == (ValueError,)
    assert config.counts_as_failure(ValueError()) is False
    assert config.counts_as_failure(KeyError()) is True


def test_config_normalizes_iterator_of_exceptions():
    config = CircuitBreakerConfig(handled_exceptions=iter((TimeoutError, KeyError)))
    assert config.handled_exceptions == (TimeoutError, KeyError)


@pytest.mark.parametrize("field", ["handled_exceptions", "ignored_exceptions"])
def test_config_rejects_non_exception_type_in_list(field):
    with pytest.raises(CircuitBreakerConfigError, match="only exception types"):
        CircuitBreakerConfig(**{field: ["not-an-exception"]})


@pytest.mark.parametrize("field", ["handled_exceptions", "ignored_exceptions"])
@pytest.mark.parametrize("value", [5, "ValueError"])
def test_config_rejects_non_iterable_or_str_exceptions(field, value):
    with pytest.raises(CircuitBreakerConfigError, match="iterable of exception types"):
        CircuitBreakerConfig(**{field: value})


@pytest.mark.parametrize("field", ["handled_exceptions", "ignored_exceptions"])
def test_config_rejects_empty_exceptions(field):
    with pytest.raises(CircuitBreakerConfigError, match="at least one exception type"):
        CircuitBreakerConfig(**{field: []})


def test_open_error_carries_circuit_info():
    info = CircuitInfo(name="payment", state=CircuitState.OPEN, failure_count=5, opened_at=123)
    error = CircuitBreakerOpenError("open", circuit=info)
    assert error.circuit is info


def test_record_to_circuit_info_strips_internal_fields():
    record = CircuitStateRecord(
        name="payment",
        state=CircuitState.OPEN,
        failure_count=5,
        opened_at=123,
        half_open_owner="env-abc",
        expiry_timestamp=999,
    )
    info = record.to_circuit_info()
    assert info == CircuitInfo(name="payment", state=CircuitState.OPEN, failure_count=5, opened_at=123)
    assert not hasattr(info, "half_open_owner")
    assert not hasattr(info, "expiry_timestamp")
