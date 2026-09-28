from __future__ import annotations

import os
import subprocess
import sys
import textwrap
import warnings
from typing import Any

import pytest

from aws_lambda_powertools import PACKAGE_PATH
from aws_lambda_powertools.utilities.feature_flags import FeatureFlags
from aws_lambda_powertools.utilities.feature_flags.base import StoreProvider
from aws_lambda_powertools.utilities.feature_flags.feature_flags import RULE_ACTION_MAPPING
from aws_lambda_powertools.warnings import PowertoolsUserWarning


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
    all_features,
    action,
    context_value,
    condition_value,
    exception_type,
):
    # GIVEN a valid rule whose operands are incompatible at evaluation time
    flags = FeatureFlags(InMemoryStore(action, condition_value))

    # WHEN either public evaluation API evaluates that rule without a custom logger
    with pytest.warns(PowertoolsUserWarning) as records:
        if all_features:
            assert flags.get_enabled_features(context={"customer": context_value}) == []
        else:
            assert flags.evaluate(name="premium", context={"customer": context_value}, default=True) is False

    # THEN identify the failing condition without exposing operand values
    assert len(records) == 1
    message = str(records[0].message)
    for value in ("premium", "eligible_customer", "customer", action, exception_type):
        assert value in message
    assert "sensitive-context" not in message
    assert "sensitive-condition" not in message


@pytest.mark.parametrize(
    "context,expected",
    [({}, False), ({"customer": "ordinary"}, False), ({"customer": "premium-customer"}, True)],
)
def test_missing_context_and_valid_comparisons_do_not_warn(context, expected):
    flags = FeatureFlags(InMemoryStore("STARTSWITH", "premium"))

    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter("always", PowertoolsUserWarning)
        assert flags.evaluate(name="premium", context=context, default=True) is expected

    assert not records


def test_comparator_warning_preserves_exception_handler():
    flags = FeatureFlags(InMemoryStore("STARTSWITH", "premium"))
    handled = []

    @flags.validation_exception_handler(AttributeError)
    def handle_error(exc):
        handled.append(exc)
        return True

    with pytest.warns(PowertoolsUserWarning) as records:
        assert flags.evaluate(name="premium", context={"customer": 123}, default=False) is True

    assert len(handled) == 1
    assert isinstance(handled[0], AttributeError)
    assert len(records) == 1


def test_warning_excludes_exception_message(monkeypatch):
    def fail_with_customer_data(context_value, condition_value):
        raise ValueError(f"Cannot compare {context_value!r} and {condition_value!r}")

    monkeypatch.setitem(RULE_ACTION_MAPPING, "STARTSWITH", fail_with_customer_data)
    flags = FeatureFlags(InMemoryStore("STARTSWITH", "sensitive-condition"))

    with pytest.warns(PowertoolsUserWarning) as records:
        assert flags.evaluate(name="premium", context={"customer": "sensitive-context"}, default=True) is False

    assert len(records) == 1
    message = str(records[0].message)
    assert "ValueError" in message
    assert "sensitive-context" not in message
    assert "sensitive-condition" not in message


@pytest.mark.parametrize("all_features", [False, True])
@pytest.mark.parametrize("register_handler", [False, True])
def test_warnings_as_errors_preserve_evaluation(all_features, register_handler):
    flags = FeatureFlags(InMemoryStore("STARTSWITH", "premium"))
    handled = []

    if register_handler:

        @flags.validation_exception_handler(AttributeError)
        def handle_error(exc):
            handled.append(exc)
            return True

    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter("error", PowertoolsUserWarning)
        if all_features:
            expected = ["premium"] if register_handler else []
            assert flags.get_enabled_features(context={"customer": 123}) == expected
        else:
            assert flags.evaluate(name="premium", context={"customer": 123}, default=True) is register_handler

    assert len(handled) == int(register_handler)
    assert not records


@pytest.mark.parametrize("exception_type", [RuntimeError, PowertoolsUserWarning])
def test_warnings_as_errors_do_not_swallow_handler_exceptions(exception_type):
    flags = FeatureFlags(InMemoryStore("STARTSWITH", "premium"))

    @flags.validation_exception_handler(AttributeError)
    def handle_error(exc):
        raise exception_type("handler failure")

    with warnings.catch_warnings():
        warnings.simplefilter("error", PowertoolsUserWarning)
        with pytest.raises(exception_type, match="handler failure"):
            flags.evaluate(name="premium", context={"customer": 123}, default=False)


@pytest.mark.parametrize("warning_filter", ["default", "error"])
def test_comparator_warning_in_fresh_process(warning_filter):
    # A fresh import retains the package's NullHandler and disabled log propagation.
    script = textwrap.dedent(
        """\
        from aws_lambda_powertools.utilities.feature_flags import FeatureFlags
        from tests.functional.feature_flags.test_comparator_warnings import InMemoryStore

        flags = FeatureFlags(InMemoryStore("STARTSWITH", "sensitive-condition"))
        assert flags.evaluate(name="premium", context={"customer": 123}, default=True) is False
        """,
    )
    environment = os.environ.copy()
    environment.pop("POWERTOOLS_DEBUG", None)
    environment.pop("PYTHONWARNINGS", None)

    result = subprocess.run(
        [sys.executable, "-W", warning_filter, "-c", script],
        cwd=PACKAGE_PATH.parent,
        env=environment,
        capture_output=True,
        text=True,
        check=True,
    )

    message = "PowertoolsUserWarning: Failed to evaluate feature flag condition"
    assert (message in result.stderr) is (warning_filter == "default")
    assert "sensitive-condition" not in result.stderr
