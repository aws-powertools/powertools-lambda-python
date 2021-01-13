from distutils.util import strtobool


def resolve_env_var_choice(env: str, choice: bool = None) -> bool:
    return choice if choice is not None else strtobool(env)
