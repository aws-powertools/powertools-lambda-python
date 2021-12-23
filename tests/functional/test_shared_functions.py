import pytest

from aws_lambda_powertools.shared.functions import resolve_env_var_choice, resolve_truthy_env_var_choice, strtobool


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
