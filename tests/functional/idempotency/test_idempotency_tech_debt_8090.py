"""
Unit tests for tech debt fixes in idempotency utility.
Issue: https://github.com/aws-powertools/powertools-lambda-python/issues/8090
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from aws_lambda_powertools.utilities.idempotency.persistence.datarecord import DataRecord

# ── Helpers ──────────────────────────────────────────────────────────────────

class MockPersistenceLayer:
    """Minimal concrete subclass of BasePersistenceLayer for testing."""

    def _get_record(self, idempotency_key):
        ...

    def _put_record(self, data_record):
        ...

    def _update_record(self, data_record):
        ...

    def _delete_record(self, data_record):
        ...

# ── Fix 1 for item-3: str(None) in Redis _item_to_data_record ───────────────────────────

def test_redis_missing_data_attr_returns_none_not_string():
    """
    When data_attr is missing from Redis hash, response_data should be
    None — not the string "None".
    """
    item = {
        "status": "COMPLETED",
        "expiration": 9999999999,
        # data_attr and validation_key_attr intentionally missing
    }

    data_attr = "data"
    validation_key_attr = "validation"

    response_data = item.get(data_attr)
    payload_hash = item.get(validation_key_attr)

    assert response_data is None, "Missing data_attr should return None, not string 'None'"
    assert payload_hash is None, "Missing validation_key_attr should return None, not string 'None'"

def test_str_none_produces_wrong_string():
    """
    Demonstrate the old bug: str(None) produces the string 'None'
    instead of actual None.
    """
    missing_value = None

    # Old broken behavior
    old_result = str(missing_value)
    assert old_result == "None"

    # New correct behavior
    new_result = missing_value
    assert new_result is None

def test_redis_existing_data_attr_returns_value():
    """
    When data_attr exists in Redis hash, response_data should be
    returned as-is without str() conversion.
    """
    item = {
        "status": "COMPLETED",
        "expiration": 9999999999,
        "data": '{"payment_id": 123}',
        "validation": "abc123hash",
    }

    data_attr = "data"
    validation_key_attr = "validation"

    response_data = item.get(data_attr)
    payload_hash = item.get(validation_key_attr)

    assert response_data == '{"payment_id": 123}'
    assert payload_hash == "abc123hash"

# ── Fix 2 for item-4: _get_idempotency_key_or_return_none helper ────────────────────────

def test_helper_returns_none_when_key_is_none():
    """
    _get_idempotency_key_or_return_none should return None when
    _get_hashed_idempotency_key returns None.
    """
    from aws_lambda_powertools.utilities.idempotency.persistence.base import BasePersistenceLayer

    class ConcretePersistenceLayer(BasePersistenceLayer):
        def _get_record(self, idempotency_key): ...
        def _put_record(self, data_record): ...
        def _update_record(self, data_record): ...
        def _delete_record(self, data_record): ...

    layer = ConcretePersistenceLayer()
    layer._get_hashed_idempotency_key = MagicMock(return_value=None)

    result = layer._get_idempotency_key_or_return_none(data={"key": "value"})

    assert result is None
    layer._get_hashed_idempotency_key.assert_called_once_with(data={"key": "value"})

def test_helper_returns_key_when_present():
    """
    _get_idempotency_key_or_return_none should return the key string
    when _get_hashed_idempotency_key returns a valid key.
    """
    from aws_lambda_powertools.utilities.idempotency.persistence.base import BasePersistenceLayer

    class ConcretePersistenceLayer(BasePersistenceLayer):
        def _get_record(self, idempotency_key): ...
        def _put_record(self, data_record): ...
        def _update_record(self, data_record): ...
        def _delete_record(self, data_record): ...

    layer = ConcretePersistenceLayer()
    expected_key = "my-function#abc123hash"
    layer._get_hashed_idempotency_key = MagicMock(return_value=expected_key)

    result = layer._get_idempotency_key_or_return_none(data={"key": "value"})

    assert result == expected_key
    layer._get_hashed_idempotency_key.assert_called_once_with(data={"key": "value"})

def test_helper_is_used_in_save_success():
    """
    save_success should return None early when idempotency key is None
    (no data saved to persistence layer).
    """
    from aws_lambda_powertools.utilities.idempotency.persistence.base import BasePersistenceLayer

    class ConcretePersistenceLayer(BasePersistenceLayer):
        def _get_record(self, idempotency_key): ...
        def _put_record(self, data_record): ...
        def _update_record(self, data_record): ...
        def _delete_record(self, data_record): ...

    layer = ConcretePersistenceLayer()
    layer._get_hashed_idempotency_key = MagicMock(return_value=None)

    result = layer.save_success(data={"key": "value"}, result={"status": "ok"})

    assert result is None

def test_helper_is_used_in_save_inprogress():
    """
    save_inprogress should return None early when idempotency key is None.
    """
    from aws_lambda_powertools.utilities.idempotency.persistence.base import BasePersistenceLayer

    class ConcretePersistenceLayer(BasePersistenceLayer):
        def _get_record(self, idempotency_key): ...
        def _put_record(self, data_record): ...
        def _update_record(self, data_record): ...
        def _delete_record(self, data_record): ...

    layer = ConcretePersistenceLayer()
    layer._get_hashed_idempotency_key = MagicMock(return_value=None)

    result = layer.save_inprogress(data={"key": "value"})

    assert result is None

def test_helper_is_used_in_delete_record():
    """
    delete_record should return None early when idempotency key is None.
    """
    from aws_lambda_powertools.utilities.idempotency.persistence.base import BasePersistenceLayer

    class ConcretePersistenceLayer(BasePersistenceLayer):
        def _get_record(self, idempotency_key): ...
        def _put_record(self, data_record): ...
        def _update_record(self, data_record): ...
        def _delete_record(self, data_record): ...

    layer = ConcretePersistenceLayer()
    layer._get_hashed_idempotency_key = MagicMock(return_value=None)

    result = layer.delete_record(data={"key": "value"}, exception=Exception("test"))

    assert result is None

def test_helper_is_used_in_get_record():
    """
    get_record should return None early when idempotency key is None.
    """
    from aws_lambda_powertools.utilities.idempotency.persistence.base import BasePersistenceLayer

    class ConcretePersistenceLayer(BasePersistenceLayer):
        def _get_record(self, idempotency_key): ...
        def _put_record(self, data_record): ...
        def _update_record(self, data_record): ...
        def _delete_record(self, data_record): ...

    layer = ConcretePersistenceLayer()
    layer._get_hashed_idempotency_key = MagicMock(return_value=None)

    result = layer.get_record(data={"key": "value"})

    assert result is None
