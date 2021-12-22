from typing import Any, Optional, Union


def strtobool(value):
    value = value.lower()
    if value in ("y", "yes", "t", "true", "on", "1"):
        return 1
    elif value in ("n", "no", "f", "false", "off", "0"):
        return 0
    else:
        raise ValueError("invalid truth value %r" % (value,))


def resolve_truthy_env_var_choice(env: str, choice: Optional[bool] = None) -> bool:
    """Pick explicit choice over truthy env value, if available, otherwise return truthy env value

    NOTE: Environment variable should be resolved by the caller.

    Parameters
    ----------
    env : str
        environment variable actual value
    choice : bool
        explicit choice

    Returns
    -------
    choice : str
        resolved choice as either bool or environment value
    """
    return choice if choice is not None else strtobool(env)


def resolve_env_var_choice(env: Any, choice: Optional[Any] = None) -> Union[bool, Any]:
    """Pick explicit choice over env, if available, otherwise return env value received

    NOTE: Environment variable should be resolved by the caller.

    Parameters
    ----------
    env : Any
        environment variable actual value
    choice : bool
        explicit choice

    Returns
    -------
    choice : str
        resolved choice as either bool or environment value
    """
    return choice if choice is not None else env
