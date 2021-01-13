import os

from aws_lambda_powertools.shared.functions import resolve_env_var_choice


def test_explicit_wins_over_env_var():
    choice_env = os.getenv("CHOICE", True)

    choice = resolve_env_var_choice(env=choice_env, choice=False)

    assert choice is False
