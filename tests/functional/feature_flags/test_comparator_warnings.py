from __future__ import annotations

import logging
from typing import Any

import pytest

from aws_lambda_powertools.utilities.feature_flags import FeatureFlags
from aws_lambda_powertools.utilities.feature_flags.base import StoreProvider
from aws_lambda_powertools.utilities.feature_flags.feature_flags import RULE_ACTION_MAPPING


class InMemoryStore(StoreProvider):
    def __init__(self, action: str, value: Any):
        self.configuration = {
            "premium": {
                "default": False,
                "rules": {
                    "eligible_customer": {
                        "when_match": True,
                        "conditions": [{"key": "customer", "action": action, "value": value}],
                    },
                },
            },
        }

    @property
    def get_raw_configuration(self) -> dict[str, Any]:
        return self.configuration

    def get_configuration(self) -> dict[str, Any]:
        return self.configuration


@pytest.mark.parametrize("all_features", [False, True])
@pytest.mark.parametrize(
    "action,context_value,condition_value,exception_type",
    [
        ("STARTSWITH", 123, "sensitive-condition", "AttributeError"),
        ("KEY_GREATER_THAN_VALUE", "sensitive-context", 123, "TypeError"),
        ("ANY_IN_VALUE", "sensitive-context", ["sensitive-condition"], "ValueError"),
    ],
)
def test_comparator_failure_warns_without_changing_result(
    caplog,
    all_features,
    action,
    context_value,
    condition_value,
    exception_type,
):
    # GIVEN a valid rule whose operands are incompatible at evaluation time
    flags = FeatureFlags(InMemoryStore(action, condition_value))

    # WHEN either public evaluation API evaluates that rule at the default log level
    with caplog.at_level(logging.WARNING):
        if all_features:
            assert flags.get_enabled_features(context={"customer": context_value}) == []
        else:
            assert flags.evaluate(name="premium", context={"customer": context_value}, default=True) is False

    # THEN identify the failing condition without exposing operand values
    assert len(caplog.records) == 1
    message = caplog.records[0].getMessage()
    for value in ("premium", "eligible_customer", "customer", action, exception_type):
        assert value in message
    assert "sensitive-context" not in message
    assert "sensitive-condition" not in message
    assert caplog.records[0].levelno == logging.WARNING


@pytest.mark.parametrize("context", [{}, {"customer": "ordinary"}])
def test_missing_context_and_valid_nonmatch_do_not_warn(caplog, context):
    flags = FeatureFlags(InMemoryStore("STARTSWITH", "premium"))

    with caplog.at_level(logging.WARNING):
        assert flags.evaluate(name="premium", context=context, default=True) is False

    assert not caplog.records


def test_comparator_warning_preserves_exception_handler(caplog):
    flags = FeatureFlags(InMemoryStore("STARTSWITH", "premium"))
    handled = []

    @flags.validation_exception_handler(AttributeError)
    def handle_error(exc):
        handled.append(exc)
        return True

    with caplog.at_level(logging.WARNING):
        assert flags.evaluate(name="premium", context={"customer": 123}, default=False) is True

    assert len(handled) == 1
    assert isinstance(handled[0], AttributeError)
    assert len(caplog.records) == 1


def test_warning_excludes_exception_message(caplog, monkeypatch):
    def fail_with_customer_data(context_value, condition_value):
        raise ValueError(f"Cannot compare {context_value!r} and {condition_value!r}")

    monkeypatch.setitem(RULE_ACTION_MAPPING, "STARTSWITH", fail_with_customer_data)
    flags = FeatureFlags(InMemoryStore("STARTSWITH", "sensitive-condition"))

    with caplog.at_level(logging.WARNING):
        assert flags.evaluate(name="premium", context={"customer": "sensitive-context"}, default=True) is False

    assert len(caplog.records) == 1
    assert "ValueError" in caplog.text
    assert "sensitive-context" not in caplog.text
    assert "sensitive-condition" not in caplog.text
