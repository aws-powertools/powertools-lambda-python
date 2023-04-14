from __future__ import annotations

import base64
import dataclasses
import itertools
import logging
import os
import warnings
from binascii import Error as BinAsciiError
from typing import Any, Dict, Generator, Optional, Union, overload

from aws_lambda_powertools.shared import constants

logger = logging.getLogger(__name__)


def strtobool(value: str) -> bool:
    """Convert a string representation of truth to True or False.

    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'value' is anything else.

    > note:: Copied from distutils.util.
    """
    value = value.lower()
    if value in ("1", "y", "yes", "t", "true", "on"):
        return True
    if value in ("0", "n", "no", "f", "false", "off"):
        return False
    raise ValueError(f"invalid truth value {value!r}")


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


def resolve_max_age(env: str, choice: Optional[int]) -> int:
    """Resolve max age value"""
    return choice if choice is not None else int(env)


@overload
def resolve_env_var_choice(env: Optional[str], choice: float) -> float:
    ...


@overload
def resolve_env_var_choice(env: Optional[str], choice: str) -> str:
    ...


@overload
def resolve_env_var_choice(env: Optional[str], choice: Optional[str]) -> str:
    ...


def resolve_env_var_choice(
    env: Optional[str] = None, choice: Optional[Union[str, float]] = None
) -> Optional[Union[str, float]]:
    """Pick explicit choice over env, if available, otherwise return env value received

    NOTE: Environment variable should be resolved by the caller.

    Parameters
    ----------
    env : str, Optional
        environment variable actual value
    choice : str|float, optional
        explicit choice

    Returns
    -------
    choice : str, Optional
        resolved choice as either bool or environment value
    """
    return choice if choice is not None else env


def base64_decode(value: str) -> bytes:
    try:
        logger.debug("Decoding base64 record item before parsing")
        return base64.b64decode(value)
    except (BinAsciiError, TypeError):
        raise ValueError("base64 decode failed")


def bytes_to_string(value: bytes) -> str:
    try:
        return value.decode("utf-8")
    except (BinAsciiError, TypeError):
        raise ValueError("base64 UTF-8 decode failed")


def powertools_dev_is_set() -> bool:
    is_on = strtobool(os.getenv(constants.POWERTOOLS_DEV_ENV, "0"))
    if is_on:
        warnings.warn(
            "POWERTOOLS_DEV environment variable is enabled. Increasing verbosity across utilities.", stacklevel=2
        )
        return True

    return False


def powertools_debug_is_set() -> bool:
    is_on = strtobool(os.getenv(constants.POWERTOOLS_DEBUG_ENV, "0"))
    if is_on:
        warnings.warn("POWERTOOLS_DEBUG environment variable is enabled. Setting logging level to DEBUG.", stacklevel=2)
        return True

    return False


def slice_dictionary(data: Dict, chunk_size: int) -> Generator[Dict, None, None]:
    for _ in range(0, len(data), chunk_size):
        yield {dict_key: data[dict_key] for dict_key in itertools.islice(data, chunk_size)}


def extract_event_from_common_models(data: Any) -> Dict | Any:
    """Extract raw event from common types used in Powertools

    If event cannot be extracted, return received data as is.

    Common models:

        - Event Source Data Classes (DictWrapper)
        - Python Dataclasses
        - Pydantic Models (BaseModel)

    Parameters
    ----------
    data : Any
        Original event, a potential instance of DictWrapper/BaseModel/Dataclass

    Notes
    -----

    Why not using static type for function argument?

    DictWrapper would cause a circular import. Pydantic BaseModel could
    cause a ModuleNotFound or trigger init reflection worsening cold start.
    """
    # Short-circuit most common type first for perf
    if isinstance(data, dict):
        return data

    # Is it an Event Source Data Class?
    if getattr(data, "raw_event", None):
        return data.raw_event

    # Is it a Pydantic Model?
    if callable(getattr(data, "dict", None)):
        return data.dict()

    # Is it a Dataclass? If not return as is
    return dataclasses.asdict(data) if dataclasses.is_dataclass(data) else data
