import os
import warnings
from dataclasses import dataclass

import pytest
from pydantic import BaseModel

from aws_lambda_powertools.shared import constants
from aws_lambda_powertools.shared.functions import (
    extract_event_from_common_models,
    powertools_debug_is_set,
    powertools_dev_is_set,
    resolve_env_var_choice,
    resolve_max_age,
    resolve_truthy_env_var_choice,
    strtobool,
)
from aws_lambda_powertools.utilities.data_classes.common import DictWrapper
from aws_lambda_powertools.utilities.parameters.base import DEFAULT_MAX_AGE_SECS


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


def test_extract_event_dict():
    data = {"hello": "world"}
    assert extract_event_from_common_models(data) == data


def test_extract_event_pydantic():
    class DummyModel(BaseModel):
        hello: str

    data = {"hello": "world"}
    assert extract_event_from_common_models(DummyModel(**data)) == data


def test_extract_event_dict_wrapper():
    class DummyClassSample(DictWrapper):
        pass

    data = {"hello": "world"}
    assert extract_event_from_common_models(DummyClassSample(data)) == data


def test_extract_event_dataclass():
    @dataclass
    class DummyDataclass:
        hello: str

    data = {"hello": "world"}
    assert extract_event_from_common_models(DummyDataclass(**data)) == data


@pytest.mark.parametrize("data", [False, True, "", 10, [], {}, object])
def test_extract_event_any(data):
    assert extract_event_from_common_models(data) == data


def test_resolve_max_age_explicit_wins_over_env_var(monkeypatch: pytest.MonkeyPatch):
    # GIVEN POWERTOOLS_PARAMETERS_MAX_AGE environment variable is set
    monkeypatch.setenv(constants.PARAMETERS_MAX_AGE_ENV, "20")

    # WHEN the choice is set explicitly
    max_age = resolve_max_age(env=os.getenv(constants.PARAMETERS_MAX_AGE_ENV, DEFAULT_MAX_AGE_SECS), choice=10)

    # THEN the result must be the choice
    assert max_age == 10


def test_resolve_max_age_with_default_value():
    # GIVEN POWERTOOLS_PARAMETERS_MAX_AGE is not set

    # WHEN the choice is set to None
    max_age = resolve_max_age(env=os.getenv(constants.PARAMETERS_MAX_AGE_ENV, DEFAULT_MAX_AGE_SECS), choice=None)

    # THEN the result must be the default value (DEFAULT_MAX_AGE_SECS)
    assert max_age == int(DEFAULT_MAX_AGE_SECS)


def test_resolve_max_age_env_var_wins_over_default_value(monkeypatch: pytest.MonkeyPatch):
    # GIVEN POWERTOOLS_PARAMETERS_MAX_AGE environment variable is set
    monkeypatch.setenv(constants.PARAMETERS_MAX_AGE_ENV, "20")

    # WHEN the choice is set to None
    max_age = resolve_max_age(env=os.getenv(constants.PARAMETERS_MAX_AGE_ENV, DEFAULT_MAX_AGE_SECS), choice=None)

    # THEN the result must be the environment variable value
    assert max_age == 20
