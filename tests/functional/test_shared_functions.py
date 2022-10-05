import warnings

import pytest

from aws_lambda_powertools.shared import constants
from aws_lambda_powertools.shared.functions import (
    powertools_debug_is_set,
    powertools_dev_is_set,
    resolve_env_var_choice,
    resolve_truthy_env_var_choice,
    strtobool,
)


def test_resolve_env_var_choice_explicit_wins_over_env_var():
    assert resolve_truthy_env_var_choice(env="true", choice=False) is False
    assert resolve_env_var_choice(env="something", choice=False) is False


def test_resolve_env_var_choice_env_wins_over_absent_explicit():
    assert resolve_truthy_env_var_choice(env="true") == 1
    assert resolve_env_var_choice(env="something") == "something"


@pytest.mark.parametrize("true_value", ["y", "yes", "t", "true", "on", "1"])
def test_strtobool_true(true_value):
    assert strtobool(true_value)


@pytest.mark.parametrize("false_value", ["n", "no", "f", "false", "off", "0"])
def test_strtobool_false(false_value):
    assert strtobool(false_value) is False


def test_strtobool_value_error():
    with pytest.raises(ValueError) as exp:
        strtobool("fail")
    assert str(exp.value) == "invalid truth value 'fail'"


def test_powertools_dev_warning(monkeypatch: pytest.MonkeyPatch):
    # GIVEN POWERTOOLS_DEBUG is set
    monkeypatch.setenv(constants.POWERTOOLS_DEV_ENV, "1")
    warning_message = "POWERTOOLS_DEV environment variable is enabled. Increasing verbosity across utilities."

    # WHEN set_package_logger is used at initialization
    # THEN a warning should be emitted
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("default")
        powertools_dev_is_set()
        assert len(w) == 1
        assert str(w[0].message) == warning_message


def test_powertools_debug_warning(monkeypatch: pytest.MonkeyPatch):
    # GIVEN POWERTOOLS_DEBUG is set
    monkeypatch.setenv(constants.POWERTOOLS_DEBUG_ENV, "1")
    warning_message = "POWERTOOLS_DEBUG environment variable is enabled. Setting logging level to DEBUG."

    # WHEN set_package_logger is used at initialization
    # THEN a warning should be emitted
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("default")
        powertools_debug_is_set()
        assert len(w) == 1
        assert str(w[0].message) == warning_message
