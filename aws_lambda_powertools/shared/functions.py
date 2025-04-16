from __future__ import annotations

import base64
import itertools
import logging
import os
import re
import warnings
from binascii import Error as BinAsciiError
from pathlib import Path
from typing import TYPE_CHECKING, Any, overload

from aws_lambda_powertools.shared import constants

if TYPE_CHECKING:
    from collections.abc import Generator

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


def resolve_truthy_env_var_choice(env: str, choice: bool | None = None) -> bool:
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


def resolve_max_age(env: str, choice: int | None) -> int:
    """Resolve max age value"""
    return choice if choice is not None else int(env)


@overload
def resolve_env_var_choice(env: str | None, choice: float) -> float: ...


@overload
def resolve_env_var_choice(env: str | None, choice: str) -> str: ...


@overload
def resolve_env_var_choice(env: str | None, choice: str | None) -> str: ...


def resolve_env_var_choice(
    env: str | None = None,
    choice: str | float | None = None,
) -> str | float | None:
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
        logger.debug("Decoding base64 item to bytes")
        return base64.b64decode(value)
    except (BinAsciiError, TypeError):
        raise ValueError("base64 decode failed - is this base64 encoded string?")


def bytes_to_base64_string(value: bytes) -> str:
    try:
        logger.debug("Encoding bytes to base64 string")
        return base64.b64encode(value).decode()
    except TypeError:
        raise ValueError(f"base64 encoding failed - is this bytes data? type: {type(value)}")


def bytes_to_string(value: bytes) -> str:
    try:
        return value.decode("utf-8")
    except (BinAsciiError, TypeError):
        raise ValueError("base64 UTF-8 decode failed")


def powertools_dev_is_set() -> bool:
    is_on = strtobool(os.getenv(constants.POWERTOOLS_DEV_ENV, "0"))
    if is_on:
        warnings.warn(
            "POWERTOOLS_DEV environment variable is enabled. Increasing verbosity across utilities.",
            stacklevel=2,
        )
        return True

    return False


def powertools_debug_is_set() -> bool:
    is_on = strtobool(os.getenv(constants.POWERTOOLS_DEBUG_ENV, "0"))
    if is_on:
        warnings.warn("POWERTOOLS_DEBUG environment variable is enabled. Setting logging level to DEBUG.", stacklevel=2)
        return True

    return False


def slice_dictionary(data: dict, chunk_size: int) -> Generator[dict, None, None]:
    for _ in range(0, len(data), chunk_size):
        yield {dict_key: data[dict_key] for dict_key in itertools.islice(data, chunk_size)}


def extract_event_from_common_models(data: Any) -> dict | Any:
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
    if is_pydantic(data):
        return pydantic_to_dict(data)

    # Is it a Dataclass?
    if is_dataclass(data):
        return dataclass_to_dict(data)

    # Return as is
    return data


def is_pydantic(data) -> bool:
    """Whether data is a Pydantic model by checking common field available in v1/v2

    Parameters
    ----------
    data: BaseModel
        Pydantic model

    Returns
    -------
    bool
        Whether it's a Pydantic model
    """
    return getattr(data, "json", False)


def is_dataclass(data) -> bool:
    """Whether data is a dataclass

    Parameters
    ----------
    data: dataclass
        Dataclass obj

    Returns
    -------
    bool
        Whether it's a Dataclass
    """
    return getattr(data, "__dataclass_fields__", False)


def pydantic_to_dict(data) -> dict:
    """Dump Pydantic model v1 and v2 as dict.

    Note we use lazy import since Pydantic is an optional dependency.

    Parameters
    ----------
    data: BaseModel
        Pydantic model

    Returns
    -------

    dict:
        Pydantic model serialized to dict
    """
    from aws_lambda_powertools.event_handler.openapi.compat import _model_dump

    return _model_dump(data)


def dataclass_to_dict(data) -> dict:
    """Dump standard dataclass as dict.

    Note we use lazy import to prevent bloating other code parts.

    Parameters
    ----------
    data: dataclass
        Dataclass

    Returns
    -------

    dict:
        Pydantic model serialized to dict
    """
    import dataclasses

    return dataclasses.asdict(data)


def abs_lambda_path(relative_path: str = "") -> str:
    """Return the absolute path from the given relative path to lambda handler.

    Parameters
    ----------
    relative_path : str, optional
        The relative path to the lambda handler, by default an empty string.

    Returns
    -------
    str
        The absolute path generated from the given relative path.
        If the environment variable LAMBDA_TASK_ROOT is set, it will use that value.
        Otherwise, it will use the current working directory.
        If the path is empty, it will return the current working directory.
    """
    # Retrieve the LAMBDA_TASK_ROOT environment variable or default to an empty string
    current_working_directory = os.environ.get("LAMBDA_TASK_ROOT", "") or str(Path.cwd())

    return str(Path(current_working_directory, relative_path))


def sanitize_xray_segment_name(name: str) -> str:
    return re.sub(constants.INVALID_XRAY_NAME_CHARACTERS, "", name)


def get_tracer_id() -> str | None:
    xray_trace_id = os.getenv(constants.XRAY_TRACE_ID_ENV)
    return xray_trace_id.split(";")[0].replace("Root=", "") if xray_trace_id else None
