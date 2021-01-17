from aws_lambda_powertools.shared.functions import resolve_env_var_choice, resolve_truthy_env_var_choice


def test_resolve_env_var_choice_explicit_wins_over_env_var():
    assert resolve_truthy_env_var_choice(env="true", choice=False) is False
    assert resolve_env_var_choice(env="something", choice=False) is False


def test_resolve_env_var_choice_env_wins_over_absent_explicit():
    assert resolve_truthy_env_var_choice(env="true") == 1
    assert resolve_env_var_choice(env="something") == "something"
